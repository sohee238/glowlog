# Glowlog Design System

> 🚦 = `harness/scripts/judge.py`가 검사하는 규칙. 뒤의 `이름`은 위반 규칙명이며, 각 이름마다 실패 샘플이 있어야 한다 (`harness/tests/run_fixtures.py`가 확인).
> 👀 = 스크립트로 셀 수 없는 규칙. S3 시안 선택(사람 승인) 때 본인이 확인한다.

## 디자인 무드
> 👀 무드 전체 (매트한 유리 질감, 바랜 파스텔 톤)
- Frosted glass — blur가 강하지 않고 뽀얗게 매트한 유리 느낌
- Iridescent — 핑크 → 라벤더 → 민트가 은은하게 섞이는 홀로그램 그라디언트
- 배경은 쿨 그레이 기반 — 오브젝트가 부드럽게 떠 있는 느낌
- 채도가 낮은 파스텔 — 비비드하지 않고 뽀얗게 바랜 톤

---

## Color Tokens
> 🚦 `hex` `rgba` `render-color` — 아래 표의 색(판정 섹션 allowed-hex·allowed-rgba)만. 브라우저가 계산한 색까지 검사

### Primitives
| 토큰명 | HEX | 용도 |
|---|---|---|
| neutral/50 | #F5F4F7 | 가장 밝은 배경 |
| neutral/100 | #E8E7ED | 앱 배경 |
| neutral/200 | #C9C7D4 | border, divider |
| neutral/400 | #9491A7 | muted text |
| neutral/600 | #5C5872 | secondary text |
| neutral/900 | #2E2B3F | primary text |
| iris/50 | #EDE9F9 | 라벤더 연한 tint |
| iris/200 | #C9BFF0 | soft accent |
| iris/500 | #8B7ED8 | primary 라벤더 |
| iris/700 | #5C4FB8 | pressed/dark |
| rose/50 | #FCE8EF | 핑크 연한 tint |
| rose/200 | #F2B8CC | soft accent |
| rose/500 | #E07399 | accent 핑크 |
| mist/50 | #E2F3F0 | 민트 연한 tint |
| mist/200 | #A3D9D1 | soft accent |

### Semantic
| 토큰명 | 값 | 용도 |
|---|---|---|
| bg/app | #E8E7ED | 전체 앱 배경 |
| bg/card | rgba(255,255,255,0.72) | 카드 배경 |
| bg/card-subtle | rgba(255,255,255,0.45) | 보조 카드 |
| bg/input | #F5F4F7 | 인풋 배경 |
| text/primary | #2E2B3F | 본문 |
| text/secondary | #5C5872 | 설명, 레이블 |
| text/muted | #9491A7 | placeholder, hint |
| text/accent | #8B7ED8 | 강조, 링크 |
| border/default | #C9C7D4 | 카드, 인풋 테두리 |
| border/glass | rgba(255,255,255,0.70) | frosted 카드 테두리 |
| interactive/primary | #8B7ED8 | 버튼, CTA |
| interactive/secondary | #EDE9F9 | 선택 상태 |
| interactive/accent | #E07399 | 오늘 사용 배지 등 |

---

## Effects (Variables로 표현 불가 — 반드시 코드/스타일로 직접 구현)

### Frosted Glass Card
> 🚦 `blur` `component-rule` — 카드는 `data-token`에 `component/card`를 붙이고 아래 조합을 모두 만족
카드의 기본 스타일. blur는 약하게, 반투명 흰색으로 매트하고 뽀얀 느낌을 구현.
```css
background: rgba(255, 255, 255, 0.72);
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
border: 1px solid rgba(255, 255, 255, 0.70);
border-radius: 20px;
```

### Frosted Glass Card (Subtle)
보조 카드, 배지 등 더 연한 버전.
```css
background: rgba(255, 255, 255, 0.45);
backdrop-filter: blur(8px);
-webkit-backdrop-filter: blur(8px);
border: 1px solid rgba(255, 255, 255, 0.55);
border-radius: 20px;
```

### Iridescent Gradient
> 🚦 `gradient` — 각도·색 순서까지 아래 코드와 동일 / 👀 CTA 버튼·배지·타이틀 등 핵심 강조 요소에만 사용
CTA 버튼, 프로젝트 배지, 앱 타이틀 등 핵심 강조 요소에 사용.
핑크 → 라벤더 → 민트 순서로 135도 방향.
```css
background: linear-gradient(135deg, #F2C4CE, #E8D5F5, #C5D8F7, #C5EDE0);
```

### Iridescent Text
> 🚦 `gradient`
앱 타이틀(Glowlog), 주요 수치 강조에 사용.
```css
background: linear-gradient(135deg, #F2C4CE, #E8D5F5, #C5D8F7, #C5EDE0);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

### App Background
> 🚦 `app-background` `gradient` — body 배경은 이 그라디언트
단순 단색이 아닌 은은한 그라디언트 배경.
```css
background: linear-gradient(160deg, #EEEAF5 0%, #E8E7ED 50%, #E5EEF0 100%);
```

### Inner Glow (선택적)
> 🚦 `box-shadow` — inset만 허용
카드에 은은한 내부 빛 효과.
```css
box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
```

---

## Typography

### Variables
| 토큰명 | 값 |
|---|---|
| fontSize/display | 26px |
| fontSize/heading1 | 20px |
| fontSize/heading2 | 16px |
| fontSize/body | 14px |
| fontSize/caption | 12px |
| fontSize/label | 11px |
| fontWeight/normal | 400 |
| fontWeight/medium | 500 |
| fontWeight/semibold | 600 |
| fontWeight/bold | 700 |
| fontWeight/extrabold | 800 |
| lineHeight/tight | 1.3 |
| lineHeight/normal | 1.5 |
| lineHeight/relaxed | 1.6 |

### Text Styles
> 🚦 `text-style` `font-size` `font-weight` — 글자가 있는 요소의 크기·굵기·행간·자간이 아래 7개 스타일 중 하나와 일치 / 👀 Label 대문자(한글은 해당 없음)
| 스타일명 | Size | Weight | Line Height | Letter Spacing | 용도 |
|---|---|---|---|---|---|
| Display | 26px | 800 | 130% | -0.5 | 앱 타이틀 |
| Heading 1 | 20px | 700 | 140% | -0.3 | 섹션 헤더 |
| Heading 2 | 16px | 700 | 150% | 0 | 카드 제목 |
| Body | 14px | 400 | 160% | 0 | 본문 |
| Body/Strong | 14px | 600 | 160% | 0 | 강조 본문 |
| Caption | 12px | 400 | 150% | 0 | 보조 설명 |
| Label | 11px | 600 | 140% | 0.8 | 섹션 라벨 (대문자) |

---

## Radius
> 🚦 `radius` / 👀 용도(배지·인풋·카드·시트) — 컴포넌트 표시가 있는 요소는 `component-rule`로 검사
| 토큰명 | 값 | 용도 |
|---|---|---|
| radius/sm | 6px | 배지, 태그 |
| radius/md | 12px | 인풋, 작은 카드 |
| radius/lg | 20px | 카드, 리스트 아이템 |
| radius/xl | 32px | 바텀시트, 모달 |

---

## Spacing
> 🚦 `spacing`
| 토큰명 | 값 |
|---|---|
| space/1 | 4px |
| space/2 | 8px |
| space/3 | 12px |
| space/4 | 16px |
| space/5 | 20px |
| space/6 | 24px |
| space/8 | 32px |

---

## 컴포넌트 규칙
> 🚦 `component-rule` `component-missing` — 판정 섹션 `component-detect` 특징을 가진 요소(frosted 카드 배경, 하단 내비 배경, `<button>`, radius 6·11px 배지, `<input>`)는 `data-token`에 해당 `component/*` 표시가 반드시 있어야 하고, `data-token`에 `component/card`·`component/button`·`component/badge`·`component/bottom-nav`·`component/input`을 붙인 요소는 판정 섹션 `component-rules`의 조합을 모두 만족

### Card
- 기본: Frosted Glass Card 스타일 적용
- 내부 padding: space/4 (16px) space/5 (20px)
- 반드시 border/glass 테두리 사용

### Button (Primary CTA)
- Iridescent Gradient 배경
- 텍스트: 흰색, Body/Strong
- border-radius: radius/lg (20px)
- padding: space/4 (16px) space/6 (24px)

### Badge / Tag
- 활성: Iridescent Gradient 배경, 흰색 텍스트
- 비활성: bg/card-subtle, text/secondary
- border-radius: radius/sm (6px)
- font: Label 스타일

### Bottom Navigation
- 배경: rgba(255,255,255,0.55), blur(20px)
- border-top: 1px solid border/glass
- 활성 아이콘: Iridescent Gradient (text fill)
- 비활성 아이콘: text/muted

### Input
- 배경: bg/input (#F5F4F7)
- border: 1px solid border/default
- border-radius: radius/md (12px)
- focus border: interactive/primary

---

## 사용 금지
- 순수 흰색 배경 카드 (반드시 반투명 처리) 🚦 `white-bg`
- 강한 drop shadow (box-shadow 사용 금지, inner glow만 허용) 🚦 `box-shadow`
- 채도 높은 원색 (모든 컬러는 위 팔레트에서만 사용) 🚦 `hex` `render-color`
- blur 값 20px 초과 (과한 유리 효과 금지) 🚦 `blur`
- 금지 기능(SNS·AI 분석·커머스·로그인·알림)을 키워드 밖 표현으로 넣는 것 (예: "친구에게 보내기") 👀 — 키워드는 `harness/rules.json`에서 `keyword`로 검사

---

## 판정 규칙 (기계용)

> 판정 스크립트가 읽는 디자인 허용값. 각 목록은 코드블록 1개, 한 줄에 값 1개.
> 금지 키워드·게이트 수치·편집 범위는 `harness/rules.json`에 있다.

### allowed-hex
```
#F5F4F7
#E8E7ED
#C9C7D4
#9491A7
#5C5872
#2E2B3F
#EDE9F9
#C9BFF0
#8B7ED8
#5C4FB8
#FCE8EF
#F2B8CC
#E07399
#E2F3F0
#A3D9D1
#F2C4CE
#E8D5F5
#C5D8F7
#C5EDE0
#EEEAF5
#E5EEF0
#FFFFFF
```

### allowed-rgba
```
rgba(255,255,255,0.72)
rgba(255,255,255,0.45)
rgba(255,255,255,0.70)
rgba(255,255,255,0.55)
rgba(255,255,255,0.8)
```

### allowed-radius
```
6px
12px
20px
32px
50%
```

### allowed-font-size
```
26px
20px
16px
14px
12px
11px
```

### allowed-font-weight
```
400
500
600
700
800
```

### allowed-blur
```
8px
12px
20px
```

### allowed-spacing
```
0
4px
8px
12px
16px
20px
24px
32px
```

### allowed-box-shadow
```
inset
```

### frame
```
390x844
```

### component-rules
```
card | backgroundColor = rgba(255, 255, 255, 0.72) | backdropFilter = blur(12px) | borderTopColor = rgba(255, 255, 255, 0.7) | borderTopLeftRadius = 20px | paddingTop = 16px | paddingLeft = 20px
button | backgroundImage ~ linear-gradient | color = #FFFFFF | fontSize = 14px | fontWeight = 600 | borderTopLeftRadius = 20px | paddingTop = 16px | paddingLeft = 24px
badge | borderTopLeftRadius = 6px | fontSize = 11px | fontWeight = 600
bottom-nav | backgroundColor = rgba(255, 255, 255, 0.55) | backdropFilter = blur(20px) | borderTopColor = rgba(255, 255, 255, 0.7)
input | backgroundColor = #F5F4F7 | borderTopColor = #C9C7D4 | borderTopLeftRadius = 12px
```

### component-detect
```
card | backgroundColor = rgba(255, 255, 255, 0.72) | backdropFilter ~ blur
bottom-nav | backgroundColor = rgba(255, 255, 255, 0.55) | backdropFilter ~ blur
button | tag = button
badge | borderTopLeftRadius = 6px | fontSize = 11px
input | tag ~ input
```
