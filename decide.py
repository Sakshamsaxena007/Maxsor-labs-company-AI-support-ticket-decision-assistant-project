"""
Ties RAG + LLM together into one function: decide(ticket) -> validated decision dict.
Never lets a bad/unparseable LLM response reach the database - falls back to
NEEDS_MORE_INFORMATION instead of guessing.
"""
import json
import re

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY
from .rag import retrieve

_client = genai.Client(api_key=GEMINI_API_KEY)
CHAT_MODEL = "gemini-3.6-flash"

VALID_ACTIONS = {
    "APPROVE_RETURN", "REJECT_OPENED_ITEM", "REJECT_FOOD_RETURN", "REJECT_OUTSIDE_WINDOW",
    "APPROVE_REFUND_OR_REPLACEMENT", "REQUEST_PHOTOS", "APPROVE_REPLACEMENT",
    "REQUEST_DEFECT_EVIDENCE", "REPLACE_CORRECT_ITEM", "WAIT_AND_TRACK",
    "OPEN_SHIPPING_INVESTIGATION", "OFFER_REPLACEMENT_OR_REFUND",
    "CANCEL_AND_REFUND", "CANNOT_CANCEL_AFTER_DISPATCH", "NEEDS_MORE_INFORMATION",
}

SYSTEM_PROMPT = """You are a support-ticket decision assistant for an e-commerce company.

You will be given a customer ticket (with structured fields) and the most relevant
policy rules retrieved from the company's knowledge base.

Decide exactly ONE action, strictly based on the provided policy rules - never invent
a rule that isn't shown to you.

IMPORTANT: Only choose NEEDS_MORE_INFORMATION if the ticket is missing a field that is
genuinely required to apply any of the given policy rules (for example: no order value,
no timing information, and no product type at all). If the ticket's structured fields
already give you what a specific rule needs (e.g. order value, days since delivery,
opened/unopened status, product type), you MUST commit to that specific action - do not
choose NEEDS_MORE_INFORMATION just because some unrelated field is empty.

Respond with ONLY a JSON object, no markdown, no commentary, in this exact shape:
{"action": "<ONE_OF_THE_ALLOWED_ACTIONS>", "confidence": <0.0-1.0>, "reason": "<1-2 sentence reason citing the rule>", "sources": ["<file.md>", ...]}

Allowed actions: """ + ", ".join(sorted(VALID_ACTIONS))


def _build_user_prompt(ticket: dict, policy_chunks: list[dict]) -> str:
    policy_text = "\n".join(f"- ({c['source']}) {c['text']}" for c in policy_chunks)
    return f"""TICKET:
message: {ticket.get('message')}
order_value_inr: {ticket.get('order_value_inr')}
days_since_delivery: {ticket.get('days_since_delivery')}
days_since_dispatch: {ticket.get('days_since_dispatch')}
product_type: {ticket.get('product_type')}
opened_status: {ticket.get('opened_status')}
order_status: {ticket.get('order_status')}

RELEVANT POLICY RULES:
{policy_text}
"""


def _extract_json(raw_text: str) -> dict:
    """LLMs sometimes wrap JSON in ```json fences despite instructions - strip them."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def _fallback(reason: str, sources: list[str] | None = None) -> dict:
    return {
        "action": "NEEDS_MORE_INFORMATION",
        "confidence": 0.3,
        "reason": reason,
        "sources": sources or [],
    }


def _decide_once(ticket: dict, policy_chunks: list[dict]) -> dict:
    """Makes one call to the LLM and validates its response."""
    try:
        response = _client.models.generate_content(
            model=CHAT_MODEL,
            contents=_build_user_prompt(ticket, policy_chunks),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
            ),
        )
        result = _extract_json(response.text)
    except Exception as exc:
        return _fallback(f"LLM call failed or returned unparseable output: {exc}")

    action = result.get("action")
    if action not in VALID_ACTIONS:
        return _fallback(f"Model returned an invalid action ('{action}').",
                          [c["source"] for c in policy_chunks])

    try:
        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.5

    reason = str(result.get("reason", "")).strip() or "No reason provided by model."
    sources = result.get("sources")
    if not isinstance(sources, list) or not sources:
        sources = [c["source"] for c in policy_chunks]

    return {"action": action, "confidence": confidence, "reason": reason, "sources": sources}


def decide(ticket: dict) -> dict:
    """
    Main entrypoint. Always returns a dict matching the DecisionResponse schema.

    If the model punts to NEEDS_MORE_INFORMATION on the first try, we ask once more -
    borderline tickets sometimes get an inconsistent first response, and a single
    retry meaningfully improves reliability without hiding genuine ambiguous cases
    (if it says NEEDS_MORE_INFORMATION twice, we trust that answer and keep it).
    """
    policy_chunks = retrieve(ticket.get("message", ""), top_k=4)

    result = _decide_once(ticket, policy_chunks)
    if result["action"] == "NEEDS_MORE_INFORMATION":
        retry = _decide_once(ticket, policy_chunks)
        if retry["action"] != "NEEDS_MORE_INFORMATION":
            return retry
    return result


if __name__ == "__main__":
    sample = {
        "message": "My ₹3,500 order arrived damaged yesterday.",
        "order_value_inr": 3500,
        "days_since_delivery": 1,
        "days_since_dispatch": None,
        "product_type": "non_food",
        "opened_status": "opened",
        "order_status": "delivered",
    }
    print(json.dumps(decide(sample), indent=2))
