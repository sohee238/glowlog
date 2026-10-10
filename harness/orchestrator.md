# Glowlog 디자인 하네스 — 오케스트레이터

> 출처: R7 인터뷰 (2026-10-10)
> 오케스트레이터 = 메인 Claude 세션. `CLAUDE.md` `## 하네스 실행`에서 이 파일로 진입한다.

## 실행 전 읽기

트리거를 받으면 단계를 시작하기 전에 아래 파일을 읽는다.
`harness/purpose.md` → `harness/pipeline.md` → `harness/artifacts.md` → `harness/gates.md` → `harness/roles.md` → `harness/rules.json` → `design.md`

## 진행 순서

1. 트리거를 해석한다 (`harness/roles.md` 자연어 트리거 표)
2. 새 실행이면 `python3 harness/scripts/new_run.py --screen {N} --keywords "A,B"`로 실행 폴더를 만든다 (같은 이름이 있으면 `-2`, `-3` …, `state.json`은 템플릿에서 생성. `03-choice.md` 템플릿은 복사하지 않는다). 재개면 `state.json`의 `stage`부터 시작한다
3. 단계 시작: `python3 harness/scripts/snapshot.py {단계} --run runs/{id}` 로 `snapshots.{단계}`를 기록한다
4. 해당 단계 에이전트를 호출한다 (S1·S2 → `researcher`, S3·S4 → `designer`)
5. 단계 종료: `judge`를 호출해 해당 게이트를 판정한다 (`python3 harness/scripts/judge.py {게이트} --run runs/{id}`)
6. 통과하면 `state.json`의 `stage`를 다음 단계로 갱신한다. 실패하면 `harness/rules.json` `retries`에 따라 되돌아가고 해당 `retries` 키를 +1 한다 (G1·G2·G3 FAIL → 같은 이름 키, G4·S5 FAIL → `G4_S5`, 본인 반려 → `reject`). S5는 이 값을 `05-report.json` `history`의 FAIL 수와 대조한다
7. S3를 통과하면 멈추고, 시안 2개와 함께 `design.md`의 👀 규칙 목록을 체크리스트로, `harness/rules.json` `figma` 값으로 Figma 가져오기 안내(시안 파일 경로 2개, 플러그인, 뷰포트)를 보여준 뒤 본인의 시안 선택을 기다린다. 본인이 "a로 할게"/"b로 할게"라고 말했을 때만 `python3 harness/scripts/choose.py {a|b} --run runs/{id} --reason "{본인이 말한 이유}"`를 실행하고, CHOICE 게이트를 판정한다
8. S4를 시작할 때 Bash로 `cp components/glowlog.css runs/{id}/04-components-before.css` (첫 실행이라 `glowlog.css`가 없으면 `touch runs/{id}/04-components-before.css`)
9. S5를 통과하면 `state.json`의 `stage`를 `DONE`으로 바꾸고 완료를 보고한다 (`DONE`이 아닌 실행이 있는 동안 guard가 고정 문서 수정을 막는다)

> `keyword` 위반이 오탐으로 보이면(예: "로그인 없이") 재시도하지 말고 멈춰서, 걸린 문맥을 보여주고 본인에게 예외 구절 추가 여부를 묻는다. 오케스트레이터와 에이전트는 `rules.json`을 고치지 않는다.

## 반드시 지킬 규칙

| # | 규칙 | 셀 수 있는 기준 |
|---|---|---|
| 1 | 산출물(01~03, `screens/`, `components/`)을 직접 작성하지 않는다 | 오케스트레이터 작성 0건 |
| 2 | 모든 단계 종료 시 `judge`를 호출한다 | S5에서 G1~G4·CHOICE 판정 기록 누락 0건 (`gate-not-passed`) |
| 3 | 게이트를 통과하기 전에는 다음 단계를 시작하지 않는다 | S5에서 이력 순서 위반 0건 (`order`), PASS 후 입력 변경 0건 (`report-stale`) |
| 4 | CHOICE 게이트(선택값 + 시안 해시) 통과 없이 S4를 시작하지 않는다. `03-choice.md`를 직접 쓰지 않고 본인 발화 없이 `choose.py`를 실행하지 않는다 | 승인 없는 S4 시작 0건 |
| 5 | 고정 문서는 실행 중 수정하지 않는다 (`PRD.md`, `design.md`, `CLAUDE.md`, `story-*.md`, `harness/` 전체) | 수정 0건 |
| 6 | 단계를 넘어갈 때마다 `state.json`을 갱신한다 | S5에서 `retries` = 이력 FAIL 수 (`retries`) |

## state.json 형식

```json
{
  "stage": "S3",
  "screen": 2,
  "keywords": ["달력", "루틴"],
  "retries": { "G1": 0, "G2": 0, "G3": 0, "reject": 0, "G4_S5": 1 },
  "snapshots": {
    "S1": { "runs/.../01-refs.md": "2026-10-10T10:00:00" }
  }
}
```

- `judge.py`는 `snapshots.{단계}`와 다음 스냅샷(또는 현재 상태)을 비교해, 그 단계에서 바뀐 파일을 해당 에이전트의 허용 범위와 대조한다.

## 멈춤 보고 형식 (5줄 고정)

```
멈춘 단계: S4
실패 게이트: S5
위반 상위 5건: (05-report.json에서 발췌)
재시도: 3/3
제안 다음 행동: (1개)
```

## 사전 차단 (guard 훅)

`.claude/settings.json`의 PreToolUse 훅이 모든 Write·Edit·Bash 호출 전에 `harness/scripts/guard.py`를 실행한다 (저장소에 커밋되어 동료 환경에도 적용). 규칙은 `harness/rules.json` `guard`·`scope`.

| 호출자 | 막는 것 |
|---|---|
| researcher·designer | 편집 범위(`scope`) 밖 쓰기, 프로젝트 밖 쓰기, Bash 전부 |
| judge | 모든 쓰기, `judge.py {게이트} --run runs/{id} [--adhoc]` 외 Bash |
| 오케스트레이터(메인) — 실행 중일 때만 | 고정 문서 쓰기, `03-choice.md` 직접 쓰기(→ `choose.py`), `state.json`·`04-components-before.css`·`review.md` 외 파일 쓰기, 고정 문서·선택 기록을 건드리는 Bash 쓰기 명령 |

- 실행 중 = `runs/*/state.json` 중 `stage`가 `DONE`이 아닌 것이 있음. 실행이 없을 때는 본인이 하네스를 자유롭게 정비할 수 있다.
- guard 내부 오류는 차단으로 처리한다 (fail-closed). 단, `python3` 자체가 없으면 훅이 실행되지 못해 통과된다 (Claude Code 2.1.283은 `onFailure: block` 미지원).
- Bash 보호 경로는 프로젝트 기준 경로로 쓰였을 때만 센다 (단어 시작·`./`·프로젝트 절대경로 뒤). 프로젝트 밖 `~/.claude/...`나 신뢰 스크립트 호출 경로(`python3 harness/scripts/snapshot.py`)는 세지 않는다 (2026-10-10 오탐 2건 수정)
- Bash 쓰기 판정은 패턴 기반(최선)이며, 빠져나간 경우는 S5 `scope`·`report-stale` 사후 판정이 잡는다.
