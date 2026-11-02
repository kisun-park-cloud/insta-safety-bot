"""이미 제작된 미리보기(docs/media/날짜)를 인스타그램에 게시 (수동 실행용).
사용: python -m src.post_existing 20261102"""
import json
import os
import sys
from pathlib import Path

from .publish_queue import wait_public, HISTORY
from .upload import publish_carousel
from .notify import notify

ROOT = Path(__file__).resolve().parent.parent


def main(date: str):
    f = ROOT / "content/published" / f"{date}.json"
    data = json.loads(f.read_text())
    if data.get("media_id"):
        print("이미 게시됨:", data["media_id"]); return
    post = data["post"]
    imgs = sorted((ROOT / "docs/media" / date).glob("card_*.jpg"))
    if len(imgs) < 2:
        raise SystemExit("카드 이미지가 없음")
    base = f"{os.environ['PUBLIC_BASE_URL'].rstrip('/')}/media/{date}"
    for p in imgs:
        wait_public(f"{base}/{p.name}")
    caption = post["caption"].strip() + "\n\n" + " ".join(post["hashtags"][:30])
    media_id = publish_carousel([f"{base}/{p.name}" for p in imgs], caption)
    data["media_id"], data["status"] = media_id, "published"
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    hist = json.loads(HISTORY.read_text()) if HISTORY.exists() else []
    for h in hist:
        if h.get("date") == date:
            h["status"], h["media_id"] = "published", media_id
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=2))
    notify(f"✅ 수동 게시 완료: {post['title']} (media_id {media_id})")
    print("게시 완료 media_id:", media_id)


if __name__ == "__main__":
    main(sys.argv[1])
