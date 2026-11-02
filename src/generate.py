"""2단계: 콘텐츠 생성 — 조사 결과만으로 카드뉴스 원고 작성."""
from .llm import ask_json
from .models import Post, Research

SYSTEM = """너는 공공 안전교육 콘텐츠 작가다. 현장 근로자와 일반인이 이해하기 쉽게 쓴다.
원칙:
1. 제공된 조사자료(key_facts, legal_refs, sources)에 있는 내용만 쓴다. 새로운 수치·조문을 만들지 않는다.
2. 사고사례는 '개요 → 원인 → 예방대책 → 관련 법령' 순서. 피해자·업체를 특정하지 않고 희생자를 존중하는 어조.
3. 과장·공포 조장·단정적 효과 표현(100% 예방 등) 금지.
4. 캡션 끝에 '출처: 기관명' 목록과 면책문구를 넣는다.
5. 해시태그는 #전기안전 #산업안전 등 관련 태그만.
6. 개인이 운영하는 정보공유 계정이다. 기관을 대표하는 말투('우리 부처는' 등), 정책 찬반, 광고·판매 유도 문구를 쓰지 않는다."""


def generate(cfg: dict, category: str, research: Research, feedback: str = "") -> Post:
    cat = cfg["categories"][category]
    user = f"""분야: {cat['label']} (형식: 인스타그램 카드뉴스)
계정명: {cfg['account']['name']}
면책문구: {cfg['account']['disclaimer']}

[조사자료]
{research.model_dump_json(indent=2)}

{('[이전 검수 지적사항 — 반드시 반영]' + chr(10) + feedback) if feedback else ''}
category 필드에는 "{category}"를 넣어라."""
    post = ask_json(cfg["model"], SYSTEM, user, Post)
    post.category = category
    return post
