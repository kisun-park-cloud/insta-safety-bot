"""1단계: 자료 수집 — 공신력 있는 도메인만 웹검색하여 사실·출처 확보."""
import feedparser
from .llm import ask_json
from .models import Research

SYSTEM = """너는 전기·산업안전 분야 자료조사관이다.
- 반드시 web_search 도구로 허용된 공공기관 자료를 찾아 근거를 확보한다.
- 출처에서 직접 확인한 사실만 key_facts에 적는다. 추측·창작 금지.
- 법령 조문은 원문(law.go.kr 등)에서 확인된 경우에만 legal_refs에 적는다.
- 사고사례는 기관이 공개한 사례만 사용하고, 업체명·개인 실명·특정 가능한 현장명은 기록하지 않는다.
- 최근 게시한 주제와 겹치지 않게 새 주제를 고른다."""


def collect(cfg: dict, category: str, recent_topics: list[str]) -> Research:
    cat = cfg["categories"][category]
    rss_items = []
    for url in cfg["sources"].get("rss") or []:
        for e in feedparser.parse(url).entries[:10]:
            rss_items.append(f"- {e.get('title')} ({e.get('link')})")

    user = f"""분야: {cat['label']}
방향: {cat['brief']}
최근 게시 주제(중복 금지): {', '.join(recent_topics[-30:]) or '없음'}
참고 RSS 신착: 
{chr(10).join(rss_items) or '없음'}

인스타그램 카드뉴스 1건 분량의 주제를 하나 정하고 근거 자료를 조사해라. 출처는 2개 이상 확보."""

    tools = [{
        "type": "web_search_20260209",
        "name": "web_search",
        "max_uses": 8,
        "allowed_domains": cfg["sources"]["allowed_domains"],
        "user_location": {"type": "approximate", "country": "KR"},
    }]
    return ask_json(cfg["model"], SYSTEM, user, Research, tools=tools)
