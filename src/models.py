"""게시물 데이터 구조 (Claude 구조화 출력 스키마로도 사용)."""
from typing import List, Literal
from pydantic import BaseModel, Field


class Source(BaseModel):
    title: str = Field(description="자료 제목")
    url: str = Field(description="원문 URL")
    publisher: str = Field(description="발행 기관 (예: 한국산업안전보건공단)")


class Research(BaseModel):
    topic: str = Field(description="선정한 구체적 주제")
    key_facts: List[str] = Field(description="출처로 확인된 핵심 사실")
    legal_refs: List[str] = Field(description="출처에서 확인된 법령 조문만 (예: 산업안전보건기준에 관한 규칙 제319조). 확인 못 했으면 빈 배열")
    sources: List[Source]


class Slide(BaseModel):
    heading: str = Field(description="슬라이드 제목, 18자 이내")
    body: List[str] = Field(description="본문 요점 2~4개, 각 40자 이내")
    illustration_svg: str = Field(default="", description="장면 일러스트 SVG (viewBox 0 0 900 480, 글자 없음)")


class Post(BaseModel):
    category: str
    title: str = Field(description="표지 제목, 20자 이내")
    subtitle: str = Field(description="표지 부제, 30자 이내")
    cover_svg: str = Field(default="", description="표지 일러스트 SVG (viewBox 0 0 900 480, 글자 없음)")
    slides: List[Slide] = Field(description="본문 슬라이드 4~7장")
    caption: str = Field(description="인스타그램 본문, 1,500자 이내, 출처 표기 포함")
    hashtags: List[str] = Field(description="해시태그 10~20개, # 포함")
    sources: List[Source]
    legal_refs: List[str]


class Issue(BaseModel):
    severity: Literal["critical", "major", "minor"]
    where: str
    problem: str
    fix: str


class Review(BaseModel):
    score: int = Field(description="0~100 종합 점수")
    passed: bool
    issues: List[Issue]
    summary: str
