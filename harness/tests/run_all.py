#!/usr/bin/env python3
"""규칙을 고친 뒤 한 번에 돌리는 회귀 검사. 하나라도 깨지면 종료 코드 1.

1. 판정 함수 샘플 + 🚦 커버리지 + guard 케이스      (run_fixtures.py)
2. 게이트 예시 12개 — 실제 명령으로 판정             (run_gates.py)
3. 재판정 자기 검증 — 옛 규칙 시절 이력(pass-history)에서 알려진 깨짐을 정확히 찾는가
4. 실제 실행 기록 재판정 — runs/* 중 예전 PASS 가 지금 규칙으로 FAIL 이 되는가   (rejudge.py)

사용법: python3 harness/tests/run_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import rejudge  # noqa: E402

# pass-history 는 렌더·글자 스타일·컴포넌트 규칙 도입 전에 실제 명령으로 통과시킨 이력이다.
# 지금 규칙으로 재판정하면 이 게이트들이 PASS→FAIL 이어야 한다 (규칙을 더 바꾸면 이 기대값도 갱신).
KNOWN_BREAKS = ['G3', 'S5']


def step(name, args):
    r = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True)
    last = [l for l in r.stdout.strip().splitlines() if l.strip()]
    tail = ' / '.join(l for l in last[-3:] if '일치' in l or '🚦' in l or '재판정' in l) or (last[-1] if last else r.stderr.strip()[-200:])
    print(f'{"OK  " if r.returncode == 0 else "FAIL"} {name:24} {tail}')
    if r.returncode:
        print('\n'.join('     ' + l for l in last if l.startswith('FAIL') or '깨짐' in l or '없음:' in l))
    return r.returncode == 0


def main():
    results = [
        step('1. 판정 함수 샘플', ['harness/tests/run_fixtures.py']),
        step('2. 게이트 예시', ['harness/tests/run_gates.py']),
    ]
    rows = rejudge.rejudge(os.path.join(HERE, 'fixtures', 'pass-history'), rejudge.judge.load_rules(ROOT))
    found = sorted(g for _, g, before, now, _ in rows if (before, now) == ('PASS', 'FAIL'))
    ok = found == sorted(KNOWN_BREAKS)
    print(f'{"OK  " if ok else "FAIL"} {"3. 재판정 자기 검증":24} 알려진 깨짐 {KNOWN_BREAKS} / 찾은 깨짐 {found}')
    results.append(ok)
    results.append(step('4. 실행 기록 재판정', ['harness/tests/rejudge.py']))
    print(f'\n회귀 검사 {sum(results)}/{len(results)} 통과' + ('' if all(results) else ' — 깨진 항목을 고치기 전에는 하네스를 쓰지 않는다'))
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
