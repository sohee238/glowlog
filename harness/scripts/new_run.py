#!/usr/bin/env python3
"""새 실행 폴더를 만든다 (오케스트레이터 전용). 같은 이름이 있으면 재사용하지 않고 -2, -3 … 을 붙인다.

사용법: python3 harness/scripts/new_run.py --screen 2 --keywords "달력,루틴 카드"
출력: 만든 폴더 경로 (runs/20261010-screen2 등)
"""
import argparse
import json
import os
from datetime import date

from judge import ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--screen', type=int, required=True, choices=[1, 2, 3])
    ap.add_argument('--keywords', required=True, help='쉼표 구분 1~3개')
    args = ap.parse_args()
    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    if not 1 <= len(keywords) <= 3:
        raise SystemExit('키워드는 1~3개')
    base = os.path.join('runs', f'{date.today():%Y%m%d}-screen{args.screen}')
    run, k = base, 2
    while os.path.exists(os.path.join(ROOT, run)):
        run, k = f'{base}-{k}', k + 1
    os.makedirs(os.path.join(ROOT, run))
    state = json.load(open(os.path.join(ROOT, 'harness', 'templates', 'state.json'), encoding='utf-8'))
    state.update(screen=args.screen, keywords=keywords)
    with open(os.path.join(ROOT, run, 'state.json'), 'w', encoding='utf-8') as fp:
        json.dump(state, fp, ensure_ascii=False, indent=2)
    print(run)


if __name__ == '__main__':
    main()
