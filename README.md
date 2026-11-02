# 전기·산업안전 인스타그램 자동 운영 시스템 (개인 계정용)

Claude 구독(Claude Code 예약 작업)으로 원고를 쓰고, GitHub Actions가 카드뉴스를 만들어 게시합니다. **Claude API 키·별도 결제 불필요.**

## 1. 처리 흐름

```
[매일 07:47 Claude Code 예약 작업]  prompts/daily.md 지침에 따라
  ① 공공기관 자료 조사 → ② 원고 작성 → ③ 독립 검수(불합격 시 재작성, 최대 3회)
  → content/queue/YYYYMMDD.json 푸시
        ↓ (푸시되면 자동 실행)
[GitHub Actions: 카드뉴스 제작·게시]
  ④ 규칙 검수(금칙어·업체명·면책문구·출처 URL 등) → ⑤ 카드 이미지 제작
  → ⑥ 인스타그램 게시(DRY_RUN=false 일 때만) → ⑦ 이력 기록
```

| 위치 | 내용 |
|---|---|
| `prompts/daily.md` | Claude가 매일 따르는 작성·검수 지침 (수정하면 다음 날부터 반영) |
| `config.yaml` | 요일별 주제, 허용 자료원, 금칙어, 디자인 |
| `content/queue/` | 게시 대기 원고 → 처리 후 `content/published/` 로 이동 |
| `data/hold/` | 검수 불합격으로 보류된 원고 |
| `docs/media/` | 카드 이미지 (시험운영 중에는 미리보기) |
| `data/history.json` | 게시 이력 (주제 중복 방지) |

요일별 주제: 월 전기지식 / 화 전기안전 / 수 산업안전 / 목 사고사례 / 금 전기안전 / 토 산업안전 / 일 사고사례

## 2. 설정

1. **GitHub Pages**: Settings → Pages → `main` 브랜치 `/docs` 폴더
2. **Settings → Secrets and variables → Actions**
   - Secrets: `IG_ACCESS_TOKEN`, (권장) `GH_PAT`, (선택) `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - Variables: `PUBLIC_BASE_URL` = `https://kisun-park-cloud.github.io/insta-safety-bot`, `DRY_RUN` = `true`
3. **인스타그램 토큰**: 크리에이터 계정 → Meta 개발자 앱(Instagram API, Unified login) → 액세스 토큰 생성
   (권한 `instagram_business_basic`, `instagram_business_content_publish`, 페이스북 페이지 불필요)
4. **GH_PAT**: GitHub → Settings → Developer settings → Fine-grained tokens → 이 저장소만, 권한 Secrets: Read and write
   → 매주 인스타 토큰 자동 갱신

## 3. 운영

- 시험운영(`DRY_RUN=true`): 매일 원고·이미지가 만들어져 `docs/media/날짜/`에 저장됨 → GitHub에서 확인
- 품질이 안정되면 `DRY_RUN=false` → 다음 원고부터 실제 게시
- 예약 작업 중지·시간 변경: claude.ai/code 의 예약 작업(Scheduled tasks) 화면
- 원고 수동 재처리: Actions → 카드뉴스 제작·게시 → Run workflow

## 4. 유의사항

- Claude 구독 사용량 한도를 함께 사용 (하루 1건 기준)
- 인스타 토큰 60일 만료 → `GH_PAT` 등록 시 매주 자동 갱신
- 저작권: 공공누리 출처표시 준수, 기관 이미지 미사용(직접 제작 카드만)
- 사고사례: 기관 공개 사례만, 업체·피해자 특정 정보 자동 차단

## 5. 공무원 개인 계정 운영 시 유의사항

- **영리활동 금지·겸직허가**(「국가공무원법」 제64조): 광고·협찬·수익화 시 사전 확인. 광고성 문구는 금칙어로 차단
- **비밀엄수**(제60조): 업무상 알게 된 비공개 정보 사용 금지 — 공공기관 공개자료만 사용
- **정치적 중립**(제65조)·**품위유지**(제63조): 정책 찬반·정치적 표현은 검수에서 불합격
- **기관과의 구분**: 프로필에 "개인 계정, 소속 기관과 무관" 명시, 기관 로고·명칭·직함 사용 자제
