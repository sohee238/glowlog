#!/usr/bin/env python3
"""PreToolUse 훅 가드: 하네스 실행 중 편집 범위·고정 문서·판정자 명령을 **사전에** 막는다.

등록: .claude/settings.json (저장소에 커밋 — 동료 환경에도 같은 강제)
입력: 훅 stdin JSON (tool_name, tool_input, agent_type — 서브에이전트 호출일 때만 agent_type 존재)
출력: 막을 때 hookSpecificOutput.permissionDecision = "deny" + 이유. 통과면 출력 없음(exit 0).

규칙 원본: harness/rules.json (scope, always_allowed, guard) / 설명: harness/roles.md
- 실행 중이 아닐 때(runs/*/state.json 중 stage != DONE 이 없음): 하네스 에이전트의 쓰기·Bash만 막고 나머지는 통과
- 이 스크립트 안에서 예외가 나면 판단할 수 없으므로 막는다 (fail-closed)
"""
import fnmatch
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(os.path.dirname(HERE), 'rules.json')
WRITE_TOOLS = {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': f'[harness guard] {reason}',
    }}, ensure_ascii=False))
    sys.exit(0)


def matches(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)


def active_runs(root):
    runs = []
    for p in glob.glob(os.path.join(root, 'runs', '*', 'state.json')):
        try:
            if json.load(open(p, encoding='utf-8')).get('stage') != 'DONE':
                runs.append(os.path.relpath(os.path.dirname(p), root))
        except (OSError, ValueError):
            runs.append(os.path.relpath(os.path.dirname(p), root))   # 읽을 수 없는 state 도 실행 중으로 본다
    return runs


def check_write(path, agent, H, active):
    g = H['guard']
    if path is None:
        if agent:
            deny(f'{agent}: 프로젝트 밖 경로에는 쓸 수 없음')
        return
    if agent == 'judge':
        deny('judge 는 읽기 전용 (파일 쓰기 금지)')
    if agent in H['scope']:
        if not matches(path, H['scope'][agent]):
            deny(f'{agent} 편집 범위 밖: {path} (허용: {", ".join(H["scope"][agent])})')
        return
    if not active:
        return                                   # 실행 중이 아님 — 본인·메인 세션의 하네스 정비는 자유
    if matches(path, g['protected']):
        deny(f'실행 중에는 고정 문서를 수정할 수 없음: {path}')
    if matches(path, g['choose_only']):
        deny(f'{path} 는 harness/scripts/choose.py 로만 기록 (본인이 시안을 골랐을 때)')
    if not matches(path, g['orchestrator_write']):
        deny(f'오케스트레이터는 산출물을 직접 작성하지 않음: {path} (허용: {", ".join(g["orchestrator_write"])})')


def glob_re(pattern):
    return re.escape(pattern).replace(r'\*', r'[^\s\'"]*')


def check_bash(cmd, agent, H, active):
    g = H['guard']
    cmd = cmd.strip()
    if agent == 'judge':
        if not re.fullmatch(g['judge_command'], cmd):
            deny(f'judge 는 이 형식의 명령만 실행 가능: {g["judge_command"]}')
        return
    if agent in H['scope']:
        deny(f'{agent} 는 Bash 를 쓰지 않음')
    if not active:
        return
    if re.search(r'judge\.py\b.*--root', cmd):
        deny('judge.py 에 --root 를 쓸 수 없음')
    if re.fullmatch(g['trusted_command'], cmd):
        return                                   # 하네스 스크립트 단독 실행 (choose.py 포함) — 스크립트가 규칙대로 씀
    if re.search(g['bash_write_pattern'], cmd):
        for p in g['protected'] + g['choose_only']:
            if re.search(glob_re(p), cmd):
                deny(f'실행 중 Bash 로 고정 문서·선택 기록을 건드리는 쓰기 명령은 금지 (일치: {p}). 실행 폴더 생성은 new_run.py, 선택 기록은 choose.py 사용')


def main():
    data = json.load(sys.stdin)
    root = os.environ.get('CLAUDE_PROJECT_DIR') or data.get('cwd') or os.getcwd()
    H = json.load(open(RULES, encoding='utf-8'))
    agent = data.get('agent_type')
    agent = agent if agent in ('researcher', 'designer', 'judge') else None
    tool, inp = data.get('tool_name', ''), data.get('tool_input', {}) or {}
    active = bool(active_runs(root))
    if tool in WRITE_TOOLS:
        target = inp.get('file_path') or inp.get('notebook_path') or ''
        full = os.path.normpath(os.path.join(root, target))
        path = os.path.relpath(full, root)
        check_write(None if path.startswith('..') else path, agent, H, active)
    elif tool == 'Bash':
        check_bash(inp.get('command', ''), agent, H, active)
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:                       # 판단 불가 → 막는다 (fail-closed)
        deny(f'가드 오류로 판단할 수 없어 차단: {type(e).__name__}: {e}')
