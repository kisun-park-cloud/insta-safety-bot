"""Claude가 그린 SVG 일러스트 검증·변환."""
import re
import xml.etree.ElementTree as ET

MAX_BYTES = 40_000
FORBIDDEN = {"script", "image", "foreignObject", "iframe", "use", "a", "style", "text", "textPath", "tspan"}


def validate(svg: str) -> str | None:
    """문제 있으면 사유 문자열, 정상이면 None."""
    if not svg:
        return None
    if len(svg.encode()) > MAX_BYTES:
        return f"SVG 용량 초과({len(svg.encode())}B > {MAX_BYTES}B)"
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        return f"SVG 문법 오류: {e}"
    if not root.tag.endswith("svg"):
        return "최상위 태그가 svg 가 아님"
    if root.get("viewBox", "").split() != ["0", "0", "900", "480"]:
        return "viewBox 는 '0 0 900 480' 이어야 함"
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in FORBIDDEN:
            return f"사용 금지 요소 <{tag}> (글자·외부이미지·스크립트 금지)"
        for k, v in el.attrib.items():
            if k.split("}")[-1] == "href" or re.search(r"url\((?!#)", v) or k.startswith("on"):
                return f"외부 참조/이벤트 속성 금지: {k}"
    return None
