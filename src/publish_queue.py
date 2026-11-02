"""GitHub Actions 전용: content/queue 의 원고 → 규칙검수 → 카드 이미지 제작 → 인스타 게시 → 기록.
원고(JSON)는 Claude Code 예약 작업이 매일 작성해 푸시한다."""
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests

from .check import load_cfg, rule_check, blocking
from .models import Post
from .render import render_images
from .upload import publish_carousel
from .notify import notify

ROOT = Path(__file__).resolve().parent.parent
QUEUE, DONE, HOLD = ROOT / "content/queue", ROOT / "content/published", ROOT / "data/hold"
HISTORY = ROOT / "data/history.json"


def git(*args):
    subprocess.run(["git", *args], check=True, cwd=ROOT)


def wait_public(url):
    for _ in range(60):  # GitHub Pages 반영 대기 (최대 10분)
        try:
            if requests.head(url, timeout=10).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(10)
    raise TimeoutError(f"공개 URL 반영 대기 초과: {url}")


def main():
    cfg = load_cfg()
    dry = os.getenv("DRY_RUN", "true").lower() != "false"
    history = json.loads(HISTORY.read_text()) if HISTORY.exists() else []
    files = sorted(QUEUE.glob("*.json"))
    if not files:
        print("대기 원고 없음")
        return
    for f in files:
        stem = f.stem
        data = json.loads(f.read_text())
        post = Post.model_validate(data["post"])
        ai = data.get("review", {})
        issues = rule_check(cfg, post)
        ai_ok = ai.get("passed") and ai.get("score", 0) >= cfg["review"]["min_score"]
        if blocking(issues) or not ai_ok:
            HOLD.mkdir(parents=True, exist_ok=True)
            data["rule_issues"] = [i.model_dump() for i in issues]
            (HOLD / f.name).write_text(json.dumps(data, ensure_ascii=False, indent=2))
            f.unlink()
            msg = "\n".join(f"- [{i.severity}] {i.problem}" for i in issues) or f"AI 검수 점수 {ai.get('score')}"
            notify(f"⛔ 게시 보류: {post.title}\n{msg}")
            history.append({"date": stem, "category": post.category, "topic": post.title, "status": "hold"})
            continue

        media_dir = ROOT / "docs/media" / stem
        images = render_images(cfg, post, media_dir)
        caption = post.caption.strip() + "\n\n" + " ".join(post.hashtags[:30])
        media_id = None
        if dry:
            status = "dry_run"
            notify(f"🧪 [시험운영] 카드뉴스 제작 완료(미게시): {post.title}\n미리보기: docs/media/{stem}")
        else:
            git("add", str(media_dir))
            git("commit", "-m", f"media: {stem}")
            git("pull", "--rebase", "origin", "main")
            git("push", "origin", "HEAD:main")
            base = f"{os.environ['PUBLIC_BASE_URL'].rstrip('/')}/media/{stem}"
            wait_public(f"{base}/{images[-1].name}")
            media_id = publish_carousel([f"{base}/{p.name}" for p in images], caption)
            status = "published"
            notify(f"✅ 게시 완료: {post.title} (media_id {media_id})")
        data["media_id"], data["status"] = media_id, status
        DONE.mkdir(parents=True, exist_ok=True)
        (DONE / f.name).write_text(json.dumps(data, ensure_ascii=False, indent=2))
        f.unlink()
        history.append({"date": stem, "category": post.category, "topic": post.title,
                        "status": status, "media_id": media_id})
    HISTORY.parent.mkdir(exist_ok=True)
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
