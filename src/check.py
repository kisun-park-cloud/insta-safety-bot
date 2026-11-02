"""규칙 기반 검수 (AI 검수 이후 기계적으로 한 번 더 확인).
사용: python -m src.check content/queue/20261103.json"""
import json
import re
import sys
from pathlib import Path

import requests
import yaml

from .models import Issue, Post
from . import illust

ROOT = Path(__file__).resolve().parent.parent


def load_cfg():
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def rule_check(cfg: dict, post: Post, check_urls: bool = True) -> list[Issue]:
    issues = []
    if post.category not in cfg["categories"]:
        issues.append(Issue(severity="critical", where="category", problem=f"알 수 없는 분류 '{post.category}'", fix="config.yaml categories 키 사용"))
    text = " ".join([post.title, post.subtitle, post.caption] +
                    [s.heading + " " + " ".join(s.body) for s in post.slides])
    for w in cfg["review"]["banned_words"]:
        if w in text:
            issues.append(Issue(severity="critical", where="본문", problem=f"금칙어 '{w}'", fix="표현 삭제"))
    if len(post.sources) < cfg["review"]["require_sources"]:
        issues.append(Issue(severity="critical", where="출처", problem="출처 부족", fix="출처 추가"))
    if cfg["account"]["disclaimer"][:15] not in post.caption:
        issues.append(Issue(severity="critical", where="캡션", problem="면책문구 누락", fix="config.yaml 의 disclaimer 그대로 추가"))
    if len(post.caption) + len(" ".join(post.hashtags)) > 2150:
        issues.append(Issue(severity="critical", where="캡션", problem="캡션+해시태그 2,200자 초과", fix="축약"))
    if len(post.hashtags) > 30:
        issues.append(Issue(severity="critical", where="해시태그", problem="30개 초과", fix="줄이기"))
    if not 3 <= len(post.slides) <= 8:
        issues.append(Issue(severity="critical", where="슬라이드", problem="본문 3~8장이어야 함(표지·출처 포함 최대 10장)", fix="조정"))
    if re.search(r"\(주\)|주식회사|㈜|유한회사", text):
        issues.append(Issue(severity="critical", where="본문", problem="업체명 의심 표현", fix="익명화"))
    if re.search(r"01[016789]-?\d{3,4}-?\d{4}", text):
        issues.append(Issue(severity="critical", where="본문", problem="전화번호 포함", fix="삭제"))
    for s in post.slides:
        if len(s.heading) > 22 or any(len(b) > 40 for b in s.body) or len(s.body) > 3:
            issues.append(Issue(severity="major", where=s.heading, problem="글자 수·줄 수 초과(제목 22자, 요점 3개·각 40자)", fix="축약"))
    svgs = [("표지", post.cover_svg)] + [(s.heading, s.illustration_svg) for s in post.slides]
    for where, svg in svgs:
        if not svg:
            issues.append(Issue(severity="minor", where=where, problem="일러스트 없음", fix="SVG 일러스트 추가"))
        elif (err := illust.validate(svg)):
            issues.append(Issue(severity="major", where=where, problem=f"일러스트 오류: {err}", fix="SVG 수정"))
    if check_urls:
        for s in post.sources:
            try:
                r = requests.get(s.url, timeout=15, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code >= 400:
                    issues.append(Issue(severity="major", where="출처", problem=f"URL 접속 불가({r.status_code}): {s.url}", fix="유효 출처로 교체"))
            except requests.RequestException:
                issues.append(Issue(severity="minor", where="출처", problem=f"URL 확인 실패: {s.url}", fix="확인"))
    return issues


def blocking(issues: list[Issue]) -> bool:
    return any(i.severity in ("critical", "major") for i in issues)


if __name__ == "__main__":
    cfg = load_cfg()
    data = json.loads(Path(sys.argv[1]).read_text())
    post = Post.model_validate(data["post"])
    issues = rule_check(cfg, post, check_urls="--no-url" not in sys.argv)
    for i in issues:
        print(f"[{i.severity}] {i.where}: {i.problem} → {i.fix}")
    print("결과:", "불합격" if blocking(issues) else "합격")
    sys.exit(1 if blocking(issues) else 0)
