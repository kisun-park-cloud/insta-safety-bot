"""4단계: 카드뉴스 이미지 제작."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .models import Post


def _font(path, size):
    try:
        f = ImageFont.truetype(path, size)
        try:  # 가변폰트(Noto Sans KR [wght])면 굵기 지정
            f.set_variation_by_axes([700 if "Bold" in path else 400])
        except (OSError, AttributeError):
            pass
        return f
    except OSError:  # 폰트 미설치 시 대체
        return ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", size)


def _wrap(draw, text, font, max_w):
    lines, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=font) > max_w:
            lines.append(line)
            line = ch.lstrip()
        else:
            line += ch
    return lines + ([line] if line else [])


def _card(cfg, label, heading, body, page, total, cover=False):
    r = cfg["render"]; c = r["colors"]; W, H = r["width"], r["height"]
    img = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(img)
    bold, reg = r["font"], r["font_regular"]
    pad = 90
    # 상단 분류 라벨
    d.rounded_rectangle((pad, pad, pad + 40 + d.textlength(label, font=_font(bold, 38)), pad + 70),
                        radius=35, fill=c["accent"])
    d.text((pad + 20, pad + 12), label, font=_font(bold, 38), fill=c["bg"])
    y = 380 if cover else 260
    hf = _font(bold, 92 if cover else 68)
    for ln in _wrap(d, heading, hf, W - pad * 2):
        d.text((pad, y), ln, font=hf, fill=c["text"]); y += hf.size + 24
    d.rectangle((pad, y + 24, pad + 120, y + 34), fill=c["accent"]); y += 70
    bf = _font(reg, 52 if cover else 46)
    for b in body:
        lines = _wrap(d, b, bf, W - pad * 2 - (0 if cover else 50))
        if not cover:
            d.ellipse((pad, y + 18, pad + 20, y + 38), fill=c["accent"])
        for ln in lines:
            d.text((pad + (0 if cover else 50), y), ln, font=bf, fill=c["text"] if not cover else c["sub"])
            y += bf.size + 16
        y += 28
    # 하단 계정명·쪽번호
    sf = _font(reg, 34)
    d.text((pad, H - pad - 34), cfg["account"]["handle"], font=sf, fill=c["sub"])
    pg = f"{page}/{total}"
    d.text((W - pad - d.textlength(pg, font=sf), H - pad - 34), pg, font=sf, fill=c["sub"])
    return img


def render_images(cfg, post: Post, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    label = cfg["categories"][post.category]["label"]
    total = len(post.slides) + 2
    cards = [_card(cfg, label, post.title, [post.subtitle], 1, total, cover=True)]
    for i, s in enumerate(post.slides, start=2):
        cards.append(_card(cfg, label, s.heading, s.body, i, total))
    src = ["출처"] + [f"{s.publisher} · {s.title}" for s in post.sources[:4]]
    cards.append(_card(cfg, label, "참고자료", src[1:] + ([" / ".join(post.legal_refs[:3])] if post.legal_refs else []), total, total))
    paths = []
    for i, im in enumerate(cards, start=1):
        p = out_dir / f"card_{i:02d}.jpg"
        im.save(p, "JPEG", quality=92)
        paths.append(p)
    return paths
