"""4단계: 카드뉴스 제작 — 카드를 웹페이지(HTML/CSS)로 디자인한 뒤 브라우저로 화면을 찍어 JPG로 저장.
- 크기 1080×1350 (4:5), 총 9장 = 표지 1 + 본문 7 + 참고자료 1
- 같은 폴더에 index.html(미리보기 웹페이지)도 생성"""
import html
import os
from pathlib import Path

from .models import Post
from . import illust

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1350

CSS = """
@font-face { font-family: 'NotoKR'; src: url('__FONT__') format('truetype'); font-weight: 100 900; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #ddd; font-family: 'NotoKR', sans-serif; word-break: keep-all; }
.card { width: 1080px; height: 1350px; position: relative; overflow: hidden;
  background: radial-gradient(circle at 88% 8%, var(--tint) 0 190px, transparent 191px),
              radial-gradient(circle at 6% 96%, var(--tint2) 0 150px, transparent 151px),
              var(--bg);
  padding: 84px 84px 0; display: flex; flex-direction: column; color: var(--ink); }
.card::before { content: ''; position: absolute; inset: 0;
  background-image: radial-gradient(var(--dot) 2.2px, transparent 2.6px); background-size: 34px 34px; opacity: .55; }
.card > * { position: relative; }
.label { align-self: flex-start; display: inline-flex; align-items: center; justify-content: center;
  height: 68px; padding: 0 34px; border-radius: 34px; background: var(--accent);
  font-size: 34px; font-weight: 800; line-height: 1; color: var(--ink); letter-spacing: -0.5px;
  box-shadow: 0 6px 0 var(--accent-dark); }
.title { margin-top: 38px; font-size: 64px; font-weight: 900; line-height: 1.22; letter-spacing: -1.5px; }
.title .hl { background: linear-gradient(transparent 62%, var(--accent) 62%); }
.panel { margin-top: 34px; height: 520px; border-radius: 44px; background: var(--panel);
  border: 5px solid var(--ink); box-shadow: 0 12px 0 var(--ink); overflow: hidden;
  display: flex; align-items: center; justify-content: center; }
.panel svg { width: 900px; height: 480px; }
.points { margin-top: 48px; display: flex; flex-direction: column; gap: 22px; }
.pt { display: flex; align-items: flex-start; gap: 20px; font-size: 42px; font-weight: 600; line-height: 1.32; letter-spacing: -0.5px; }
.num { flex: none; width: 54px; height: 54px; border-radius: 50%; background: var(--ink); color: #fff;
  font-size: 28px; font-weight: 800; display: flex; align-items: center; justify-content: center; margin-top: 1px; }
.foot { position: absolute; left: 84px; right: 84px; bottom: 62px; display: flex; justify-content: space-between; align-items: center;
  font-size: 30px; font-weight: 700; color: var(--sub); }
.dots { display: flex; gap: 10px; }
.dots i { width: 14px; height: 14px; border-radius: 7px; background: var(--dotoff); display: block; }
.dots i.on { width: 40px; background: var(--ink); }
/* 표지 */
.cover .title { font-size: 86px; margin-top: 46px; }
.cover .sub { margin-top: 22px; font-size: 42px; font-weight: 700; color: var(--sub); line-height: 1.35; }
.cover .panel { height: 540px; margin-top: 40px; }
.cover .panel svg { width: 960px; height: 512px; }
.swipe { margin-top: 36px; align-self: flex-end; font-size: 34px; font-weight: 800; background: var(--ink); color: #fff;
  padding: 16px 32px; border-radius: 40px; }
/* 참고자료 */
.refs { margin-top: 44px; background: #fff; border: 5px solid var(--ink); border-radius: 40px; box-shadow: 0 12px 0 var(--ink);
  padding: 44px 48px; display: flex; flex-direction: column; gap: 30px; }
.ref b { display: block; font-size: 34px; font-weight: 800; }
.ref span { display: block; margin-top: 6px; font-size: 30px; font-weight: 500; color: #475569; line-height: 1.4; }
.law { margin-top: 36px; font-size: 32px; font-weight: 700; line-height: 1.45; }
.disc { margin-top: 30px; font-size: 26px; font-weight: 500; color: var(--sub); line-height: 1.5; }
"""

THEME = {  # 밝고 귀여운 파스텔 테마
    "--bg": "#FFF8E6", "--tint": "#FFE8A3", "--tint2": "#CDEFFF", "--dot": "#F3DFA8",
    "--ink": "#22304A", "--sub": "#6B7A90", "--accent": "#FFD43B", "--accent-dark": "#E8B500",
    "--panel": "#E3F5FF", "--dotoff": "#E6D9B8",
}


def _esc(s):
    return html.escape(s, quote=True)


def _dots(page, total):
    return '<div class="dots">' + "".join(f'<i class="{"on" if i == page else ""}"></i>' for i in range(1, total + 1)) + "</div>"


def _foot(cfg, page, total):
    return f'<div class="foot"><span>{_esc(cfg["account"]["handle"])}</span>{_dots(page, total)}</div>'


def _svg(svg):
    return svg if svg and not illust.validate(svg) else ""


def _title(text):
    # 쉼표·가운뎃점 앞부분을 형광펜 강조
    for sep in (",", "·", " "):
        if sep in text:
            a, b = text.split(sep, 1)
            return f'<span class="hl">{_esc(a)}</span>{_esc(sep)}{_esc(b)}'
    return f'<span class="hl">{_esc(text)}</span>'


def build_cards(cfg, post: Post) -> list[str]:
    label = _esc(cfg["categories"][post.category]["label"])
    slides = post.slides[:7]
    total = len(slides) + 2
    cards = [f'''<section class="card cover"><div class="label">{label}</div>
<h1 class="title">{_title(post.title)}</h1><p class="sub">{_esc(post.subtitle)}</p>
<div class="panel">{_svg(post.cover_svg)}</div><div class="swipe">넘겨서 보기 →</div>{_foot(cfg, 1, total)}</section>''']
    for i, s in enumerate(slides, start=2):
        pts = "".join(f'<div class="pt"><span class="num">{k}</span><span>{_esc(b)}</span></div>'
                      for k, b in enumerate(s.body[:3], start=1))
        cards.append(f'''<section class="card"><div class="label">{label}</div>
<h2 class="title">{_esc(s.heading)}</h2><div class="panel">{_svg(s.illustration_svg)}</div>
<div class="points">{pts}</div>{_foot(cfg, i, total)}</section>''')
    refs = "".join(f'<div class="ref"><b>{_esc(x.publisher)}</b><span>{_esc(x.title)}</span></div>' for x in post.sources[:4])
    law = f'<p class="law">📘 {_esc(" · ".join(post.legal_refs[:3]))}</p>' if post.legal_refs else ""
    cards.append(f'''<section class="card"><div class="label">{label}</div>
<h2 class="title"><span class="hl">참고자료</span></h2><div class="refs">{refs}</div>{law}
<p class="disc">{_esc(cfg["account"]["disclaimer"])}</p>{_foot(cfg, total, total)}</section>''')
    return cards


def _page(cards, font_uri):
    style = ":root{" + ";".join(f"{k}:{v}" for k, v in THEME.items()) + "}" + CSS.replace("__FONT__", font_uri)
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{style}</style></head><body>{"".join(cards)}</body></html>'


def render_images(cfg, post: Post, out_dir: Path) -> list[Path]:
    from playwright.sync_api import sync_playwright
    out_dir.mkdir(parents=True, exist_ok=True)
    font = (ROOT / cfg["render"]["font"]).resolve()
    cards = build_cards(cfg, post)
    tmp = out_dir / "_cards.html"
    tmp.write_text(_page(cards, font.as_uri()), encoding="utf-8")
    paths = []
    with sync_playwright() as p:
        exe = os.getenv("CHROMIUM_PATH")
        browser = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(tmp.resolve().as_uri())
        page.evaluate("document.fonts.ready")
        for i, el in enumerate(page.query_selector_all("section.card"), start=1):
            path = out_dir / f"card_{i:02d}.jpg"
            el.screenshot(path=str(path), type="jpeg", quality=93)
            paths.append(path)
        browser.close()
    tmp.unlink()
    _gallery(cfg, post, paths, out_dir)
    return paths


def _gallery(cfg, post, paths, out_dir):
    """미리보기 웹페이지(index.html): GitHub Pages 에서 /media/날짜/ 로 열람."""
    imgs = "".join(f'<img src="{p.name}" alt="{i}장" loading="lazy">' for i, p in enumerate(paths, 1))
    cap = _esc(post.caption + "\n\n" + " ".join(post.hashtags))
    (out_dir / "index.html").write_text(f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{_esc(post.title)}</title>
<style>body{{margin:0;background:#FFF8E6;font-family:sans-serif;color:#22304A}}
main{{max-width:1180px;margin:0 auto;padding:24px 16px}}h1{{font-size:22px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
.g img{{width:100%;aspect-ratio:4/5;border-radius:14px;box-shadow:0 4px 14px #0002}}
pre{{white-space:pre-wrap;background:#fff;padding:16px;border-radius:12px;font-size:14px;line-height:1.6}}</style></head>
<body><main><h1>{_esc(post.title)} — {len(paths)}장 (4:5)</h1><div class="g">{imgs}</div>
<h2>캡션</h2><pre>{cap}</pre></main></body></html>''', encoding="utf-8")
