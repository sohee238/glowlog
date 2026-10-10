#!/usr/bin/env python3
"""사람 승인 기록: 사용자가 "a로 할게"/"b로 할게"라고 말했을 때만 오케스트레이터가 실행한다.

03-choice.md 에 선택값·이유·승인 시점 시안 해시를 쓴다. 이후 시안이 바뀌면 CHOICE·S5 게이트에서 choice-stale.
사용법: python3 harness/scripts/choose.py {a|b} --run runs/<id> --reason "이유 한 줄"
"""
import argparse
import os
import sys

from judge import ROOT, draft_hashes, load_rules


def main():
    H = load_rules(ROOT)['H']
    c = H['choice']
    ap = argparse.ArgumentParser()
    ap.add_argument('choice', choices=c['allowed'])
    ap.add_argument('--run', required=True)
    ap.add_argument('--reason', required=True)
    args = ap.parse_args()
    hashes = draft_hashes(args.run, H)
    if 'missing' in hashes:
        print(f'시안 파일 없음: {H["G3"]["drafts"]}', file=sys.stderr)
        sys.exit(2)
    with open(os.path.join(args.run, c['file']), 'w', encoding='utf-8') as fp:
        fp.write(f'{args.choice}\n{c["reason_field"]} {args.reason}\n{c["hash_field"]} {" / ".join(hashes)}\n')
    print(f'{c["file"]} 기록: {args.choice} ({" / ".join(hashes)})')


if __name__ == '__main__':
    main()
