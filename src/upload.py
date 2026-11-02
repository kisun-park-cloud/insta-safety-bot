"""5단계: 인스타그램 업로드 (Meta 공식 Instagram Graph API — 콘텐츠 게시 API).
인스타그램 서버가 이미지를 직접 내려받으므로 PUBLIC_BASE_URL 로 공개된 파일이어야 한다."""
import os
import time
import requests

API = f"https://graph.facebook.com/{os.getenv('IG_GRAPH_VERSION', 'v23.0')}"


def _post(path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.post(f"{API}/{path}", data=params, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Graph API 오류 {r.status_code}: {r.text}")
    return r.json()


def _wait_ready(container_id, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = requests.get(f"{API}/{container_id}", params={
            "fields": "status_code,status", "access_token": os.environ["IG_ACCESS_TOKEN"]}, timeout=30).json()
        if r.get("status_code") == "FINISHED":
            return
        if r.get("status_code") == "ERROR":
            raise RuntimeError(f"미디어 처리 실패: {r}")
        time.sleep(10)
    raise TimeoutError("미디어 처리 시간 초과")


def publish_carousel(image_urls: list[str], caption: str) -> str:
    ig = os.environ["IG_USER_ID"]
    children = [_post(f"{ig}/media", image_url=u, is_carousel_item="true")["id"] for u in image_urls[:10]]
    for c in children:
        _wait_ready(c)
    parent = _post(f"{ig}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    _wait_ready(parent)
    return _post(f"{ig}/media_publish", creation_id=parent)["id"]


def refresh_token() -> str:
    """장기 액세스 토큰 갱신 (만료 전 주기적으로 실행)."""
    r = requests.get(f"{API}/oauth/access_token", params={
        "grant_type": "fb_exchange_token",
        "client_id": os.environ["FB_APP_ID"], "client_secret": os.environ["FB_APP_SECRET"],
        "fb_exchange_token": os.environ["IG_ACCESS_TOKEN"]}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]
