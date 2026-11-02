"""Claude API 호출 공통부. 안전 분류기 거절 시 서버측 대체 모델로 자동 전환."""
import json
import anthropic

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용

FALLBACK_BETA = "server-side-fallback-2026-07-01"


def ask_json(model: str, system: str, user: str, schema_model, *, tools=None,
             effort: str = "high"):
    """Pydantic 모델 스키마로 JSON을 받아 검증된 객체로 반환."""
    kwargs = dict(
        model=model,
        max_tokens=64000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={
            "effort": effort,
            "format": {"type": "json_schema",
                       "schema": _strict_schema(schema_model.model_json_schema())},
        },
        betas=[FALLBACK_BETA],
        fallbacks="default",
    )
    if tools:
        kwargs["tools"] = tools
    with client.beta.messages.stream(**kwargs) as stream:
        resp = stream.get_final_message()

    if resp.stop_reason == "refusal":
        raise RuntimeError(f"모델이 요청을 거절함: {resp.stop_details}")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("출력 길이 초과")
    text = [b.text for b in resp.content if b.type == "text"][-1]
    return schema_model.model_validate(json.loads(text))


def _strict_schema(schema: dict) -> dict:
    """구조화 출력 요건: 모든 object에 additionalProperties=false, 전 필드 required, $ref 인라인."""
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(dict(defs[node["$ref"].split("/")[-1]]))
            node = {k: walk(v) for k, v in node.items() if k not in ("title", "default")}
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}).keys())
            return node
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    return walk(schema)
