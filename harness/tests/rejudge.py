#!/usr/bin/env python3
"""실행 기록 재판정: runs/* 의 게이트를 **지금 규칙**으로 다시 판정해 예전 판정과 비교한다 (리포트·이력에 쓰지 않음).

- 판정 당시 입력 파일 지문(05-report.json inputs)과 지금 파일이 다르면 규칙 변화가 아니라 파일 변화이므로 생략한다.
- S5 의 편집 범위(scope) 판정은 시간이 지나면 다른 실행 때문에 바뀌므로 비교에서 뺀다.
- 예전 PASS → 지금 FAIL 이 하나라도 있으면 종료 코드 1.

사용법: python3 harness/tests/rejudge.py [--root 프로젝트 폴더]
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'harness', 'scripts'))
import judge  # noqa: E402

TIME_DEPENDENT = {'scope'}


def rejudge(root, R):
    """[(실행, 게이트, 예전, 지금, 바뀐 규칙들)] — 규칙은 항상 지금 프로젝트(ROOT)의 것을 쓴다."""
    H = R['H']
    rows = []
    for report in sorted(glob.glob(os.path.join(root, 'runs', '*', H['report']))):
        run_dir = os.path.dirname(report)
        data = json.load(open(report, encoding='utf-8'))
        for gate in H['gate_order']:
            rec = data.get(gate)
            if not rec:
                continue
            before = 'PASS' if rec['pass'] else 'FAIL'
            if rec.get('inputs') != judge.input_hashes(gate, run_dir, root, H):
                rows.append((os.path.relpath(run_dir, root), gate, before, '생략(입력 변경)', []))
                continue
            out, _ = judge.run_gate(gate, run_dir, root, R)
            out = [v for v in out if v['rule'] not in TIME_DEPENDENT]
            rows.append((os.path.relpath(run_dir, root), gate, before, 'FAIL' if out else 'PASS', sorted({v['rule'] for v in out})))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=ROOT)
    args = ap.parse_args()
    rows = rejudge(os.path.abspath(args.root), judge.load_rules(ROOT))
    breaks = [r for r in rows if r[2] == 'PASS' and r[3] == 'FAIL']
    for run, gate, before, now, rules in rows:
        mark = '깨짐' if (before, now) == ('PASS', 'FAIL') else ('변화' if before != now and not now.startswith('생략') else '    ')
        print(f'{mark} {run} {gate:6} {before} → {now} {rules if rules else ""}')
    print(f'\n실행 기록 재판정: {len(rows)}건 중 PASS→FAIL {len(breaks)}건' + ('' if rows else ' (runs/ 에 기록 없음)'))
    sys.exit(1 if breaks else 0)


if __name__ == '__main__':
    main()
