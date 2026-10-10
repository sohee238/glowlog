# S2 화면 설계 — 화면 1

## 기능 요구사항 체크리스트
- [ ] 관리 카테고리 선택: 화장품 / 뷰티 디바이스 / 피부과 시술 / 마사지·기타 → "카테고리" 카드(component/card) 안에 칩 4개를 가로 줄바꿈으로 한 줄에 배치. 칩은 component/badge 규칙(Badge/Tag): 활성 = effect/iridescent-gradient 배경 + 흰색(#FFFFFF) 텍스트, 비활성 = bg/card-subtle 배경 + text/secondary 텍스트, radius/sm(6px), Label 스타일(fontSize/label 11px, fontWeight/semibold 600, lineHeight 140%, 자간 0.8). 칩 앞에 작은 카테고리 아이콘. 칩은 `<button>`이 아닌 요소(role="radio")로 만들어 CTA 규칙과 충돌하지 않게 하고, 기본 선택은 1개(화장품)
- [ ] 세부 항목 입력: 브랜드명, 제품·시술명, 사용 부위 (선택) → "세부 항목" 카드(component/card) 안에 1행 브랜드명·제품·시술명 2열, 2행 사용 부위 1열의 `<input>` 3개. 모두 component/input 조합(bg/input 배경, 1px border/default 테두리, radius/md 12px, focus 시 interactive/primary 테두리). 각 입력 위에 Label 스타일 라벨(text/secondary), "사용 부위" 라벨 옆에 "선택" 표시(text/muted, Caption), placeholder는 text/muted
- [ ] 사진 첨부: 카메라 촬영 또는 갤러리 선택, 복수 첨부 가능 → "사진" 카드(component/card) 안에 정사각 타일(72px) 가로 나열. 첫 타일은 추가 타일(bg/card-subtle 면 + border/default 점선 테두리 + radius/md, "+" 아이콘 + "촬영·앨범" Caption + 장수 카운터 "2/10" text/muted), 그 뒤에 첨부 썸네일 2장(radius/md, 우상단 원형 삭제 표시 radius 50%). 추가 타일은 `<button>`이 아닌 요소로 만들고, 파일 선택 `<input>`을 넣는다면 component/input 표시를 붙인다
- [ ] 메모 입력 (선택): 피부 반응, 느낌, 주의사항 등 자유 텍스트 → "메모" 카드(component/card) 안에 여러 줄 입력 영역 1개(높이 약 72px), component/input 조합(bg/input, border/default, radius/md). 라벨 옆 "선택" 표시, placeholder "피부 반응, 느낌, 주의사항을 적어두세요"(text/muted, Body)
- [ ] 날짜 자동 입력 (오늘), 수동 변경 가능 → 헤드라인 줄 오른쪽에 날짜 `<input>` 1개(component/input 조합), 기본값 오늘 날짜("2026.10.10 (토)") 표시. 입력 오른쪽 끝에 text/accent 색 달력 아이콘을 두어 탭하면 날짜를 바꿀 수 있음을 표시
- [ ] 저장 시 루틴 목록에 반영 → 화면 하단 고정 "저장하기" 버튼 1개, 가로 꽉 찬 `<button>`, component/button 조합(effect/iridescent-gradient 배경, 흰색 텍스트, Body/Strong 14px 600, radius/lg 20px, padding space/4 space/6). 버튼 위에 Caption 안내 "저장하면 날짜·루틴 목록에 오늘 날짜로 반영돼요"(text/secondary)

## 레이아웃 (위→아래)
1. 프레임 390×844, body 배경 effect/app-background, 좌우 padding space/5(20px), 세로 Auto Layout(flex column), 섹션 간격 space/3(12px) — 한 화면에 모두 들어가야 하므로 스크롤 없이 배치
2. 상단 바(높이 약 48px) — 왼쪽 뒤로가기 아이콘(`<a>` 요소, text/primary), 가운데 제목 "오늘 한 관리"(Heading 2, text/primary). 하단 내비게이션 없음
3. 헤드라인 줄 — 왼쪽 "오늘 어떤 관리를 했나요?"(Heading 1, text/primary) + 아래 Caption 보조 문구(text/secondary), 오른쪽 날짜 입력(component/input)
4. 카테고리 카드 — component/card(effect/frosted-glass-card), Label 라벨 "카테고리" + 칩 4개(component/badge)
5. 세부 항목 카드 — component/card, 입력 3개(component/input), 2열 + 1열, 입력 간격 space/2(8px)
6. 사진 카드 — component/card, 추가 타일 + 썸네일 2장 가로 나열, 타일 간격 space/2
7. 메모 카드 — component/card, 여러 줄 입력 1개(component/input)
8. 하단 고정 영역 — Caption 안내 문구 + "저장하기" 버튼(component/button), 하단 여백 space/6(24px)

카드 내부 padding은 space/4(16px) space/5(20px), 카드 안 라벨과 내용 간격 space/2(8px).

## 사용 토큰
- 색: bg/app, bg/card, bg/card-subtle, bg/input, text/primary, text/secondary, text/muted, text/accent, border/default, border/glass, interactive/primary, interactive/secondary
- 효과: effect/app-background, effect/frosted-glass-card, effect/iridescent-gradient, effect/iridescent-text
- radius: radius/sm(칩), radius/md(입력·사진 타일), radius/lg(카드·버튼)
- 타이포: fontSize/heading1, fontSize/heading2, fontSize/body, fontSize/caption, fontSize/label, fontWeight/normal, fontWeight/semibold, fontWeight/bold, lineHeight/normal, lineHeight/relaxed
- 간격: space/2, space/3, space/4, space/5, space/6
- 컴포넌트: component/card, component/badge, component/input, component/button
- 그림자: 외부 그림자 없음. 깊이는 bg/app 대비와 border/glass로 표현

## 레퍼런스 반영
- 달다방: 위→아래 한 화면 구조(분류 → 이름 입력 → 메모 → 하단 고정 저장 버튼), 저장 버튼 하단 고정·채움 강조
- 닥터다이어리: "오늘 어떤 관리를 했나요?" 질문형 헤드라인, 하단 CTA는 가로 꽉 찬 라운드 버튼 1개, 파스텔 그라디언트는 effect/iridescent-gradient로 대체
- 럽맘(칩 그리드): 카테고리 4종을 칩으로 한 번에 노출, 섹션마다 라벨을 필드 위에 둔다 (선택 상태 표현은 design.md Badge/Tag 규칙으로 대체)
- 베이비빌리: 칩 앞 작은 아이콘, 가로 줄바꿈 배치, 바텀시트 대신 본문 상단에 바로 노출 (칩 모양은 알약형 대신 radius/sm 6px)
- 럽맘(사진추가): 정사각 타일 가로 나열, 첫 타일은 점선 추가 + 장수 카운터, 썸네일 우상단 삭제 표시, 타일 모서리 라운드 통일
- 집지켜: 칩 → 입력 → 사진 → 메모 → 하단 버튼 순서와 섹션 간격 리듬
