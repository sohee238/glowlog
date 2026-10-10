#!/usr/bin/env python3
"""pass.html 에서 위반 1건씩만 넣은 실패 샘플을 만들고 expected.json 의 HTML 항목을 갱신한다.

pass.html 을 고친 뒤 실행: python3 harness/tests/build_fixtures.py
(디렉터리 샘플 fail-component·fail-scope·*-history 는 건드리지 않는다)
"""
import json
import os

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')

# 이름: (찾을 문자열, 바꿀 문자열, [추가 치환], 정적 기대 규칙, 렌더 기대 규칙)
VARIANTS = {
    'fail-hex':             ('color: #5C5872;', 'color: #333333;', [], 'hex', None),
    'fail-rgba':            ('background: rgba(255,255,255,0.72);', 'background: rgba(255,255,255,0.9);', [], 'rgba', None),
    'fail-radius':          ('border-radius: 20px;', 'border-radius: 16px;', [], 'radius', None),
    'fail-font-size':       ('font-size: 12px;', 'font-size: 13px;', [], 'font-size', None),
    'fail-font-weight':     ('font-size: 16px; font-weight: 700;', 'font-size: 16px; font-weight: 900;', [], 'font-weight', None),
    'fail-blur':            ('blur(12px)', 'blur(24px)', [], 'blur', None),
    'fail-spacing':         ('gap: 8px;', 'gap: 10px;', [], 'spacing', None),
    'fail-box-shadow':      ('box-shadow: inset 0 1px 0', 'box-shadow: 0 4px 12px', [], 'box-shadow', None),
    'fail-frame':           ('width: 390px;', 'width: 375px;', [], 'frame', None),
    'fail-data-token':      (' data-token="text/secondary fontSize/caption"', '', [], 'data-token', None),
    'fail-token-name':      ('data-token="interactive/accent"', 'data-token="accent/pink"', [], 'token-name', None),
    'fail-position':        ('.dot { width: 6px;', '.dot { position: absolute; width: 6px;', [], 'position', None),
    'fail-keyword':         ('>오늘 사용<', '>공유하기<', [], 'keyword', None),
    'fail-gradient':        ('linear-gradient(135deg,', 'linear-gradient(90deg,', [], 'gradient', None),
    'fail-keyword-phrase':  ('>메모: 피드백 없음 · 다음 예정 10월 10일<', '>로그인 없이 바로 기록해요<', [], 'keyword', None),
    # 렌더 전용: 파일 정적 판정은 통과(0)하지만 브라우저 계산값은 위반
    'fail-render-margin':   ('.title { margin: 0; font-size: 26px;', '.title { font-size: 26px;', [], None, 'render-spacing'),
    'fail-render-color':    ('<span class="dot"', '<p class="note" data-token="fontSize/caption">메모 없음</p>\n  <span class="dot"',
                             [('.dot {', '.note { margin: 0; font-size: 12px; font-weight: 400; line-height: 1.5; }\n.dot {')], None, 'render-color'),
    'fail-token-value':     ('background: #E07399;', 'background: #8B7ED8;', [], None, 'token-value'),
    'fail-render-overflow': ('</section>\n</body>', '</section>\n<div class="spacer"></div>\n</body>',
                             [('.dot {', '.spacer { height: 900px; flex-shrink: 0; }\n.dot {')], None, 'render-frame'),
    'fail-white-bg':        ('</section>\n</body>', '</section>\n<div class="panel" data-token="radius/md"></div>\n</body>',
                             [('.dot {', '.panel { height: 8px; background: #FFFFFF; border-radius: 12px; }\n.dot {')], None, 'white-bg'),
    'fail-text-style':      ('font-weight: 400; line-height: 1.5;', 'font-weight: 400; line-height: 1.2;', [], None, 'text-style'),
    'fail-component-rule':  ('padding: 16px 20px;', 'padding: 20px 20px;', [], None, 'component-rule'),
    'fail-component-missing': ('data-token="component/card bg/card', 'data-token="bg/card', [], None, 'component-missing'),
    'fail-app-background':  ('background: linear-gradient(160deg, #EEEAF5 0%, #E8E7ED 50%, #E5EEF0 100%);', 'background: #E8E7ED;', [], None, 'app-background'),
}


def main():
    src = open(os.path.join(FIX, 'pass.html'), encoding='utf-8').read()
    exp_path = os.path.join(FIX, 'expected.json')
    expected = json.load(open(exp_path, encoding='utf-8'))
    expected = {k: v for k, v in expected.items() if not (k.endswith('.html') or k.startswith('render:'))}
    expected['pass.html'] = {'check': 'html', 'count': 0}
    expected['render:pass.html'] = {'check': 'render', 'count': 0}
    for name, (a, b, extra, static_rule, render_rule) in VARIANTS.items():
        assert src.count(a) == 1, (name, a)
        out = src.replace(a, b)
        for x, y in extra:
            assert out.count(x) == 1, (name, x)
            out = out.replace(x, y)
        open(os.path.join(FIX, f'{name}.html'), 'w', encoding='utf-8').write(out.replace('fixture pass', f'fixture {name}'))
        expected[f'{name}.html'] = {'check': 'html', 'count': 1, 'rule': static_rule} if static_rule else {'check': 'html', 'count': 0}
        if render_rule:
            expected[f'render:{name}.html'] = {'check': 'render', 'count': 1, 'rule': render_rule}
    # 같은 파일에 본인이 예외 구절을 추가했다고 가정하면 통과해야 한다
    expected['exc:fail-keyword-phrase.html'] = {'check': 'html', 'count': 0, 'exceptions': ['로그인 없이']}
    with open(exp_path, 'w', encoding='utf-8') as fp:
        json.dump(expected, fp, ensure_ascii=False, indent=2)
    print(f'샘플 {len(VARIANTS)}개 생성, expected.json 항목 {len([k for k in expected if not k.startswith("_")])}개')


if __name__ == '__main__':
    main()
