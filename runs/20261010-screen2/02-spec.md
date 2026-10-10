# S2 화면 설계 — 화면 2

## 기능 요구사항 체크리스트
- [ ] 진행 중인 루틴 카드 목록 (루틴명, 최근 기록일, 다음 예정일) → 상단 "진행 중인 루틴" 섹션에 component/card 세로 목록. 카드마다 루틴명(Heading 2) + 최근 기록일(Caption, text/secondary) + 다음 예정일(Body/Strong, text/accent). 카드 우측에 Before / After 비교 진입용 텍스트 링크(text/accent)
- [ ] 월 달력 뷰: 기록이 있는 날짜 표시 (점 또는 색상) → component/card 안에 연월 제목(Heading 2) + 좌우 화살표 월 이동 + 요일 헤더(Label) + 7열 날짜 그리드. 기록이 있는 날짜 숫자 아래 작은 점(interactive/accent), 오늘은 원형 배경(interactive/secondary), 다른 달 날짜는 text/muted
- [ ] 날짜 탭 시 해당 날짜 기록 요약 표시 → 달력 아래 "선택한 날짜 기록" 영역. 선택 날짜는 iris/200 원형 배경으로 강조, 그날 기록을 카테고리(화장품 / 뷰티 디바이스 / 피부과 시술 / 마사지·기타)별 component/card로 쌓아 제목 + 제품·시술명 + 사용 부위·메모 한 줄 표시. 기록이 없으면 카드 안에 빈 상태 문구 "이 날은 기록이 없어요"(text/muted)
- [ ] 루틴별 사용 주기 설정 (매일 / 격일 / 주 N회 / 자유) → 루틴 카드 루틴명 옆 주기 component/badge(예: "격일", "주 2회"). 카드 탭 시 바텀시트(radius/xl, effect/frosted-glass-card)에서 주기 선택 4개 세그먼트(매일 / 격일 / 주 N회 / 자유)와 주 N회 횟수 선택, 하단에 "루틴 종료" 텍스트 버튼, 저장 component/button
- [ ] 다음 사용 예정일 자동 계산 및 표시 → 최근 기록일 + 주기로 계산한 예정일을 카드에 "다음 예정 10.12 (D-2)" 형식으로 표시, D-n은 활성 component/badge(effect/iridescent-gradient). 오늘이 예정일이면 "오늘" 배지(interactive/accent). 주기가 '자유'인 카드는 예정일·D-n을 표시하지 않고 최근 기록일만 표시

## 레이아웃 (위→아래)
1. 헤더 — 화면 제목 "루틴" (fontSize/heading1, Heading 1) + 오른쪽 오늘 날짜 Caption
2. 진행 중인 루틴 섹션 — 섹션 라벨(Label) + component/card 루틴 카드 세로 목록 (카드 간격 space/3), 카드 내부 component/badge(주기, D-n)
3. 월 달력 — component/card 1개, 연월 제목 + 화살표, 요일 헤더, 7열 날짜 그리드, 기록 점
4. 선택한 날짜 기록 요약 — 섹션 라벨(Label, 선택 날짜) + 카테고리별 component/card 목록 또는 빈 상태 카드
5. 하단 내비게이션 — component/bottom-nav (기록 / 루틴 / 비교), 현재 탭 "루틴" 활성
6. 주기 설정 바텀시트 (카드 탭 시 표시되는 상태) — radius/xl 시트, 주기 세그먼트 4개 + component/button 저장

## 사용 토큰
- 색: bg/app, bg/card, bg/card-subtle, border/glass, border/default, text/primary, text/secondary, text/muted, text/accent, interactive/primary, interactive/secondary, interactive/accent, iris/200
- radius: radius/sm (배지), radius/md (주기 세그먼트), radius/lg (카드·CTA 버튼), radius/xl (바텀시트)
- 타이포: fontSize/heading1 (화면 제목), fontSize/heading2 (카드 제목·연월), fontSize/body (본문·날짜 숫자), fontSize/caption (최근 기록일·보조 설명), fontSize/label (섹션 라벨·배지·요일 헤더)
- 간격: space/2, space/3, space/4, space/5, space/6
- 효과: effect/frosted-glass-card (루틴 카드·달력 카드·요약 카드·바텀시트), effect/iridescent-gradient (D-n 활성 배지·저장 버튼), effect/app-background (body 배경). 비활성 배지는 bg/card-subtle + text/secondary

## 레퍼런스 반영
- 미니모어맥스: 기록이 있는 날짜를 숫자 아래 작은 점으로 표시, 연월 제목 + 좌우 화살표로 월 이동, 선택 날짜 강조 배경. 다크 배경 대신 design.md 토큰 색 사용
- 열품타: 오늘 날짜 원형 배경, 다른 달 날짜는 text/muted로 낮춤. 날짜 칸에는 점만 두고 요약은 달력 아래 별도 영역에 표시
- 오늘의 루틴: 루틴 카드에 루틴명 + 주기 라벨 + D-n 한 줄 구성, 카드 메뉴에서 주기 수정과 루틴 종료(아카이브)로 진입. 주기 '자유' 카드는 D-n 없이 최근 기록일만 표시
- 앳플리: 날짜 탭 시 기록 요약을 카테고리별 카드로 쌓는 구조(제목 + 핵심 값 + 보조 설명 3단 위계), 기록 없는 날짜의 빈 상태 문구
