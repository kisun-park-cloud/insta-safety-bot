"""전체 자동화: 수집 → 생성 → 검수(불합격 시 재작성) → 제작 → 업로드 → 기록."""
import argparse
import datetime as dt
import json
import os
import shutil
from pathlib import Path

import yaml

from .collect import collect
from .generate import generate
from .review import review, feedback_text
from .render import render_images
from .upload import publish_carousel
from .notify import notify

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history.json"
PUBLIC = ROOT / "docs" / "media"      # GitHub Pages 공개 폴더


def load_history():
    return json.loads(HISTORY.read_text()) if HISTORY.exists() else []


def run(category: str | None = None, dry_run: bool = True):
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    category = category or cfg["schedule"][today.weekday()]
    history = load_history()
    stamp = today.strftime("%Y%m%d_%H%M")
    work = ROOT / "output" / stamp

    # 1) 수집
    research = collect(cfg, category, [h["topic"] for h in history])
    # 2)~3) 생성 + 검수 반복
    feedback, rv, post = "", None, None
    for attempt in range(1, cfg["review"]["max_attempts"] + 1):
        post = generate(cfg, category, research, feedback)
        rv = review(cfg, post, research)
        print(f"[검수 {attempt}회차] 점수 {rv.score} / 합격 {rv.passed}")
        if rv.passed:
            break
        feedback = feedback_text(rv)

    work.mkdir(parents=True, exist_ok=True)
    record = {"date": stamp, "category": category, "topic": research.topic,
              "score": rv.score, "passed": rv.passed,
              "review": rv.model_dump(), "post": post.model_dump(), "research": research.model_dump()}
    (work / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))

    if not rv.passed and cfg["review"]["hold_on_fail"]:
        hold = ROOT / "data" / "hold" / stamp
        shutil.copytree(work, hold, dirs_exist_ok=True)
        notify(f"⛔ 검수 불합격으로 게시 보류: {research.topic} (점수 {rv.score})\n{feedback_text(rv)[:1500]}")
        return record

    # 4) 제작
    images = render_images(cfg, post, work)
    caption = post.caption.strip() + "\n\n" + " ".join(post.hashtags[:30])

    # 5) 업로드
    if dry_run:
        notify(f"🧪 [DRY RUN] 제작 완료(미게시): {post.title} / 점수 {rv.score} / {work}")
        record["media_id"] = None
    else:
        dest = PUBLIC / stamp
        dest.mkdir(parents=True, exist_ok=True)
        for f in images:
            shutil.copy(f, dest / f.name)
        publish_files_publicly(dest)
        base = f"{os.environ['PUBLIC_BASE_URL'].rstrip('/')}/media/{stamp}"
        mid = publish_carousel([f"{base}/{p.name}" for p in images], caption)
        record["media_id"] = mid
        notify(f"✅ 게시 완료: {post.title} (점수 {rv.score}, media_id {mid})")

    history.append({k: record[k] for k in ("date", "category", "topic", "score", "passed")}
                   | {"media_id": record["media_id"]})
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2))
    return record


def publish_files_publicly(dest: Path):
    """GitHub Actions에서 실행 시: docs/media 를 커밋·푸시하여 GitHub Pages로 공개하고 반영을 기다림."""
    if os.getenv("GITHUB_ACTIONS") != "true":
        return
    import subprocess, time, requests
    subprocess.run(["git", "add", str(dest)], check=True)
    subprocess.run(["git", "commit", "-m", f"media: {dest.name}"], check=True)
    subprocess.run(["git", "push"], check=True)
    url = f"{os.environ['PUBLIC_BASE_URL'].rstrip('/')}/media/{dest.name}/card_01.jpg"
    for _ in range(60):  # Pages 배포 대기 (최대 10분)
        if requests.head(url, timeout=10).status_code == 200:
            return
        time.sleep(10)
    raise TimeoutError("GitHub Pages 반영 대기 초과")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", choices=["electrical_knowledge", "electrical_safety",
                                           "industrial_safety", "accident_case"])
    ap.add_argument("--publish", action="store_true", help="실제 게시 (기본은 DRY RUN)")
    a = ap.parse_args()
    dry = not a.publish or os.getenv("DRY_RUN", "true").lower() == "true"
    run(a.category, dry_run=dry)
