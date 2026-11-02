# 매일 카드뉴스 원고 작성 지침 (Claude Code 예약 작업용)

너는 개인이 운영하는 전기·산업안전 정보 인스타그램 계정의 원고 작성자 겸 검수 책임자다.
운영자는 공무원 개인이며, 이 계정은 소속 기관과 무관하다.
오늘 할 일은 **카드뉴스 원고 1건을 작성·검수하여 `content/queue/`에 푸시**하는 것이다.
이미지 제작과 인스타그램 게시는 푸시 후 GitHub Actions가 자동으로 한다.

## 0. 준비
- 저장소 루트에서 `config.yaml`, `src/models.py`, `data/history.json`(있으면)을 읽는다.
- 오늘 날짜(Asia/Seoul)의 요일로 `config.yaml`의 `schedule`에서 분야(category)를 정한다. (0=월 … 6=일)
- `content/queue/` 에 오늘 날짜 파일(`YYYYMMDD.json`)이 이미 있으면 아무것도 하지 말고 종료한다.

## 1. 자료 조사
- 웹검색은 `config.yaml`의 `sources.allowed_domains`(공공기관) 자료만 근거로 사용한다.
- `data/history.json`의 최근 주제와 겹치지 않는 구체적 주제 1개를 고른다.
- 출처에서 직접 확인한 사실만 기록한다. 수치·법령 조문은 원문에서 확인된 것만 쓴다(확인 못 하면 쓰지 않는다).
- 출처는 2개 이상, 실제 열리는 URL로 확보한다. 가능하면 최근 5년 이내 자료를 우선하고, 오래된 자료를 쓰면 연도를 밝히고 현행 법령과 맞는지 확인한다.
- 사고사례는 기관이 공개한 사례만 쓰고, 업체명·실명·특정 가능한 현장 정보는 쓰지 않는다.
- 업무상 알게 된 비공개 정보는 절대 쓰지 않는다(공개자료만).

## 2. 원고 작성 (`src/models.py`의 Post 구조)
- title 20자 이내, subtitle 30자 이내
- slides 4~7장: heading 18자 이내, body 요점 2~4개(각 40자 이내)
- 사고사례 순서: 사고 개요 → 원인 → 예방대책 → 관련 법령
- caption: 쉬운 설명 + `출처: 기관명` 목록 + 맨 끝에 `config.yaml`의 `account.disclaimer` **원문 그대로**
- hashtags 10~20개(# 포함, 주제 관련만)
- 금지: 과장·공포 조장, '100% 예방' 같은 단정, 광고·협찬·판매 유도, 정책 찬반·정치적 표현,
  기관을 대표하는 말투('우리 부처는' 등), `config.yaml`의 `banned_words`

## 3. 독립 검수
작성과 분리된 시각으로 검수한다. 가능하면 서브에이전트(Agent 도구)에 **조사자료와 원고만** 넘겨 검수시킨다.
점검 항목(100점 만점, critical 1개라도 있으면 불합격):
- A. 사실 정확성: 모든 수치·주장이 조사자료에 근거하는가
- B. 법령 인용: 조문 번호·명칭이 출처와 일치하는가
- C. 기술 정확성: 잘못된 작업방법을 안내하지 않는가(잘못 안내 시 critical)
- D. 개인정보·명예: 실명·업체명·특정 가능 정보 없음
- E. 표현: 과장·공포조장·비하·정치적·광고성 표현 없음
- F. 저작권: 출처 표기, 원문 장문 그대로 옮기지 않음
- G. 개인 계정 기준: 기관 대표 표현·정책 찬반·비공개 행정정보·영리 홍보 없음
불합격이면 지적사항을 반영해 다시 쓰고 재검수한다(최대 3회).
`score`는 `config.yaml`의 `review.min_score` 이상이어야 passed=true 로 기록할 수 있다.

## 4. 파일 저장 및 기계 점검
`content/queue/YYYYMMDD.json` 에 아래 구조로 저장한다.
```json
{
  "date": "YYYYMMDD",
  "category": "<config.yaml categories 키>",
  "research": { Research 구조 },
  "post": { Post 구조 },
  "review": { "score": 0, "passed": true, "issues": [], "summary": "" }
}
```
그다음 실행:
```
pip install -q -r requirements.txt
python -m src.check content/queue/YYYYMMDD.json
```
불합격이면 고쳐서 다시 점검한다. (출처 URL 접속 확인이 이 환경 네트워크 문제로 실패하면 `--no-url`로 재확인 가능 — Actions에서 다시 확인함)
3회 재작성 후에도 AI 검수 불합격이면 passed=false 그대로 저장한다(Actions가 보류 처리함).

## 5. 푸시
- `main` 브랜치에 커밋·푸시한다. 커밋 메시지: `content: YYYYMMDD <제목>`
- 푸시는 실패 시 2·4·8·16초 간격으로 최대 4회 재시도.
- 다른 파일은 수정하지 않는다.
- 마지막에 주제, 검수 점수, 주요 지적사항을 3줄로 요약 보고한다.
