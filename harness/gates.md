# Glowlog 디자인 하네스 — 게이트

> 출처: R5 인터뷰 (2026-10-10)
> 단계: `harness/pipeline.md` / 산출물: `harness/artifacts.md`
> 디자인 허용값 원본: `design.md` `## 판정 규칙 (기계용)` / 금지 키워드·게이트 수치·편집 범위 원본: `harness/rules.json`
> 수치 원본: `harness/rules.json` — 이 문서의 표와 다르면 rules.json이 우선한다.

## 게이트 통과 조건

| 게이트 | 대상 | 통과 조건 (모두 충족) |
|---|---|---|
| G1 | `01-refs.md` | ① 레퍼런스 ≥ 3개 ② 레퍼런스마다 uibowl `ui_url` 1개 + "반영 포인트" ≥ 1줄 ③ ★ 금지 키워드 0건 |
| G2 | `02-spec.md` | ① PRD 해당 화면 기능 요구사항 bullet 수 = spec 체크리스트 항목 수 (화면 1·2·3 = 6·5·5) ② ★ 금지 키워드 0건 |
| G3 | `03-draft-a.html`, `03-draft-b.html` | ① 파일 2개 존재 ② 각 390×844 ③ HTML 허용값 위반 0건 (`data-token` 검사 면제) ④ ★ 금지 키워드 0건 ⑤ `position: absolute`/`fixed` 0건 ⑥ 렌더 판정 위반 0건 (`render-*`) ⑦ 외부 참조 0건 — `<link rel=stylesheet>`, `@import`, `<script|img|source|iframe src>`, `url(…)` 중 `data:`가 아닌 것 (`self-contained`, Figma 가져오기용 단독 파일) |
| 사람 승인 (CHOICE) | `03-choice.md` | ① 첫 줄이 `a` 또는 `b` ② `drafts:` 줄의 시안 해시 = 현재 `03-draft-a/b.html` 해시 |
| G4 | `04-components-before.css`, `components/glowlog.css` | ① 스냅샷 존재 ② 이전 클래스 삭제 0건 ③ 이전 클래스 정의 변경 0건 |
| S5 | `screens/screen-{N}.html` | ① 390×844 ② HTML 허용값 위반 0건 ③ `data-token` 누락 0건 ④ ★ 금지 키워드 0건 ⑤ 편집 범위 밖 수정 파일 0건 (`harness/roles.md`) ⑥ `position: absolute`/`fixed` 0건 ⑦ `data-token` 값이 `design.md` 토큰명에 존재 ⑧ CHOICE 조건 재확인 (승인 후 시안 변경 0건) ⑨ G1~G4·CHOICE의 마지막 판정이 PASS이고 그 입력 파일 지문이 지금과 같음 (`gate-not-passed`·`report-stale` 0건) ⑩ 판정 이력 순서 위반 0건 (`order`) ⑪ `state.json` retries = 이력의 FAIL 수 (`retries`, `--adhoc` 판정 제외) ⑫ 렌더 판정 위반 0건 (`render-*`) ⑬ `data-token` 값이 실제 계산값에 쓰임 (`token-value`) |

★ = `story-service.md` "어기면 안 되는 것"(SNS 기능, AI 피부 분석) 위반 시 걸리는 조건

## HTML 허용값 검사 항목

hex, rgba, radius, font-size, font-weight, blur, padding·margin·gap, box-shadow(`inset`만), 프레임 크기, 그라디언트(`gradient`: Effects 코드와 각도·색 순서까지 동일)
→ 허용값은 `design.md` 판정 섹션만 참조한다. 금지 키워드는 `harness/rules.json` `keywords.forbidden`.

## 렌더 판정 (G3·S5)

- 헤드리스 Chrome(`harness/rules.json` `render`)으로 390×844 창에 그린 뒤, 요소마다 **브라우저 계산값**을 `design.md` 허용값과 대조한다. 파일에 적히지 않은 값(브라우저 기본 margin, 상속된 글자색)도 잡는다.
- `render-frame`: body 계산 크기 ≠ 390×844 또는 내용이 프레임 밖으로 넘침
- `render-color`: 글자가 있는 요소의 color, 모든 요소의 배경·테두리·그라디언트·그림자 색
- `render-font-size`·`render-font-weight`: 글자가 있는 요소만
- `render-spacing`·`render-radius`·`render-blur`·`render-box-shadow`: 모든 요소
- `white-bg`: 순수 흰색(#FFFFFF, 불투명) 배경 요소
- `app-background`: body 배경이 App Background 그라디언트가 아님
- `text-style`: 글자가 있는 요소의 (크기, 굵기, 행간, 자간)이 design.md Text Styles 7개 중 어느 것과도 일치하지 않음
- `component-rule`: `data-token`에 `component/*`가 있는 요소가 design.md `component-rules` 조합을 만족하지 않음
- `component-missing` (S5만): design.md `component-detect` 특징(frosted 카드 배경, 하단 내비 배경, `<button>`, radius 6·11px 배지, `<input>`)을 가진 요소에 해당 `component/*` 표시가 없음 — 표시를 빼서 조합 검사를 피하는 것을 막는다
- `token-value` (S5만): `data-token`의 토큰 값(design.md 표, 효과는 Effects 코드블록의 특징)이 그 요소의 계산값에 실제로 있어야 한다
- Chrome이 없거나 제한 시간을 넘기면 판정을 건너뛰지 않고 `render-unavailable`로 FAIL

## 금지 키워드 검사 범위

- 대상: HTML에 보이는 텍스트, `01-refs.md`, `02-spec.md`
- 예외: 문서에서 `제외:`로 시작하는 줄
- 영문 키워드는 단어 경계(`\b`)로만 센다 (예: `like`는 `likely`에 걸리지 않음)
- `harness/rules.json` `keywords.exceptions`에 있는 구절 안의 일치는 세지 않는다 (예: `피드백`)
- 부정문("~하지 않는다", "~없이")도 자동으로 봐주지 않는다. 문서는 `제외:` 줄로, 화면 오탐은 본인이 예외 **구절**(예: `로그인 없이`)을 추가해서 처리한다
- 리포트에는 걸린 키워드와 그 문장 문맥을 함께 기록한다 (예: `"로그인" — …로그인 없이 바로 기록해요…`)

## 🚦 / 👀

- `design.md`에서 🚦가 붙은 규칙은 위 판정 규칙명으로 검사된다. `harness/tests/run_fixtures.py`가 🚦 규칙마다 실패 샘플이 있는지 확인한다.
- 👀가 붙은 규칙은 스크립트로 셀 수 없어 사람 승인 지점에서 본인이 확인한다.

## 사람 승인 지점 (1곳)

- S3 시안 선택. `03-choice.md` 첫 줄에 `a` 또는 `b`가 적혀야 S4로 진행한다.
- `03-choice.md`는 `harness/scripts/choose.py`만 쓴다. 승인 시점의 시안 해시를 함께 기록하므로, 승인 후 시안이 다시 만들어지거나 수정되면 승인은 무효(`choice-stale`)가 되고 본인이 다시 골라야 한다.
- S5를 통과하면 사람 확인 없이 자동으로 완료한다.

## 실패 시 복귀

| 게이트 실패 | 복귀 | 최대 | 초과 시 |
|---|---|---|---|
| G1 | S1 (키워드 변경) | 2회 | 멈추고 보고 |
| G2 | S2 재작성 | 2회 | 멈추고 보고 |
| G3 | S3 재생성 | 2회 | 멈추고 보고 |
| 시안 둘 다 반려 | S2 | 1회 | 멈추고 보고 |
| G4 또는 S5 | S4 | 3회 | 멈추고 보고 |
