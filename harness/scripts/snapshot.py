#!/usr/bin/env python3
"""단계 시작 시 프로젝트 파일 목록·수정 시각을 state.json snapshots.{단계}에 기록한다 (오케스트레이터 전용).

사용법: python3 harness/scripts/snapshot.py S1 --run runs/<YYYYMMDD>-screen<N>
"""
import argparse
import json
import os

from judge import ROOT, STAGES, list_files, load_rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=STAGES)
    ap.add_argument('--run', required=True)
    args = ap.parse_args()
    path = os.path.join(args.run, 'state.json')
    state = json.load(open(path, encoding='utf-8'))
    state.setdefault('snapshots', {})[args.stage] = list_files(ROOT, load_rules(ROOT)['H'])
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(state, fp, ensure_ascii=False, indent=2)
    print(f'{args.stage} 스냅샷 기록: 파일 {len(state["snapshots"][args.stage])}개')


if __name__ == '__main__':
    main()
