"""5단계: 인스타그램 업로드 (Meta 공식 Instagram API).
토큰 종류를 자동 판별한다.
- IGAA... (인스타그램 로그인 토큰)  → graph.instagram.com, 60일 만료(자동 갱신)
- EAA...  (통합 로그인/시스템 사용자 토큰) → graph.facebook.com, 만료 없음
인스타그램 서버가 이미지를 직접 내려받으므로 PUBLIC_BASE_URL 로 공개된 파일이어야 한다."""
import os
import time
import requests

VER = os.getenv("IG_GRAPH_VERSION", "v23.0")


def _is_ig_token():
    return os.environ["IG_ACCESS_TOKEN"].startswith("IG")


def _api():
    host = "graph.instagram.com" if _is_ig_token() else "graph.facebook.com"
    return f"https://{host}/{VER}"


def _token():
    return os.environ["IG_ACCESS_TOKEN"]


def _check(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram API 오류 {r.status_code}: {r.text}")
    return r.json()


def _post(path, **params):
    params["access_token"] = _token()
    return _check(requests.post(f"{_api()}/{path}", data=params, timeout=60))


def _get(path, **params):
    params["access_token"] = _token()
    return _check(requests.get(f"{_api()}/{path}", params=params, timeout=30))


def _safe(fn):
    try:
        return fn()
    except Exception as e:  # 탐색 실패는 다음 방법으로
        print("  (탐색 실패:", str(e)[:200], ")")
        return []


def ig_user_id() -> str:
    """IG_USER_ID 미설정 시 토큰으로 계정 ID 자동 조회."""
    if os.getenv("IG_USER_ID"):
        return os.environ["IG_USER_ID"]
    if _is_ig_token():
        return _get("me", fields="user_id,username")["user_id"]
    # 통합 로그인 토큰: 페이지 → 비즈니스 포트폴리오 순으로 연결된 인스타 계정 탐색
    tries = [
        lambda: [a["instagram_business_account"] for a in _get(
            "me/accounts", fields="instagram_business_account{id,username}").get("data", [])
            if a.get("instagram_business_account")],
        lambda: [ia for b in _get("me/businesses").get("data", [])
                 for edge in ("instagram_accounts", "owned_instagram_accounts")
                 for ia in _safe(lambda: _get(f"{b['id']}/{edge}", fields="id,username").get("data", []))],
    ]
    for t in tries:
        found = _safe(t)
        if found:
            print("찾은 인스타그램 계정:", found)
            return found[0]["id"]
    raise RuntimeError("토큰으로 인스타그램 계정 ID를 찾지 못함 — Secrets 에 IG_USER_ID 를 등록하세요")


def _wait_ready(container_id, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = _get(container_id, fields="status_code")
        if r.get("status_code") == "FINISHED":
            return
        if r.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"미디어 처리 실패: {r}")
        time.sleep(5)
    raise TimeoutError("미디어 처리 시간 초과")


def publish_carousel(image_urls: list[str], caption: str) -> str:
    """카드뉴스(캐러셀) 게시: 이미지별 컨테이너 → 캐러셀 컨테이너 → 게시."""
    ig = ig_user_id()
    children = [_post(f"{ig}/media", image_url=u, is_carousel_item="true")["id"] for u in image_urls[:10]]
    for c in children:
        _wait_ready(c)
    parent = _post(f"{ig}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    _wait_ready(parent)
    return _post(f"{ig}/media_publish", creation_id=parent)["id"]


def refresh_token() -> str | None:
    """IGAA 장기 토큰(60일) 갱신. EAA(시스템 사용자) 토큰은 만료가 없어 None."""
    if not _is_ig_token():
        return None
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": _token()}, timeout=30)
    return _check(r)["access_token"]


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["refresh"]:
        print(refresh_token() or "")
    elif sys.argv[1:] == ["whoami"]:
        kind = "인스타그램 로그인 토큰(IGAA, 60일)" if _is_ig_token() else "통합 로그인 토큰(EAA)"
        print("토큰 종류:", kind, "/ API:", _api())
        if _is_ig_token():
            print("계정:", _get("me", fields="user_id,username"))
        else:
            print("토큰 사용자:", _get("me", fields="id,name"))
        uid = ig_user_id()
        print("인스타그램 계정 ID:", uid)
        print("계정 정보:", _get(uid, fields="username,media_count"))
        print("✅ 토큰 정상 — 게시 준비 완료")
