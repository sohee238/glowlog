# Glowlog 디자인 하네스 — 산출물

> 출처: R4 인터뷰 (2026-10-10)
> 단계 정의: `harness/pipeline.md`

## 폴더·파일 구조

```
runs/{YYYYMMDD}-screen{N}[-k]/     ← 같은 이름이 있으면 -2, -3 … (기존 폴더 재사용 금지)
  state.json                ← 진행 상태
  01-refs.md                ← S1 레퍼런스 분석
  02-spec.md                ← S2 화면 설계
  03-draft-a.html           ← S3 시안 A
  03-draft-b.html           ← S3 시안 B
  03-choice.md              ← 본인 선택 기록 (a|b, 이유, 시안 해시) — choose.py만 씀
  04-components-before.css  ← S4 시작 전 공용 컴포넌트 스냅샷
  05-report.json            ← 게이트별 최신 결과(+ 입력 파일 지문 inputs) + 전체 판정 이력 history — judge.py만 씀
screens/screen-{N}.html     ← 최종 화면 (실행 폴더 밖, 덮어쓰기)
components/glowlog.css      ← 공용 컴포넌트 (실행 폴더 밖, 추가만)

harness/                    ← 하네스 정의 (실행 중 수정 금지)
  rules.json                ← 운영 수치 SSOT
  *.md                      ← purpose·pipeline·artifacts·gates·roles·orchestrator·review
  templates/                ← 산출물 양식
  scripts/                  ← judge.py, snapshot.py, choose.py, new_run.py, guard.py
  tests/                    ← run_all.py, run_fixtures.py, run_gates.py, rejudge.py, build_*.py, fixtures/, gates/
```

- 실행 1회 = 폴더 1개. 파일명 앞 숫자는 단계 번호다.
- 최종 결과물(`screens/`, `components/`)은 실행 폴더 밖에 두어, 받는 쪽 에이전트가 항상 같은 경로에서 읽는다.

## 단계별 산출물

| 단계 | 산출물 |
|---|---|
| S1 | `01-refs.md` |
| S2 | `02-spec.md` |
| S3 | `03-draft-a.html`, `03-draft-b.html`, `03-choice.md` |
| S4 | `04-components-before.css`, `components/glowlog.css` (추가분), `screens/screen-{N}.html` |
| 모든 게이트 | `05-report.json` (게이트마다 갱신, history는 추가만) |

## 규칙 SSOT

규칙 원본은 역할별로 2개다 (교재 R4 `harness/rules.yaml`에 해당, PyYAML 미설치로 JSON 사용).

| 원본 | 담는 것 |
|---|---|
| `design.md` `## 판정 규칙 (기계용)` | 디자인 허용값: hex, rgba, radius, font-size, font-weight, blur, spacing, box-shadow, frame |
| `harness/rules.json` | 하네스 운영 수치: 단계·에이전트, 편집 범위, 레퍼런스 최소 수, 시안·선택 파일, 재시도 한도, 금지 키워드·예외 |

- `harness/scripts/judge.py`와 오케스트레이터는 이 두 곳만 읽는다. 다른 문서의 수치와 다르면 이 두 곳이 우선한다.

## 템플릿

| 템플릿 | 사용 |
|---|---|
| `harness/templates/state.json` | 새 실행 시 `new_run.py`가 실행 폴더에 생성 |
| `harness/templates/01-refs.md` | researcher가 S1 작성 형식으로 사용 |
| `harness/templates/02-spec.md` | researcher가 S2 작성 형식으로 사용 |
| `harness/templates/03-choice.md` | 형식 참고용 (**복사 금지** — 실제 파일은 `choose.py`가 씀) |

## 재개

- `state.json` 형식: `harness/templates/state.json` (상세: `harness/orchestrator.md`)
- 재개할 때는 마지막으로 완료되지 않은 단계부터 시작한다.
- 재시도 횟수는 재개해도 초기화하지 않는다.

## 공용 컴포넌트 추가-only 판정

- S4를 시작할 때 `components/glowlog.css`를 `04-components-before.css`로 복사한다.
- S5에서 두 파일을 비교한다.
- 이전 파일에 있던 클래스가 사라졌거나, 정의가 한 글자라도 바뀌었으면 위반이다.
