#!/usr/bin/env python3
"""Glowlog 디자인 하네스 판정 스크립트.

디자인 허용값 원본: design.md `## 판정 규칙 (기계용)`
운영 수치·금지 키워드·편집 범위 원본: harness/rules.json
(값을 이 파일에 하드코딩하지 않는다. 게이트 설명: harness/gates.md)

사용법:
  python3 harness/scripts/judge.py {G1|G2|G3|CHOICE|G4|S5} --run runs/<YYYYMMDD>-screen<N> [--adhoc | --dry]

결과는 <run>/05-report.json 에 게이트별로 기록한다.
종료 코드: 통과 0 / 실패 1 / 사용 오류 2
"""
import argparse
import fnmatch
import hashlib
import html as html_lib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------- 규칙 로드

RULE_SECTION = '## 판정 규칙 (기계용)'


def load_rules(root):
    design_path = os.path.join(root, 'design.md')
    H = json.load(open(os.path.join(root, 'harness', 'rules.json'), encoding='utf-8'))
    text = open(design_path, encoding='utf-8').read()
    i = text.find(RULE_SECTION)
    if i < 0:
        raise SystemExit(f'{design_path}에 "{RULE_SECTION}" 섹션이 없음')
    raw = {}
    for m in re.finditer(r'^### ([\w-]+)\s*\n```\n(.*?)```', text[i:], re.M | re.S):
        raw[m.group(1)] = [l.strip() for l in m.group(2).splitlines() if l.strip()]
    def parse_component_lines(lines):
        parsed = {}
        for line in lines:
            name, *conds = [c.strip() for c in line.split('|')]
            parsed[name] = [re.match(r'(\w+)\s*(=|~)\s*(.+)', c).groups() for c in conds]
        return parsed
    components = parse_component_lines(raw.get('component-rules', []))
    component_detect = parse_component_lines(raw.get('component-detect', []))
    return {
        'hex': {expand_hex(h.lstrip('#')) for h in raw['allowed-hex']},
        'rgba': [parse_rgb_args(re.search(r'\((.*)\)', v).group(1)) for v in raw['allowed-rgba']],
        'radius': {norm_len(v) for v in raw['allowed-radius']},
        'font-size': {norm_len(v) for v in raw['allowed-font-size']},
        'font-weight': set(raw['allowed-font-weight']),
        'blur': {norm_len(v) for v in raw['allowed-blur']},
        'spacing': {norm_len(v) for v in raw['allowed-spacing']},
        'box-shadow': set(raw['allowed-box-shadow']),
        'frame': tuple(raw['frame'][0].split('x')),
        'token-names': load_token_names(text[:i]) | {f'component/{c}' for c in components},
        'token-values': load_token_values(text[:i]),
        'effects': load_effects(text[:i]),
        'gradients': load_gradients(text[:i]),
        'text-styles': load_text_styles(text[:i]),
        'components': components,
        'component-detect': component_detect,
        'keywords': H['keywords']['forbidden'],
        'keyword-exceptions': H['keywords']['exceptions'],
        'skip-prefix': H['keywords']['skip_line_prefix'],
        'H': H,
    }


def load_token_names(text):
    """design.md 표의 첫 칸(`bg/card`, `radius/lg` …) + Effects 소제목(`effect/frosted-glass-card` …)."""
    names = set()
    for line in text.splitlines():
        if line.startswith('|'):
            cell = line.strip('|').split('|')[0].strip()
            if re.fullmatch(r'[A-Za-z]+(/[A-Za-z0-9-]+)+', cell):
                names.add(cell)
    m = re.search(r'^## Effects.*?$(.*?)^## ', text, re.M | re.S)
    if m:
        for heading in re.findall(r'^### (.+)$', m.group(1), re.M):
            names.add('effect/' + re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-'))
    return names


def load_token_values(text):
    """design.md 표의 `토큰 | 값` 쌍. 렌더 판정에서 data-token 이 가리키는 값과 실제 계산값을 비교한다."""
    values = {}
    for line in text.splitlines():
        if line.startswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) >= 2 and re.fullmatch(r'[A-Za-z]+(/[A-Za-z0-9-]+)+', cells[0]):
                values[cells[0]] = cells[1]
    return values


def load_effects(text):
    """Effects 소제목별 css 블록 → 렌더 판정용 특징(backdrop blur, 배경색, 그라디언트 첫 색, inset)."""
    effects = {}
    m = re.search(r'^## Effects.*?$(.*?)^## ', text, re.M | re.S)
    if not m:
        return effects
    for heading, css in re.findall(r'^### (.+?)$.*?```css\n(.*?)```', m.group(1), re.M | re.S):
        name = 'effect/' + re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
        sig = []
        for prop, value in parse_decls(css):
            vl = value.lower()
            if prop == 'backdrop-filter':
                sig.append(('backdropFilter', vl.replace(' ', '')))
            elif prop == 'background' and 'gradient' in vl:
                first = re.search(r'#[0-9a-f]{3,8}|rgba?\([^)]*\)', vl)
                if first:
                    sig.append(('gradient', first.group(0)))
            elif prop == 'background':
                sig.append(('backgroundColor', vl))
            elif prop == 'box-shadow' and 'inset' in vl:
                sig.append(('inset', 'inset'))
        effects[name] = sig
    return effects


def norm_gradient(v):
    return re.sub(r'\s+', '', v.lower())


def gradient_calls(value):
    """값 안의 linear-gradient(...) 호출을 괄호 짝을 맞춰 꺼낸다."""
    calls, i = [], 0
    while (j := value.lower().find('linear-gradient(', i)) >= 0:
        depth, k = 0, j
        while k < len(value):
            depth += (value[k] == '(') - (value[k] == ')')
            k += 1
            if depth == 0 and value[k - 1] == ')':
                break
        calls.append(value[j:k])
        i = k
    return calls


def load_gradients(text):
    """Effects 코드블록에 정의된 그라디언트 — 화면의 그라디언트는 이 중 하나와 각도·색 순서까지 같아야 한다."""
    m = re.search(r'^## Effects.*?$(.*?)^## ', text, re.M | re.S)
    return {norm_gradient(g) for css in re.findall(r'```css\n(.*?)```', m.group(1), re.S) for g in gradient_calls(css)} if m else set()


def load_text_styles(text):
    """Text Styles 표: (이름, size px, weight, line-height 비율, letter-spacing px)."""
    m = re.search(r'^### Text Styles.*?$(.*?)^## ', text, re.M | re.S)
    styles = []
    for line in (m.group(1).splitlines() if m else []):
        cells = [c.strip() for c in line.strip('|').split('|')]
        if line.startswith('|') and len(cells) >= 5 and re.fullmatch(r'\d+px', cells[1]):
            styles.append((cells[0], float(cells[1][:-2]), cells[2], float(cells[3].rstrip('%')) / 100, float(cells[4])))
    return styles


# ---------------------------------------------------------------- 값 정규화

def expand_hex(h):
    h = h.upper()
    return ''.join(c * 2 for c in h) if len(h) in (3, 4) else h


def norm_len(v):
    v = v.strip().lower()
    return '0' if re.fullmatch(r'0(\.0+)?(px|%|rem|em)?', v) else v


def parse_rgb_args(args):
    return tuple(float(x.rstrip('%')) for x in re.split(r'[,\s/]+', args.strip()) if x)


NAMED_COLORS = set('''
aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown
burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue darkcyan
darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet
deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro
ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki
lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan lightgoldenrodyellow
lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue lightslategray
lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine
mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen mediumturquoise
mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive olivedrab
orange orangered orchid palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru
pink plum powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown
seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan
teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen
'''.split())
NO_COLOR_PROPS = {'font-family', 'font', 'content', 'grid-template-areas'}

SPACING_PROPS = re.compile(r'^(padding|margin)(-(top|right|bottom|left|inline|block)(-(start|end))?)?$|^(row-|column-|grid-)?gap$')
RADIUS_PROPS = re.compile(r'^border(-(top|bottom|start|end)-(left|right|start|end))?-radius$')
TOKEN_PROPS = re.compile(r'^(color|background(-color|-image)?|border(-(top|right|bottom|left))?(-color)?|fill|stroke|font-size|font|.*radius)$')


# ---------------------------------------------------------------- CSS 파싱

def split_top(s, sep):
    parts, depth, cur = [], 0, ''
    for ch in s:
        depth += (ch == '(') - (ch == ')')
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def parse_decls(block):
    decls = []
    for part in split_top(block, ';'):
        if ':' in part:
            prop, value = part.split(':', 1)
            value = re.sub(r'\s*!important\s*$', '', value.strip(), flags=re.I)
            decls.append((prop.strip().lower(), value))
    return decls


def parse_css(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    return [(sel.strip(), body) for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css)]


# ---------------------------------------------------------------- 위반 기록

def add(out, rule, where, detail):
    out.append({'rule': rule, 'where': where, 'detail': detail})


def check_values(decls, where, R, out):
    """hex·rgba·radius·font-size·font-weight·blur·spacing·box-shadow·position"""
    for prop, value in decls:
        vl = value.lower()
        for h in re.findall(r'#([0-9a-fA-F]{3,8})\b', value):
            if expand_hex(h) not in R['hex']:
                add(out, 'hex', where, f'{prop}: #{h}')
        for fn, args in re.findall(r'\b(rgba?)\(([^)]*)\)', vl):
            try:
                nums = parse_rgb_args(args)
            except ValueError:
                add(out, 'rgba', where, f'{prop}: {fn}({args}) 해석 불가')
                continue
            if len(nums) == 3 or (len(nums) == 4 and nums[3] == 1):
                hx = ''.join(f'{int(n):02X}' for n in nums[:3])
                if hx not in R['hex']:
                    add(out, 'hex', where, f'{prop}: {fn}({args})')
            elif not any(len(a) == len(nums) and all(abs(x - y) < 1e-9 for x, y in zip(a, nums)) for a in R['rgba']):
                add(out, 'rgba', where, f'{prop}: {fn}({args})')
        if prop not in NO_COLOR_PROPS:
            for word in re.findall(r'(?<![\w-])[a-z]+(?![\w-])', vl):
                if word in NAMED_COLORS:
                    add(out, 'hex', where, f'{prop}: 색 이름 "{word}"')
        if RADIUS_PROPS.match(prop):
            for t in re.split(r'[\s/]+', value.strip()):
                if norm_len(t) not in R['radius']:
                    add(out, 'radius', where, f'{prop}: {t}')
        if prop == 'font-size' and norm_len(value) not in R['font-size']:
            add(out, 'font-size', where, f'{prop}: {value}')
        if prop == 'font-weight':
            w = {'normal': '400', 'bold': '700'}.get(vl.strip(), vl.strip())
            if w not in R['font-weight']:
                add(out, 'font-weight', where, f'{prop}: {value}')
        if prop == 'font':
            m = re.search(r'(?<![\w.])(\d+(?:\.\d+)?(?:px|rem|em|%))', vl)
            if m and norm_len(m.group(1)) not in R['font-size']:
                add(out, 'font-size', where, f'font: {value}')
            for w in re.findall(r'(?<![\w.])([1-9]00)(?![\w.%])', vl):
                if w not in R['font-weight']:
                    add(out, 'font-weight', where, f'font: {value}')
        for b in re.findall(r'\bblur\(([^)]*)\)', vl):
            if norm_len(b) not in R['blur']:
                add(out, 'blur', where, f'{prop}: blur({b})')
        for g in gradient_calls(value):
            if norm_gradient(g) not in R['gradients']:
                add(out, 'gradient', where, f'{prop}: {g} (design.md Effects 그라디언트와 각도·색 순서 불일치)')
        if 'drop-shadow(' in vl:
            add(out, 'box-shadow', where, f'{prop}: drop-shadow 금지')
        if SPACING_PROPS.match(prop):
            for t in value.split():
                if norm_len(t) not in R['spacing']:
                    add(out, 'spacing', where, f'{prop}: {t}')
        if prop == 'box-shadow' and vl.strip() != 'none':
            for part in split_top(vl, ','):
                if not any(re.search(rf'\b{re.escape(a)}\b', part) for a in R['box-shadow']):
                    add(out, 'box-shadow', where, f'{prop}: {part}')
        if prop == 'text-shadow' and vl.strip() != 'none':
            add(out, 'box-shadow', where, f'{prop}: 텍스트 그림자 금지')
        if prop == 'position' and vl.strip() in ('absolute', 'fixed'):
            add(out, 'position', where, f'position: {vl.strip()} (Auto Layout 위반)')


# ---------------------------------------------------------------- 금지 키워드

def keyword_hits(text, R):
    """금지 키워드 일치 목록 [(키워드, 걸린 문장 문맥)]. 부정문도 자동으로 봐주지 않는다 —
    오탐은 본인이 rules.json keywords.exceptions 에 '구절'로 추가한다 (예: "로그인 없이")."""
    masked = text
    for ex in R['keyword-exceptions']:
        masked = masked.replace(ex, ' ' * len(ex))
    hits = []
    for kw in R['keywords']:
        pattern = rf'\b{re.escape(kw)}\b' if re.fullmatch(r'[A-Za-z ]+', kw) else re.escape(kw)
        for m in re.finditer(pattern, masked, re.I):
            end = text.find('\n', m.end())
            a = max(text.rfind('\n', 0, m.start()) + 1, m.start() - 15)
            b = min(len(text) if end < 0 else end, m.end() + 15)
            hits.append((kw, re.sub(r'\s+', ' ', text[a:b]).strip()))
    return hits


def check_doc_keywords(path, R, out):
    """md 문서: rules.json skip_line_prefix(`제외:`)로 시작하는 줄과 URL은 검사하지 않는다."""
    for no, line in enumerate(open(path, encoding='utf-8').read().splitlines(), 1):
        if re.match(r'^\s*(?:[-*]\s+)?' + re.escape(R['skip-prefix']), line):
            continue
        for kw, ctx in keyword_hits(re.sub(r'https?://\S+', ' ', line), R):
            add(out, 'keyword', f'{rel(path)}:{no}', f'"{kw}" — …{ctx}…')


# ---------------------------------------------------------------- HTML

VISIBLE_ATTRS = ('alt', 'placeholder', 'aria-label', 'title', 'value')
SKIP_TEXT = {'script', 'style', 'head', 'template'}


class Doc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.elements, self.css, self.links, self.text = [], [], [], []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        self.elements.append({'tag': tag, 'attrs': a, 'line': self.getpos()[0]})
        if tag == 'link' and 'stylesheet' in a.get('rel', '').lower():
            self.links.append(a.get('href', ''))
        if not any(t in SKIP_TEXT for t in self.stack):
            self.text += [a[k] for k in VISIBLE_ATTRS if a.get(k)]
        if tag in SKIP_TEXT:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if self.stack and self.stack[-1] == 'style':
            self.css.append(data)
        elif not any(t in SKIP_TEXT for t in self.stack):
            self.text.append(data)


def check_html(path, R, require_tokens):
    """G3(require_tokens=False)·S5(True) 공통 HTML 판정."""
    out = []
    doc = Doc()
    doc.feed(open(path, encoding='utf-8').read())
    sources = [(rel(path), ''.join(doc.css))]
    for href in doc.links:
        if re.match(r'^[a-z]+:|^//', href):
            continue
        p = os.path.normpath(os.path.join(os.path.dirname(path), href))
        if os.path.exists(p):
            sources.append((rel(p), open(p, encoding='utf-8').read()))
    rules = []
    for src, css in sources:
        for sel, body in parse_css(css):
            decls = parse_decls(body)
            rules.append((sel, decls))
            check_values(decls, f'{src} {sel}', R, out)
    for el in doc.elements:
        where = f'{rel(path)}:{el["line"]} <{el["tag"]}>'
        if el['attrs'].get('style'):
            check_values(parse_decls(el['attrs']['style']), where, R, out)
        for attr in ('fill', 'stroke', 'stop-color', 'color'):
            if el['attrs'].get(attr):
                check_values([(attr, el['attrs'][attr])], where, R, out)

    # 프레임: body 의 width·height
    body = {}
    for sel, decls in rules:
        if 'body' in [s.strip() for s in sel.split(',')]:
            body.update(dict(decls))
    body_el = next((e for e in doc.elements if e['tag'] == 'body'), None)
    if body_el and body_el['attrs'].get('style'):
        body.update(dict(parse_decls(body_el['attrs']['style'])))
    w, h = R['frame']
    if norm_len(body.get('width', '')) != f'{w}px' or norm_len(body.get('height', '')) != f'{h}px':
        add(out, 'frame', rel(path), f'body width/height = {body.get("width")}/{body.get("height")} (기대 {w}px/{h}px)')

    # data-token: 색·radius·font-size 를 쓰는 클래스(선택자 마지막 부분 기준) 또는 인라인 스타일
    if require_tokens:
        token_classes = set()
        for sel, decls in rules:
            if any(TOKEN_PROPS.match(p) for p, _ in decls):
                for s in sel.split(','):
                    last = re.split(r'[\s>+~]+', s.strip())[-1]
                    token_classes.update(re.findall(r'\.([A-Za-z0-9_-]+)', last))
        for el in doc.elements:
            a = el['attrs']
            where = f'{rel(path)}:{el["line"]} <{el["tag"]} class="{a.get("class", "")}">'
            needs = bool(set(a.get('class', '').split()) & token_classes) or \
                any(TOKEN_PROPS.match(p) for p, _ in parse_decls(a.get('style', '')))
            if 'data-token' not in a:
                if needs:
                    add(out, 'data-token', where, 'data-token 누락')
                continue
            for t in a['data-token'].split():
                if t not in R['token-names']:
                    add(out, 'token-name', where, f'design.md에 없는 토큰 "{t}"')

    for kw, ctx in keyword_hits('\n'.join(doc.text), R):
        add(out, 'keyword', rel(path), f'"{kw}" — …{ctx}…')
    return out


SRC_ATTRS = {'script': 'src', 'img': 'src', 'source': 'src', 'iframe': 'src', 'video': 'src', 'audio': 'src', 'embed': 'src', 'object': 'data'}


def check_self_contained(path):
    """G3 시안은 파일 1개로 Figma(html.to.design)에 가져올 수 있어야 한다 — 외부 CSS·스크립트·이미지·url() 참조 금지 (data: 만 허용)."""
    out = []
    doc = Doc()
    doc.feed(open(path, encoding='utf-8').read())
    for el in doc.elements:
        a, where = el['attrs'], f'{rel(path)}:{el["line"]} <{el["tag"]}>'
        if el['tag'] == 'link' and 'stylesheet' in a.get('rel', '').lower():
            add(out, 'self-contained', where, f'외부 CSS href="{a.get("href", "")}"')
        attr = SRC_ATTRS.get(el['tag'])
        if attr and a.get(attr) and not a[attr].startswith('data:'):
            add(out, 'self-contained', where, f'외부 참조 {attr}="{a[attr]}"')
        for u in re.findall(r'url\(\s*[\'"]?([^\'")]+)', a.get('style', '')):
            if not u.startswith('data:'):
                add(out, 'self-contained', where, f'외부 참조 url({u})')
    css = ''.join(doc.css)
    for m in re.finditer(r'@import[^;]*;', css):
        add(out, 'self-contained', f'{rel(path)} <style>', f'외부 CSS {m.group(0)}')
    for u in re.findall(r'url\(\s*[\'"]?([^\'")]+)', css):
        if not u.startswith('data:'):
            add(out, 'self-contained', f'{rel(path)} <style>', f'외부 참조 url({u})')
    return out


# ---------------------------------------------------------------- 렌더 판정 (헤드리스 Chrome 계산값)

PROBE = """<script>
addEventListener('load', () => {
  const P = ['marginTop','marginRight','marginBottom','marginLeft','paddingTop','paddingRight','paddingBottom','paddingLeft',
    'rowGap','columnGap','fontSize','fontWeight','color','backgroundColor','backgroundImage',
    'borderTopWidth','borderRightWidth','borderBottomWidth','borderLeftWidth',
    'borderTopColor','borderRightColor','borderBottomColor','borderLeftColor',
    'borderTopLeftRadius','borderTopRightRadius','borderBottomRightRadius','borderBottomLeftRadius',
    'backdropFilter','boxShadow','lineHeight','letterSpacing','textTransform'];
  const b = document.body, r = b.getBoundingClientRect();
  const out = { body: [r.width, r.height], content: [b.scrollWidth, b.scrollHeight], els: [] };
  for (const el of [b, ...b.querySelectorAll('*')]) {
    const tag = el.tagName.toLowerCase();
    if (['script', 'style', 'template'].includes(tag)) continue;
    const c = getComputedStyle(el), s = {};
    for (const p of P) s[p] = c[p];
    const text = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    out.els.push({ tag, cls: el.getAttribute('class') || '', token: el.getAttribute('data-token'), text, s });
  }
  const pre = document.createElement('pre');
  pre.id = 'glowlog-probe';
  pre.textContent = JSON.stringify(out);
  b.appendChild(pre);
});
</script>"""


def find_chrome(cfg):
    """환경변수 → 후보 경로 순서로 Chrome 을 찾는다 (동료 컴퓨터마다 설치 위치가 다름)."""
    for p in [os.environ.get(cfg['chrome_env'], '')] + cfg['chrome_candidates']:
        p = os.path.expanduser(p)
        if p and os.path.exists(p):
            return p
    return None


def render_probe(path, R):
    """HTML 을 헤드리스 Chrome 으로 그려 요소별 계산 스타일을 받는다. 실패 시 (None, 이유)."""
    cfg = R['H']['render']
    chrome = find_chrome(cfg)
    if not chrome:
        return None, f'Chrome 없음 (환경변수 {cfg["chrome_env"]} 또는 rules.json render.chrome_candidates 확인)'
    w, h = R['frame']
    src = open(path, encoding='utf-8').read()
    base = f'<base href="file://{os.path.dirname(os.path.abspath(path))}/">'
    if re.search(r'<head[^>]*>', src, re.I):
        src = re.sub(r'<head[^>]*>', lambda m: m.group(0) + base, src, count=1, flags=re.I)
    else:
        src = base + src
    src = src.replace('</body>', PROBE + '</body>') if '</body>' in src else src + PROBE
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        page, dump = os.path.join(td, 'probe.html'), os.path.join(td, 'dump.html')
        open(page, 'w', encoding='utf-8').write(src)
        with open(dump, 'w') as fo:
            proc = subprocess.Popen(
                [chrome, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
                 '--hide-scrollbars', f'--user-data-dir={td}/profile', f'--window-size={w},{h}', '--dump-dom', 'file://' + page],
                stdout=fo, stderr=subprocess.DEVNULL, start_new_session=True)
            deadline = time.time() + cfg['timeout_sec']
            data = ''
            # Chrome 은 dump 출력 후에도 종료하지 않는 경우가 있어, 출력이 끝나면 직접 종료한다
            while time.time() < deadline:
                time.sleep(0.2)
                data = open(dump, encoding='utf-8', errors='replace').read()
                if 'glowlog-probe' in data and '</html>' in data or proc.poll() is not None:
                    break
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except (PermissionError, ProcessLookupError):
                    proc.kill()          # 그룹 종료가 거부되면 본 프로세스만 종료
                proc.wait()
            data = open(dump, encoding='utf-8', errors='replace').read()
    m = re.search(r'<pre id="glowlog-probe">(.*?)</pre>', data, re.S)
    if not m:
        return None, f'계산값을 받지 못함 ({cfg["timeout_sec"]}초 제한)'
    return json.loads(html_lib.unescape(m.group(1))), None


def colors_in(value):
    return [parse_rgb_args(a) for a in re.findall(r'rgba?\(([^)]*)\)', value)]


def color_allowed(c, R):
    if len(c) == 4 and c[3] == 0:
        return True
    if len(c) == 3 or c[3] == 1:
        return ''.join(f'{int(round(n)):02X}' for n in c[:3]) in R['hex']
    return any(len(a) == 4 and all(abs(x - y) < 0.005 for x, y in zip(a, c)) for a in R['rgba'])


def same_color(a, b):
    a, b = tuple(a) + (1,) * (4 - len(a)), tuple(b) + (1,) * (4 - len(b))
    return all(abs(x - y) < 0.005 for x, y in zip(a, b))


def css_color(v):
    v = v.strip().lower()
    if v.startswith('#'):
        h = expand_hex(v[1:])
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r'rgba?\(([^)]*)\)', v)
    return parse_rgb_args(m.group(1)) if m else None


SIDES = ('Top', 'Right', 'Bottom', 'Left')
CORNERS = ('TopLeft', 'TopRight', 'BottomRight', 'BottomLeft')


def token_matches(token, s, R):
    """data-token 이 가리키는 design.md 값이 이 요소의 계산값 어딘가에 실제로 쓰였는가."""
    if token.startswith('component/'):
        return True                      # 조합 검사는 component-rule 에서 한다
    if token.startswith('effect/'):
        for kind, want in R['effects'].get(token, []):
            if kind == 'backdropFilter' and s['backdropFilter'].replace(' ', '') != want:
                return False
            if kind == 'gradient' and not any(same_color(c, css_color(want)) for c in colors_in(s['backgroundImage'])):
                return False
            if kind == 'backgroundColor' and not same_color(colors_in(s['backgroundColor'])[0], css_color(want)):
                return False
            if kind == 'inset' and 'inset' not in s['boxShadow']:
                return False
        return True
    want = R['token-values'].get(token)
    if want is None or token.startswith('lineHeight/'):
        return True                      # 이름 검사는 정적 판정(token-name)에서 한다
    if css_color(want):
        props = ['color', 'backgroundColor'] + [f'border{d}Color' for d in SIDES if s[f'border{d}Width'] != '0px']
        return any(colors_in(s[p]) and same_color(colors_in(s[p])[0], css_color(want)) for p in props)
    if token.startswith('fontSize/'):
        return s['fontSize'] == want
    if token.startswith('fontWeight/'):
        return s['fontWeight'] == want
    if token.startswith('radius/'):
        return any(s[f'border{c}Radius'] == want for c in CORNERS)
    if token.startswith('space/'):
        return want in [s[k] for k in s if k.startswith(('margin', 'padding')) or k.endswith('Gap')]
    return True


def text_style_matches(style, s):
    _, size, weight, lh, ls = style
    if s['fontSize'] != f'{size:g}px' or s['fontWeight'] != weight:
        return False
    if s['lineHeight'] == 'normal' or abs(float(s['lineHeight'][:-2]) - size * lh) > 0.05:
        return False
    actual_ls = 0.0 if s['letterSpacing'] == 'normal' else float(s['letterSpacing'][:-2])
    return abs(actual_ls - ls) < 0.01


def component_cond(actual, op, want):
    if op == '~':
        return want.lower() in actual.lower()
    if css_color(want) and colors_in(actual):
        return same_color(colors_in(actual)[0], css_color(want))
    return actual.strip() == want.strip()


def check_render(path, R, require_tokens):
    """브라우저 계산값 기준 판정: 기본 margin·상속 색처럼 파일에 적히지 않은 값까지 잡는다."""
    out = []
    probe, err = render_probe(path, R)
    if probe is None:
        add(out, 'render-unavailable', rel(path), err)
        return out
    w, h = (int(x) for x in R['frame'])
    bw, bh = probe['body']
    cw, ch = probe['content']
    if round(bw) != w or round(bh) != h or cw > w or ch > h:
        add(out, 'render-frame', rel(path), f'body {bw:g}×{bh:g}, 내용 {cw}×{ch} (기대 {w}×{h} 안)')
    for i, el in enumerate(probe['els']):
        s = el['s']
        where = f'{rel(path)} #{i} <{el["tag"]} class="{el["cls"]}">'
        bad = []
        if el['text']:
            bad += [f'color {s["color"]}'] if not all(color_allowed(c, R) for c in colors_in(s['color'])) else []
        for p in ['backgroundColor', 'backgroundImage', 'boxShadow'] + [f'border{d}Color' for d in SIDES if s[f'border{d}Width'] != '0px']:
            bad += [f'{p} {s[p]}' for c in colors_in(s[p]) if not color_allowed(c, R)][:1]
        if bad:
            add(out, 'render-color', where, ', '.join(bad))
        if el['text'] and norm_len(s['fontSize']) not in R['font-size']:
            add(out, 'render-font-size', where, s['fontSize'])
        if el['text'] and s['fontWeight'] not in R['font-weight']:
            add(out, 'render-font-weight', where, s['fontWeight'])
        spacing = [f'{k} {s[k]}' for k in s if (k.startswith(('margin', 'padding')) or k.endswith('Gap'))
                   and s[k] != 'normal' and norm_len(s[k]) not in R['spacing']]
        if spacing:
            add(out, 'render-spacing', where, ', '.join(spacing))
        radius = [f'{c} {s[f"border{c}Radius"]}' for c in CORNERS
                  if norm_len(s[f'border{c}Radius']) != '0' and not all(norm_len(v) in R['radius'] for v in s[f'border{c}Radius'].split())]
        if radius:
            add(out, 'render-radius', where, ', '.join(radius))
        for b in re.findall(r'blur\(([^)]*)\)', s['backdropFilter']):
            if norm_len(b) not in R['blur']:
                add(out, 'render-blur', where, f'blur({b})')
        if s['boxShadow'] != 'none' and not all('inset' in part for part in split_top(s['boxShadow'], ',')):
            add(out, 'render-box-shadow', where, s['boxShadow'])
        for c in colors_in(s['backgroundColor']):
            if same_color(c, (255, 255, 255, 1)):
                add(out, 'white-bg', where, '순수 흰색 배경 (반투명 처리 필요)')
        if i == 0:
            want = dict(R['effects'].get('effect/app-background', [])).get('gradient')
            if want and not any(same_color(c, css_color(want)) for c in colors_in(s['backgroundImage'])):
                add(out, 'app-background', where, f'body 배경이 App Background 그라디언트가 아님: {s["backgroundImage"]}')
        if el['text'] and not any(text_style_matches(st, s) for st in R['text-styles']):
            add(out, 'text-style', where, f'{s["fontSize"]} / {s["fontWeight"]} / line-height {s["lineHeight"]} / letter-spacing {s["letterSpacing"]} — Text Styles 7개 중 일치 없음')
        tokens = (el['token'] or '').split()
        if require_tokens:               # 역방향: 컴포넌트 특징이 있는데 component/* 표시가 없으면 조합 검사를 피한 것
            facts = dict(s, tag=el['tag'])
            for name, conds in R['component-detect'].items():
                if f'component/{name}' not in tokens and all(component_cond(facts.get(p, ''), op, want) for p, op, want in conds):
                    add(out, 'component-missing', where, f'{name} 특징({" · ".join(f"{p} {op} {w}" for p, op, w in conds)})이 있는데 data-token에 component/{name} 없음')
        for t in tokens:
            if t.startswith('component/') and t[len('component/'):] in R['components']:
                miss = [f'{p} {op} {want} (실제 {s.get(p)})' for p, op, want in R['components'][t[len('component/'):]]
                        if not component_cond(s.get(p, ''), op, want)]
                if miss:
                    add(out, 'component-rule', where, f'{t}: ' + ', '.join(miss))
        if require_tokens and el['token']:
            for t in el['token'].split():
                if t in R['token-names'] and not token_matches(t, s, R):
                    add(out, 'token-value', where, f'"{t}" = {R["token-values"].get(t, "효과")} 인데 실제 계산값에 없음')
    return out


# ---------------------------------------------------------------- G1·G2

def check_refs(path, R):
    g = R['H']['G1']
    out = []
    sections = re.split(r'^## ', open(path, encoding='utf-8').read(), flags=re.M)[1:]
    if len(sections) < g['min_refs']:
        add(out, 'refs-count', rel(path), f'레퍼런스 {len(sections)}개 (최소 {g["min_refs"]}개)')
    for sec in sections:
        title = sec.splitlines()[0].strip()
        urls = re.findall(re.escape(g['url_field']) + r'\s*(\S+)', sec)
        if len(urls) != 1 or g['url_domain'] not in urls[0]:
            add(out, 'refs-url', f'{rel(path)} ## {title}', f'{g["url_domain"]} {g["url_field"]} {len(urls)}개 (정확히 1개)')
        if not re.search(r'^\s*(?:[-*]\s+)?' + re.escape(g['point_field']) + r'\s*\S', sec, re.M):
            add(out, 'refs-point', f'{rel(path)} ## {title}', f'"{g["point_field"]}" 줄 없음')
    check_doc_keywords(path, R, out)
    return out


def prd_bullet_count(prd_path, screen):
    text = open(prd_path, encoding='utf-8').read()
    m = re.search(rf'^\*\*화면 {screen} —.*?$(.*?)(?=^\*\*화면 \d|^---|\Z)', text, re.M | re.S)
    if not m:
        raise SystemExit(f'PRD.md에서 화면 {screen} 기능 요구사항을 찾지 못함')
    return len(re.findall(r'^- ', m.group(1), re.M))


def check_spec(path, prd_path, screen, R):
    out = []
    expected = prd_bullet_count(prd_path, screen)
    items = len(re.findall(r'^\s*[-*] \[[ xX]\] ', open(path, encoding='utf-8').read(), re.M))
    if items != expected:
        add(out, 'spec-count', rel(path), f'체크리스트 {items}개 ≠ PRD 화면 {screen} 요구사항 {expected}개')
    check_doc_keywords(path, R, out)
    return out


# ---------------------------------------------------------------- G4: 공용 컴포넌트 추가-only

def check_components(before_path, after_path):
    out = []
    if not os.path.exists(before_path):
        add(out, 'component', rel(before_path), '스냅샷 없음')
        return out
    before = parse_css(open(before_path, encoding='utf-8').read())
    after_text = open(after_path, encoding='utf-8').read() if os.path.exists(after_path) else ''
    after = {}
    for sel, body in parse_css(after_text):
        after.setdefault(sel, []).append(body.strip())
    for sel, body in before:
        if sel not in after:
            add(out, 'component', rel(after_path), f'"{sel}" 삭제됨')
        elif body.strip() not in after[sel]:
            add(out, 'component', rel(after_path), f'"{sel}" 정의 변경됨')
    return out


# ---------------------------------------------------------------- 편집 범위 (rules.json scope)

STAGES = ['S1', 'S2', 'S3', 'S4', 'S5']


def list_files(root, H):
    skip_dirs, skip_files = set(H['snapshot_skip']['dirs']), set(H['snapshot_skip']['files'])
    files = {}
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x not in skip_dirs]
        for n in names:
            p = os.path.join(d, n)
            r = os.path.relpath(p, root)
            if n in skip_files or r in skip_files:
                continue
            files[r] = datetime.fromtimestamp(os.path.getmtime(p)).isoformat()
    return files


def check_scope(root, run_dir, R):
    H = R['H']
    out = []
    state = json.load(open(os.path.join(run_dir, 'state.json'), encoding='utf-8'))
    snaps = state.get('snapshots', {})
    stages = [s for s in STAGES if s in snaps]
    if not stages:
        add(out, 'scope', rel(run_dir), 'state.json에 snapshots 없음')
        return out
    current = list_files(root, H)
    for i, s in enumerate(stages):
        a = snaps[s]
        b = snaps[stages[i + 1]] if i + 1 < len(stages) else current
        allowed = H['scope'][H['stages'][s]['agent']] + H['always_allowed']
        for p in sorted(set(a) | set(b)):
            if a.get(p) != b.get(p) and not any(fnmatch.fnmatch(p, g) for g in allowed):
                add(out, 'scope', p, f'{s} 단계 편집 범위 밖 수정')
    return out


# ---------------------------------------------------------------- 실행

def rel(p):
    try:
        return os.path.relpath(p, ROOT)
    except ValueError:
        return p


# ---------------------------------------------------------------- 사람 승인: 선택값 + 시안 해시

def draft_hashes(run_dir, H):
    n = H['choice']['hash_len']
    hashes = []
    for name in H['G3']['drafts']:
        p = os.path.join(run_dir, name)
        hashes.append(hashlib.sha256(open(p, 'rb').read()).hexdigest()[:n] if os.path.exists(p) else 'missing')
    return hashes


def check_choice(run_dir, H):
    """첫 줄 = a|b, 그리고 기록된 시안 해시 = 지금 시안 해시 (승인 후 시안이 바뀌면 무효)."""
    c = H['choice']
    out = []
    path = os.path.join(run_dir, c['file'])
    lines = open(path, encoding='utf-8').read().splitlines() if os.path.exists(path) else []
    first = lines[0].strip() if lines else ''
    if first not in c['allowed']:
        add(out, 'choice', c['file'], f'첫 줄 "{first}" ({" 또는 ".join(c["allowed"])} 필요)')
        return out
    recorded = next((l[len(c['hash_field']):] for l in lines if l.startswith(c['hash_field'])), None)
    if recorded is None:
        add(out, 'choice-stale', c['file'], f'"{c["hash_field"]}" 줄 없음 — choose.py로 기록해야 함')
        return out
    recorded = [h.strip() for h in recorded.split('/')]
    current = draft_hashes(run_dir, H)
    if recorded != current:
        add(out, 'choice-stale', c['file'], f'승인 시 시안 {" / ".join(recorded)} ≠ 현재 시안 {" / ".join(current)} — 다시 선택 필요')
    return out


def screen_of(run_dir, H):
    m = re.search(H['run_dir']['screen_regex'], os.path.basename(os.path.normpath(run_dir)))
    return int(m.group(1)) if m else None


def run_gate(gate, run_dir, root, R=None):
    R = R or load_rules(root)
    H = R['H']
    screen = screen_of(run_dir, H)
    f = lambda name: os.path.join(run_dir, name)
    out = []
    if gate == 'G1':
        if not os.path.exists(f(H['G1']['file'])):
            add(out, 'missing', H['G1']['file'], '파일 없음')
        else:
            out = check_refs(f(H['G1']['file']), R)
    elif gate == 'G2':
        if not os.path.exists(f(H['G2']['file'])):
            add(out, 'missing', H['G2']['file'], '파일 없음')
        else:
            out = check_spec(f(H['G2']['file']), os.path.join(root, H['G2']['prd']), screen, R)
    elif gate == 'G3':
        for name in H['G3']['drafts']:
            if os.path.exists(f(name)):
                out += check_html(f(name), R, require_tokens=False)
                out += check_render(f(name), R, require_tokens=False)
                if H['G3'].get('self_contained'):
                    out += check_self_contained(f(name))
            else:
                add(out, 'missing', name, '파일 없음')
    elif gate == 'CHOICE':
        out = check_choice(run_dir, H)
    elif gate == 'G4':
        out = check_components(f(H['G4']['snapshot']), os.path.join(root, H['G4']['components']))
    elif gate == 'S5':
        screen_path = os.path.join(root, H['S5']['screen'].replace('{N}', str(screen)))
        if os.path.exists(screen_path):
            out = check_html(screen_path, R, require_tokens=True)
            out += check_render(screen_path, R, require_tokens=True)
        else:
            add(out, 'missing', rel(screen_path), '파일 없음')
        out += check_scope(root, run_dir, R)
        out += check_choice(run_dir, H)
        out += check_history(root, run_dir, H)
    return out, input_hashes(gate, run_dir, root, H)


# ---------------------------------------------------------------- 리포트 지문·판정 이력

def file_hash(path, n=12):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:n] if os.path.exists(path) else 'missing'


def input_hashes(gate, run_dir, root, H):
    """게이트가 판정한 입력 파일들의 지문. 이후 파일이 바뀌면 그 PASS는 무효(report-stale)."""
    f = lambda name: os.path.join(run_dir, name)
    drafts = [f(d) for d in H['G3']['drafts']]
    screen = H['S5']['screen'].replace('{N}', str(screen_of(run_dir, H)))
    paths = {
        'G1': [f(H['G1']['file'])],
        'G2': [f(H['G2']['file']), os.path.join(root, H['G2']['prd'])],
        'G3': drafts,
        'CHOICE': [f(H['choice']['file'])] + drafts,
        'G4': [f(H['G4']['snapshot']), os.path.join(root, H['G4']['components'])],
        'S5': [os.path.join(root, screen), os.path.join(root, H['G4']['components']), f(H['choice']['file'])] + drafts,
    }[gate]
    return {os.path.relpath(p, root): file_hash(p) for p in paths}


def check_history(root, run_dir, H):
    """S5 전용: ① 앞 게이트 PASS가 지금 파일과 같은지 ② 게이트 순서 ③ state.json retries = 이력의 FAIL 수."""
    out = []
    path = os.path.join(run_dir, H['report'])
    data = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    order = H['gate_order']
    for g in order[:-1]:
        rec = data.get(g)
        if not rec or not rec['pass']:
            add(out, 'gate-not-passed', g, '마지막 판정이 PASS가 아님' if rec else '판정 기록 없음')
            continue
        now = input_hashes(g, run_dir, root, H)
        changed = [p for p in now if rec.get('inputs', {}).get(p) != now[p]]
        if changed:
            add(out, 'report-stale', g, f'PASS 이후 바뀐 입력: {", ".join(changed)}')
    passed = set()
    history = [e for e in data.get('history', []) if not e.get('adhoc')]
    for no, e in enumerate(history, 1):
        k = order.index(e['gate'])
        if k > 0 and order[k - 1] not in passed:
            add(out, 'order', f'history #{no}', f'{order[k - 1]} PASS 전에 {e["gate"]} 판정')
        if e['pass']:
            passed.add(e['gate'])
    state_path = os.path.join(run_dir, 'state.json')
    retries = json.load(open(state_path, encoding='utf-8')).get('retries', {}) if os.path.exists(state_path) else {}
    fails = {}
    for e in history:
        if not e['pass']:
            fails[e['gate']] = fails.get(e['gate'], 0) + 1
    for key in H['retries']:
        if key == 'reject':          # 사람의 시안 반려는 게이트 이력에 남지 않는다
            continue
        expected = sum(fails.get(g, 0) for g in key.split('_'))
        if retries.get(key, 0) != expected:
            add(out, 'retries', 'state.json', f'retries.{key} = {retries.get(key, 0)} ≠ 이력 FAIL {expected}회')
    return out


def write_report(run_dir, gate, out, inputs, name, adhoc=False):
    path = os.path.join(run_dir, name)
    data = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    by_rule = {}
    for v in out:
        by_rule[v['rule']] = by_rule.get(v['rule'], 0) + 1
    now = datetime.now().isoformat(timespec='seconds')
    data[gate] = {
        'pass': not out,
        'count': len(out),
        'by_rule': by_rule,
        'checked_at': now,
        'inputs': inputs,
        'violations': out,
    }
    entry = {'gate': gate, 'pass': not out, 'count': len(out), 'checked_at': now}
    if adhoc:
        entry['adhoc'] = True
    data.setdefault('history', []).append(entry)
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description='Glowlog 하네스 판정')
    ap.add_argument('gate', choices=['G1', 'G2', 'G3', 'CHOICE', 'G4', 'S5'])
    ap.add_argument('--run', required=True, help='runs/<YYYYMMDD>-screen<N>')
    ap.add_argument('--root', default=ROOT)
    ap.add_argument('--dry', action='store_true', help='판정만 하고 리포트·이력에 쓰지 않음 (재판정·테스트용)')
    ap.add_argument('--adhoc', action='store_true', help='"판정만 돌려줘" — 이력에 남기되 순서·재시도 대조에서 제외')
    args = ap.parse_args()
    run_dir = os.path.abspath(args.run)
    if not os.path.isdir(run_dir):
        print(f'실행 폴더 없음: {args.run}', file=sys.stderr)
        sys.exit(2)
    out, inputs = run_gate(args.gate, run_dir, os.path.abspath(args.root))
    if not args.dry:
        write_report(run_dir, args.gate, out, inputs, load_rules(os.path.abspath(args.root))['H']['report'], args.adhoc)
    print(f'{args.gate} {"PASS" if not out else f"FAIL {len(out)}건"}{" (dry)" if args.dry else ""}')
    for v in out[:5]:
        print(f'  [{v["rule"]}] {v["where"]} — {v["detail"]}')
    sys.exit(0 if not out else 1)


if __name__ == '__main__':
    main()
