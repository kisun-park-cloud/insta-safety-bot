"""5단계: 인스타그램 업로드 — Instagram API with Instagram Login (페이스북 페이지 불필요).
인스타그램 서버가 이미지를 직접 내려받으므로 PUBLIC_BASE_URL 로 공개된 파일이어야 한다.
필요 권한: instagram_business_basic, instagram_business_content_publish"""
import os
import time
import requests

API = f"https://graph.instagram.com/{os.getenv('IG_GRAPH_VERSION', 'v23.0')}"


def _token():
    return os.environ["IG_ACCESS_TOKEN"]


def _check(r):
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram API 오류 {r.status_code}: {r.text}")
    return r.json()


def _post(path, **params):
    params["access_token"] = _token()
    return _check(requests.post(f"{API}/{path}", data=params, timeout=60))


def _get(path, **params):
    params["access_token"] = _token()
    return _check(requests.get(f"{API}/{path}", params=params, timeout=30))


def ig_user_id() -> str:
    """IG_USER_ID 미설정 시 토큰으로 계정 ID 자동 조회."""
    return os.getenv("IG_USER_ID") or _get("me", fields="user_id,username")["user_id"]


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


def refresh_token() -> str:
    """장기 토큰(60일) 갱신 — 발급 후 24시간 이상 지났고 아직 유효한 토큰만 갱신 가능."""
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": _token()}, timeout=30)
    return _check(r)["access_token"]


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["refresh"]:
        print(refresh_token())
    elif sys.argv[1:] == ["whoami"]:
        print(_get("me", fields="user_id,username"))
