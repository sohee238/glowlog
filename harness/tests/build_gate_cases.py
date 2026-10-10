#!/usr/bin/env python3
"""게이트 예시 12개(게이트 6개 × 통과·실패)를 harness/tests/gates/ 에 만든다.

각 예시 = tree/ (실행 폴더를 포함한 미니 프로젝트) + case.json (게이트, 사전 단계, 기대 결과 코드·위반 규칙).
pass.html 이나 템플릿을 고친 뒤 실행: python3 harness/tests/build_gate_cases.py
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
GATES = os.path.join(HERE, 'gates')
RUN = 'runs/20261010-screen2'
PASS_HTML = open(os.path.join(HERE, 'fixtures', 'pass.html'), encoding='utf-8').read()

STATE = json.dumps({'stage': 'S1', 'screen': 2, 'keywords': ['달력', '루틴 카드'],
                    'retries': {'G1': 0, 'G2': 0, 'G3': 0, 'reject': 0, 'G4_S5': 0}, 'snapshots': {}},
                   ensure_ascii=False, indent=2)
REFS = """# S1 레퍼런스 분석 — 화면 2

## A앱 — 달력 화면
- ui_url: https://uibowl.io/ui/1
- 관찰: 월 달력 아래 기록 요약
- 반영 포인트: 기록일 점 표시
- 제외: 공유 버튼은 가져오지 않음

## B앱 — 루틴 카드
- ui_url: https://uibowl.io/ui/2
- 반영 포인트: 다음 예정일 강조

## C앱 — 기록 요약
- ui_url: https://uibowl.io/ui/3
- 반영 포인트: 날짜 탭 시 요약 시트
"""
SPEC = """# S2 화면 설계 — 화면 2

## 기능 요구사항 체크리스트
- [ ] 진행 중인 루틴 카드 목록 → 카드 리스트
- [ ] 월 달력 뷰 기록 표시 → 날짜 아래 점
- [ ] 날짜 탭 시 기록 요약 → 하단 요약 카드
- [ ] 루틴별 사용 주기 설정 → 카드 배지
- [ ] 다음 사용 예정일 표시 → 카드 캡션
"""
DRAFT_B = PASS_HTML.replace('</html>', '</html>\n<!-- 시안 b -->')
BEFORE_CSS = '.card {\n  border-radius: 20px;\n}\n'
AFTER_CSS = BEFORE_CSS + '.chip {\n  border-radius: 6px;\n}\n'
FULL = {
    f'{RUN}/state.json': STATE, f'{RUN}/01-refs.md': REFS, f'{RUN}/02-spec.md': SPEC,
    f'{RUN}/03-draft-a.html': PASS_HTML, f'{RUN}/03-draft-b.html': DRAFT_B,
    f'{RUN}/04-components-before.css': BEFORE_CSS, 'components/glowlog.css': AFTER_CSS,
    'screens/screen-2.html': PASS_HTML,
}
CHAIN = [['gate', 'G1'], ['gate', 'G2'], ['gate', 'G3'], ['choose', 'a'], ['gate', 'CHOICE'], ['gate', 'G4'], ['snapshot', 'S5']]


def one(text, a, b):
    assert text.count(a) == 1, a
    return text.replace(a, b)


# (게이트, 통과/실패, 파일, 사전 단계, 기대 결과 코드, 기대 위반 규칙, 설명)
CASES = [
    ('G1', 'pass', {f'{RUN}/state.json': STATE, f'{RUN}/01-refs.md': REFS}, [], 0, [], '레퍼런스 3개, 금지 기능은 제외: 줄에만'),
    ('G1', 'fail', {f'{RUN}/state.json': STATE, f'{RUN}/01-refs.md': one(REFS, '반영 포인트: 기록일 점 표시', '반영 포인트: 공유 버튼 배치')},
     [], 1, ['keyword'], '★ 반영 포인트에 "공유"'),
    ('G2', 'pass', {f'{RUN}/state.json': STATE, f'{RUN}/02-spec.md': SPEC}, [], 0, [], '체크리스트 5개 = PRD 화면 2 요구사항 5개'),
    ('G2', 'fail', {f'{RUN}/state.json': STATE, f'{RUN}/02-spec.md': one(SPEC, '- [ ] 다음 사용 예정일 표시 → 카드 캡션\n', '')},
     [], 1, ['spec-count'], '체크리스트 4개 (PRD는 5개)'),
    ('G3', 'pass', {f'{RUN}/state.json': STATE, f'{RUN}/03-draft-a.html': PASS_HTML, f'{RUN}/03-draft-b.html': DRAFT_B},
     [], 0, [], '시안 a·b 모두 규칙 준수'),
    ('G3', 'fail', {f'{RUN}/state.json': STATE, f'{RUN}/03-draft-a.html': PASS_HTML,
                    f'{RUN}/03-draft-b.html': one(DRAFT_B, '>오늘 사용<', '>AI 피부 분석<')},
     [], 1, ['keyword'], '★ 시안 b에 "AI 피부 분석" 버튼'),
    ('CHOICE', 'pass', {f'{RUN}/state.json': STATE, f'{RUN}/03-draft-a.html': PASS_HTML, f'{RUN}/03-draft-b.html': DRAFT_B},
     [['choose', 'a']], 0, [], 'choose.py로 a 선택'),
    ('CHOICE', 'fail', {f'{RUN}/state.json': STATE, f'{RUN}/03-draft-a.html': PASS_HTML, f'{RUN}/03-draft-b.html': DRAFT_B},
     [['choose', 'a'], ['append', f'{RUN}/03-draft-b.html', '<!-- 재생성 -->']], 1, ['choice-stale'], '승인 후 시안 b 재생성 (예전 승인)'),
    ('G4', 'pass', {f'{RUN}/state.json': STATE, f'{RUN}/04-components-before.css': BEFORE_CSS, 'components/glowlog.css': AFTER_CSS},
     [], 0, [], '기존 클래스 유지 + 새 클래스 추가'),
    ('G4', 'fail', {f'{RUN}/state.json': STATE, f'{RUN}/04-components-before.css': BEFORE_CSS,
                    'components/glowlog.css': '.chip {\n  border-radius: 6px;\n}\n'},
     [], 1, ['component'], '기존 클래스 .card 삭제'),
    ('S5', 'pass', FULL, CHAIN, 0, [], 'G1~G4 실제 통과 이력 + 정상 최종 화면'),
    ('S5', 'fail', dict(FULL, **{'screens/screen-2.html': one(PASS_HTML, '>오늘 사용<', '>좋아요<')}),
     CHAIN, 1, ['keyword'], '★ 최종 화면에 "좋아요" 버튼'),
]


def main():
    if os.path.isdir(GATES):
        shutil.rmtree(GATES)
    for gate, kind, files, setup, code, rules, desc in CASES:
        case = os.path.join(GATES, gate, kind)
        for rel, text in files.items():
            p = os.path.join(case, 'tree', rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'w', encoding='utf-8').write(text)
        with open(os.path.join(case, 'case.json'), 'w', encoding='utf-8') as fp:
            json.dump({'gate': gate, 'run': RUN, 'setup': setup, 'expect_exit': code, 'expect_rules': rules,
                       '설명': desc}, fp, ensure_ascii=False, indent=2)
    print(f'게이트 예시 {len(CASES)}개 생성: {os.path.relpath(GATES)}')


if __name__ == '__main__':
    main()
