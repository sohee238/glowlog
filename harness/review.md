# Glowlog 디자인 하네스 — 검증과 리뷰

> 출처: R8 인터뷰 (2026-10-10)
> 게이트: `harness/gates.md` / 오케스트레이터: `harness/orchestrator.md`

## 1. 판정 스크립트 검증 (하네스 사용 전 필수)

**한 번에 돌리기 (규칙을 고칠 때마다):** `python3 harness/tests/run_all.py` — 하나라도 깨지면 종료 코드 1

| 단계 | 스크립트 | 확인하는 것 |
|---|---|---|
| 1 | `run_fixtures.py` | 판정 함수 샘플 68건 + 🚦 커버리지 + guard 26건 (아래 표) |
| 2 | `run_gates.py` | 게이트 예시 12개(`harness/tests/gates/{게이트}/{pass,fail}`)를 임시 폴더에서 **실제 명령**으로 판정 — 결과 코드·위반 규칙·리포트 기록 |
| 3 | `run_all.py` 내장 | 재판정 자기 검증: 옛 규칙 시절 이력 `pass-history`를 지금 규칙으로 재판정하면 알려진 깨짐(G3·S5)을 정확히 찾는가 |
| 4 | `rejudge.py` | 실제 `runs/*`를 지금 규칙으로 재판정(`--dry`, 기록 없음). 예전 PASS → 지금 FAIL이면 깨짐. 입력 파일이 바뀐 게이트는 생략, S5 `scope`는 시간 의존이라 제외 |

- 검증 (2026-10-10): 4/4 통과, 약 18초. 복사본에서 `design.md` allowed-font-size의 `11px`을 지우자 1단계가 32/68로 깨지고 종료 코드 1 — 규칙 변경이 기존 판정을 깨는 것을 잡음
- 예시 재생성: `build_fixtures.py`(HTML 샘플), `build_gate_cases.py`(게이트 예시). 규칙을 의도적으로 바꿨다면 샘플·기대값을 고친 뒤 다시 4/4를 확인한다


- 위치: `harness/tests/fixtures/`
- 검사 68건 = 정적 판정 17 + 렌더 판정 10 + 렌더 샘플의 정적 통과 확인 9 + 디렉터리 샘플 6 + guard 26
- 샘플 목록과 기대값의 원본은 `harness/tests/fixtures/expected.json` (아래 표는 종류별 요약)
- HTML 샘플은 `pass.html`에서 `harness/tests/build_fixtures.py`가 생성한다. `pass.html`을 고치면 이 스크립트를 다시 돌린다
- 🚦 커버리지: `design.md`의 🚦 규칙마다 그 규칙으로 실패하는 샘플이 1개 이상 있어야 한다 (현재 15/15)

| 종류 | 샘플 | 기대 |
|---|---|---|
| 정적 통과 | `pass.html`, `exc:fail-keyword-phrase` (예외 구절 추가 가정) | 0 |
| 정적 실패 | `fail-hex` `fail-rgba` `fail-radius` `fail-font-size` `fail-font-weight` `fail-blur` `fail-spacing` `fail-box-shadow` `fail-frame` `fail-data-token` `fail-token-name` `fail-position` `fail-keyword` `fail-keyword-phrase` `fail-gradient` | 각 1 |
| 렌더 통과 | `render:pass.html` | 0 |
| 렌더 실패 (같은 파일 정적 판정은 0) | `fail-render-margin` `fail-render-color` `fail-token-value` `fail-render-overflow` `fail-white-bg` `fail-text-style` `fail-component-rule` `fail-component-missing` `fail-app-background` | 각 1 |
| 디렉터리 | `fail-component` `fail-scope` / `pass-history` / `fail-report-stale` `fail-retries` `fail-order` | 1 / 0 / 각 1 |

- 통과 기준: 68건 모두에서 기대 위반 수 = 실제 위반 수, 위반 규칙 이름도 일치
- 하나라도 어긋나면 하네스를 사용하지 않는다.

## 2. 리뷰에서 보강한 규칙

| # | 구멍 | 보강 | 반영 위치 |
|---|---|---|---|
| ① | Auto Layout 검사 없음 | `position: absolute`/`fixed` 0건 (G3·S5) | `harness/gates.md` |
| ② | 한글 키워드 오탐 (피드 → 피드백) | `keywords.exceptions` 목록 | `harness/rules.json` |
| ③ | `data-token` 임의 값 통과 | `data-token` 값이 `design.md` 토큰명에 존재해야 함 (S5) | `harness/gates.md` |
| ④ | 실패 복귀 표 중복 | `harness/gates.md` 하나로 일원화 | `harness/pipeline.md` |

## 3. 사전 차단 훅 (도입, 2026-10-10)

- 동료가 받은 저장소에서도 권한 강제가 유지되도록 저장소에 커밋되는 `.claude/settings.json`에 등록했다 (`settings.local.json`·`~/.claude/settings.json` 아님).
- `harness/scripts/guard.py` 검증: `guard:` 케이스 26건 (차단 17 · 통과 9) — 훅 stdin과 같은 입력으로 실제 실행해 판정. 차단 사유도 각 규칙과 일치함을 확인
- 깨진 입력 → 차단 (fail-closed) 확인

## 4. 시범 실행 리뷰

- 대상: 화면 2 (날짜·루틴 목록), 1회
- 기록: `runs/{id}/review.md`

| 리뷰 항목 | 통과 기준 |
|---|---|
| 완료 여부 | S5 통과 |
| 사람 개입 | 정확히 1회 (시안 선택) |
| 총 재시도 | 한도 이내 |
| 오케스트레이터 규칙 1~6 | 위반 0건 |
| ★ 금지 키워드 | 0건 |

## 5. 파일 ≠ 실제 상태 (2026-10-10 추가)

| # | 구멍 | 처리 |
|---|---|---|
| 1 | CSS에 적힌 값 ≠ 브라우저 계산값 (기본 margin, 상속 색) | 해결 — 헤드리스 Chrome 렌더 판정 (`render-*`). 원인: Chrome이 dump 후 종료하지 않음 → 출력 확인 후 직접 종료 |
| 2 | `data-token` 이름 ≠ 실제 값 | 해결 — 토큰 값 대조 (`token-value`) |
| 3 | 리포트 PASS 이후 파일 변경 | 해결 — 게이트별 입력 지문 + S5 재확인 (`report-stale`) |
| 4 | `state.json` 자기 보고 | 해결 — 판정 이력 history + S5 대조 (`order`, `retries`, `gate-not-passed`) |
| 5 | HTML ≠ Figma | 범위 밖 (본인 수동) |

## 6. 🚦 커버리지 (2026-10-10 추가)

- 🚦 규칙 15개: `hex` `rgba` `render-color` `blur` `gradient` `app-background` `box-shadow` `text-style` `font-size` `font-weight` `radius` `spacing` `component-rule` `component-missing` `white-bg` — 모두 실패 샘플 있음
- `component-missing` 한계: `<div>`로 만든 버튼, frosted subtle(0.45) 보조 카드는 특징으로 잡히지 않는다 (designer 지침으로 `<button>` 강제)
- 👀 규칙 5개: 디자인 무드, 그라디언트 사용 위치, Label 대문자, radius 용도, 키워드 밖 표현의 금지 기능 → S3 시안 선택 때 본인 확인
- design.md 밖의 규칙(`frame`, `position`, `data-token`, `token-name`, `token-value`, `keyword`, `component`, `scope`, 이력 규칙)도 각각 실패 샘플이 있다
