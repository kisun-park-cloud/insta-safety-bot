"""4단계: 카드뉴스 이미지 제작."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .models import Post
from . import illust


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


def _card(cfg, label, heading, body, page, total, cover=False, svg=""):
    r = cfg["render"]; c = r["colors"]; W, H = r["width"], r["height"]
    img = Image.new("RGB", (W, H), c["bg"]); d = ImageDraw.Draw(img)
    bold, reg = r["font"], r["font_regular"]
    pad = 90
    illus = illust.to_image(svg, 900, 480)
    # 상단 분류 라벨
    lf = _font(bold, 38)
    d.rounded_rectangle((pad, pad, pad + 40 + d.textlength(label, font=lf), pad + 70), radius=35, fill=c["accent"])
    d.text((pad + 20, pad + 12), label, font=lf, fill=c["bg"])

    if illus is None:  # 그림 없는 카드(참고자료 등): 기존 배치
        y = 380 if cover else 260
        hf = _font(bold, 92 if cover else 68)
    else:              # 그림 카드: 제목 → 그림 → 요점
        y = 200
        hf = _font(bold, 80 if cover else 62)
    for ln in _wrap(d, heading, hf, W - pad * 2):
        d.text((pad, y), ln, font=hf, fill=c["text"]); y += hf.size + 20
    d.rectangle((pad, y + 14, pad + 120, y + 24), fill=c["accent"]); y += 50

    if illus is not None:
        panel = (pad, y, W - pad, y + 480)
        d.rounded_rectangle(panel, radius=36, fill=c.get("panel", "#1E293B"))
        img.paste(illus, (pad, y), illus)
        y += 480 + 40

    bf = _font(reg, (46 if cover else 40) if illus is not None else (52 if cover else 46))
    gap = 12 if illus is not None else 16
    for b in body:
        lines = _wrap(d, b, bf, W - pad * 2 - (0 if cover else 50))
        if not cover:
            d.ellipse((pad, y + bf.size // 2 - 4, pad + 18, y + bf.size // 2 + 14), fill=c["accent"])
        for ln in lines:
            d.text((pad + (0 if cover else 50), y), ln, font=bf, fill=c["sub"] if cover else c["text"])
            y += bf.size + gap
        y += 18 if illus is not None else 28
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
    cards = [_card(cfg, label, post.title, [post.subtitle], 1, total, cover=True, svg=post.cover_svg)]
    for i, s in enumerate(post.slides, start=2):
        cards.append(_card(cfg, label, s.heading, s.body, i, total, svg=s.illustration_svg))
    src = ["출처"] + [f"{s.publisher} · {s.title}" for s in post.sources[:4]]
    cards.append(_card(cfg, label, "참고자료", src[1:] + ([" / ".join(post.legal_refs[:3])] if post.legal_refs else []), total, total))
    paths = []
    for i, im in enumerate(cards, start=1):
        p = out_dir / f"card_{i:02d}.jpg"
        im.save(p, "JPEG", quality=92)
        paths.append(p)
    return paths
