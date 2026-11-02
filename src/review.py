"""3단계: 검수 — ①규칙 기반 자동점검 ②별도 AI 검수관의 사실·법령·표현 점검."""
import re
import requests
from .llm import ask_json
from .models import Post, Research, Review, Issue

SYSTEM = """너는 공공기관 홍보물 검수관이다. 작성자와 독립적으로 엄격하게 검토한다.
점검 항목:
A. 사실 정확성: 원고의 모든 수치·주장이 조사자료에 근거하는가 (근거 없으면 critical)
B. 법령 인용: 조문 번호·명칭이 조사자료와 일치하는가, 폐지·개정 의심 표현은 없는가
C. 기술 정확성: 전기·안전 기술 내용이 위험한 오해를 줄 소지가 없는가 (잘못된 작업방법 안내는 critical)
D. 개인정보·명예: 실명, 업체명, 특정 가능한 현장 정보가 없는가
E. 표현: 과장·공포조장·비하·정치적 표현, 광고성 문구가 없는가
F. 저작권: 출처 표기가 있는가, 타 기관 문구를 길게 그대로 옮기지 않았는가
G. 개인 계정 운영 기준: 운영자는 공무원 개인이다. 특정 기관·부서를 대표하는 듯한 표현, 정부 정책에 대한 찬반·정치적 의견,
   공개되지 않은 행정정보로 보이는 내용, 영리 목적의 홍보·판매 유도가 없는가 (있으면 critical)
critical이 하나라도 있으면 passed=false. 점수는 100점 만점."""


def rule_check(cfg: dict, post: Post) -> list[Issue]:
    issues = []
    text = " ".join([post.title, post.subtitle, post.caption] +
                    [s.heading + " ".join(s.body) for s in post.slides])
    for w in cfg["review"]["banned_words"]:
        if w in text:
            issues.append(Issue(severity="critical", where="본문", problem=f"금칙어 '{w}'", fix="표현 삭제"))
    if len(post.sources) < cfg["review"]["require_sources"]:
        issues.append(Issue(severity="critical", where="출처", problem="출처 부족", fix="출처 추가"))
    if len(post.caption) > 2200:
        issues.append(Issue(severity="critical", where="캡션", problem="2,200자 초과(인스타 한도)", fix="축약"))
    if len(post.hashtags) > 30:
        issues.append(Issue(severity="major", where="해시태그", problem="30개 초과", fix="줄이기"))
    if not 3 <= len(post.slides) <= 9:
        issues.append(Issue(severity="major", where="슬라이드", problem="장수 부적정(표지 포함 최대 10장)", fix="4~7장"))
    if re.search(r"\(주\)|주식회사|㈜", text):
        issues.append(Issue(severity="critical", where="본문", problem="업체명 의심 표현", fix="익명화"))
    if re.search(r"\b01[016789]-?\d{3,4}-?\d{4}\b", text):
        issues.append(Issue(severity="critical", where="본문", problem="전화번호 포함", fix="삭제"))
    for s in post.sources:  # 출처 URL 실제 접속 확인
        try:
            r = requests.get(s.url, timeout=10, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code >= 400:
                issues.append(Issue(severity="major", where="출처", problem=f"URL 접속 불가({r.status_code}): {s.url}", fix="유효 출처로 교체"))
        except requests.RequestException:
            issues.append(Issue(severity="minor", where="출처", problem=f"URL 확인 실패: {s.url}", fix="확인"))
    for s in post.slides:
        if len(s.heading) > 22 or any(len(b) > 50 for b in s.body):
            issues.append(Issue(severity="minor", where=s.heading, problem="글자 수 초과로 카드 가독성 저하", fix="문장 축약"))
    return issues


def ai_review(cfg: dict, post: Post, research: Research) -> Review:
    user = f"""[조사자료]
{research.model_dump_json(indent=2)}

[검수 대상 원고]
{post.model_dump_json(indent=2)}"""
    return ask_json(cfg["model"], SYSTEM, user, Review, effort="high")


def review(cfg: dict, post: Post, research: Research) -> Review:
    rules = rule_check(cfg, post)
    ai = ai_review(cfg, post, research)
    issues = rules + ai.issues
    critical = any(i.severity == "critical" for i in issues)
    penalty = sum({"critical": 30, "major": 10, "minor": 2}[i.severity] for i in rules)
    score = max(0, ai.score - penalty)
    passed = (not critical) and ai.passed and score >= cfg["review"]["min_score"]
    return Review(score=score, passed=passed, issues=issues, summary=ai.summary)


def feedback_text(r: Review) -> str:
    return "\n".join(f"- [{i.severity}] {i.where}: {i.problem} → {i.fix}" for i in r.issues)
