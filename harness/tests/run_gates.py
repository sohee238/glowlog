#!/usr/bin/env python3
"""게이트 예시 12개를 실제 명령(judge.py {게이트} --run …)으로 판정해 결과 코드·위반 규칙·리포트 기록을 확인한다.

예시마다 임시 폴더에 지금의 design.md·PRD.md·harness/rules.json·harness/scripts 와 예시 파일을 복사해서 돌린다
(실제 프로젝트 폴더에는 아무것도 쓰지 않는다). 사용법: python3 harness/tests/run_gates.py
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def sh(args, cwd):
    return subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True)


def run_case(case_dir):
    spec = json.load(open(os.path.join(case_dir, 'case.json'), encoding='utf-8'))
    run = spec['run']
    with tempfile.TemporaryDirectory() as t:
        for f in ('design.md', 'PRD.md'):
            shutil.copy(os.path.join(ROOT, f), t)
        shutil.copytree(os.path.join(ROOT, 'harness', 'scripts'), os.path.join(t, 'harness', 'scripts'),
                        ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copy(os.path.join(ROOT, 'harness', 'rules.json'), os.path.join(t, 'harness'))
        shutil.copytree(os.path.join(case_dir, 'tree'), t, dirs_exist_ok=True)
        for step in spec['setup']:
            if step[0] == 'gate':
                r = sh(['harness/scripts/judge.py', step[1], '--run', run], t)
            elif step[0] == 'choose':
                r = sh(['harness/scripts/choose.py', step[1], '--run', run, '--reason', '테스트'], t)
            elif step[0] == 'snapshot':
                r = sh(['harness/scripts/snapshot.py', step[1], '--run', run], t)
            elif step[0] == 'append':
                open(os.path.join(t, step[1]), 'a', encoding='utf-8').write(step[2])
                continue
            if r.returncode != 0:
                return False, f'사전 단계 {step} 실패: {r.stdout.strip()} {r.stderr.strip()[-200:]}'
        r = sh(['harness/scripts/judge.py', spec['gate'], '--run', run], t)
        report_path = os.path.join(t, run, '05-report.json')
        rec = json.load(open(report_path, encoding='utf-8')).get(spec['gate']) if os.path.exists(report_path) else None
        rules = sorted({v['rule'] for v in rec['violations']}) if rec else None
        ok = (r.returncode == spec['expect_exit'] and rec is not None
              and rec['pass'] == (spec['expect_exit'] == 0) and rules == sorted(spec['expect_rules']))
        return ok, f'결과 코드 {r.returncode} (기대 {spec["expect_exit"]}), 위반 {rules} (기대 {spec["expect_rules"]}) — {spec["설명"]}'


def main():
    cases = sorted(glob.glob(os.path.join(HERE, 'gates', '*', '*')))
    failed = 0
    for c in cases:
        ok, msg = run_case(c)
        failed += not ok
        print(f'{"OK  " if ok else "FAIL"} {os.path.relpath(c, os.path.join(HERE, "gates")):12} {msg}')
    print(f'\n게이트 예시 {len(cases) - failed}/{len(cases)} 일치')
    sys.exit(1 if failed or not cases else 0)


if __name__ == '__main__':
    main()
