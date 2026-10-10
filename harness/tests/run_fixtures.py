#!/usr/bin/env python3
"""judge.py 검증: harness/tests/fixtures/ 샘플의 기대 위반 수·규칙이 실제와 모두 일치해야 통과 (harness/review.md).

사용법: python3 harness/tests/run_fixtures.py
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIX = os.path.join(HERE, 'fixtures')
sys.path.insert(0, os.path.join(ROOT, 'harness', 'scripts'))
import judge  # noqa: E402


def run(name, spec, R):
    path = os.path.join(FIX, name.split(':', 1)[-1])
    if spec.get('exceptions'):           # 본인이 rules.json 에 예외 구절을 추가한 상황을 흉내
        R = dict(R, **{'keyword-exceptions': R['keyword-exceptions'] + spec['exceptions']})
    if spec['check'] == 'render':
        return judge.check_render(path, R, require_tokens=True)
    if spec['check'] == 'html':
        return judge.check_html(path, R, require_tokens=True)
    if spec['check'] == 'component':
        return judge.check_components(os.path.join(path, '04-components-before.css'), os.path.join(path, 'glowlog.css'))
    if spec['check'] == 'guard':         # 훅에 들어오는 stdin 그대로 guard.py 를 실행
        project = os.path.join(FIX, spec['project'])
        data = dict(spec['input'], cwd=project)
        if data['tool_input'].get('file_path', '').startswith(('screens/', 'runs/', 'harness/', 'PRD', 'design', '.claude')):
            data['tool_input'] = dict(data['tool_input'], file_path=os.path.join(project, data['tool_input']['file_path']))
        res = subprocess.run([sys.executable, os.path.join(ROOT, 'harness', 'scripts', 'guard.py')], input=json.dumps(data),
                             capture_output=True, text=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=project))
        denied = '"deny"' in res.stdout
        return [{'rule': 'guard-deny', 'where': name, 'detail': res.stdout.strip()}] if denied else []
    if spec['check'] == 'history':
        return judge.check_history(path, os.path.join(path, 'runs', '20261010-screen2'), R['H'])
    if spec['check'] == 'scope':
        return judge.check_scope(path, os.path.join(path, 'runs', '20261010-screen2'), R)
    raise ValueError(spec['check'])


def main():
    R = judge.load_rules(ROOT)
    expected = {k: v for k, v in json.load(open(os.path.join(FIX, 'expected.json'), encoding='utf-8')).items() if not k.startswith('_')}
    failed = 0
    for name, spec in expected.items():
        out = run(name, spec, R)
        rules = sorted({v['rule'] for v in out})
        ok = len(out) == spec['count'] and rules == ([spec['rule']] if 'rule' in spec else [])
        failed += not ok
        print(f'{"OK  " if ok else "FAIL"} {name:24} 기대 {spec["count"]} / 실제 {len(out)} {rules}')
        if not ok:
            for v in out:
                print(f'       [{v["rule"]}] {v["where"]} — {v["detail"]}')
    print(f'\n{len(expected) - failed}/{len(expected)} 일치')

    # 🚦 커버리지: design.md 에 🚦로 표시한 규칙마다 그 규칙으로 실패하는 샘플이 1개 이상 있어야 한다
    design = open(os.path.join(ROOT, 'design.md'), encoding='utf-8').read()
    marked = sorted({rule for line in design.splitlines() if '🚦' in line
                     for rule in re.findall(r'`([a-z][a-z-]*)`', re.split(r'—|/|👀', line.split('🚦', 1)[1])[0])})
    covered = {spec.get('rule') for spec in expected.values()}
    missing = [r for r in marked if r not in covered]
    eyes = sum(line.count('👀') for line in design.splitlines() if not line.startswith('> 👀 ='))
    print(f'🚦 규칙 {len(marked)}개 중 실패 샘플 있음 {len(marked) - len(missing)}개' + (f' — 없음: {", ".join(missing)}' if missing else ''))
    print(f'👀 사람 확인 규칙 {eyes}개 (S3 시안 선택 때 확인)')
    sys.exit(1 if failed or missing else 0)


if __name__ == '__main__':
    main()
