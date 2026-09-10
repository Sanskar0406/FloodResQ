import os
import re
import json
import base64
from typing import Dict, Any, Optional
import httpx

VALID_URGENCY = ["critical", "high", "medium", "low"]
VALID_CREDIBILITY = ["high", "medium", "low"]

def heuristic_score(description: str, need_type: str = "rescue") -> Dict[str, str]:
    """Intelligent fallback NLP triage engine when offline or no API key."""
    desc_lower = description.lower()
    length = len(desc_lower.strip())

    # Critical patterns
    critical_patterns = [
        r"\btrapped\b", r"\bdrown", r"\broof\b", r"\brooftop\b", r"\bchest[- ]deep\b",
        r"\bneck[- ]deep\b", r"\binfant\b", r"\bbaby\b", r"\belderly\b", r"\bpregnant\b",
        r"\bbleeding\b", r"\bunconscious\b", r"\bcardiac\b", r"\bswept\b", r"\bcurrent\b",
        r"\bcollapsed\b", r"\bdying\b", r"\blife[- ]threatening\b", r"\bimmediate rescue\b",
        r"\bsos\b", r"\bcannot swim\b", r"\bcan't breathe\b", r"\bcrushed\b"
    ]

    # High patterns
    high_patterns = [
        r"\brising fast\b", r"\brising rapidly\b", r"\bwaist[- ]deep\b", r"\bknee[- ]deep\b",
        r"\bstuck in car\b", r"\bvehicle\b", r"\bcut off\b", r"\bstranded\b",
        r"\bdiabetic\b", r"\binsulin\b", r"\bmedicine\b", r"\binjured\b", r"\bfracture\b",
        r"\bno electricity\b", r"\bwater entering house\b", r"\bground floor flooded\b",
        r"\burgent\b", r"\bhelp soon\b"
    ]

    # Low patterns
    low_patterns = [
        r"\bmild\b", r"\breceding\b", r"\breceded\b", r"\bpuddle\b", r"\bdrainage slow\b",
        r"\bwater clearing\b", r"\bjust informing\b", r"\bmonitoring\b", r"\bcleared\b"
    ]

    is_critical = any(re.search(pat, desc_lower) for pat in critical_patterns)
    is_high = any(re.search(pat, desc_lower) for pat in high_patterns)
    is_low = any(re.search(pat, desc_lower) for pat in low_patterns)

    # Urgency assignment
    if is_critical or (need_type == "rescue" and ("child" in desc_lower or "water rising" in desc_lower)):
        urgency = "critical"
        reasoning = "Critical urgency: Imminent threat to life or trapped individuals identified in report."
    elif is_high or need_type == "medical" or need_type == "rescue":
        urgency = "high"
        reasoning = "High urgency: Severe flood impact requiring swift dispatch and priority assistance."
    elif is_low:
        urgency = "low"
        reasoning = "Low urgency: Informational or receding condition with low immediate danger."
    else:
        urgency = "medium"
        reasoning = "Medium urgency: Significant flood condition requiring shelter, food, or community aid."

    # Credibility assignment
    if length > 35 and any(w in desc_lower for w in ["near", "at", "road", "street", "building", "floor", "bridge", "nagar", "colony"]):
        credibility = "high"
    elif length > 15:
        credibility = "medium"
    else:
        credibility = "medium"

    return {
        "urgency": urgency,
        "credibility": credibility,
        "reasoning": reasoning
    }

async def score_report(
    description: str,
    need_type: str = "rescue",
    photo_bytes: Optional[bytes] = None,
    photo_mime: str = "image/jpeg"
) -> Dict[str, str]:
    """Score report urgency and credibility using Gemini API with intelligent fallback."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        return heuristic_score(description, need_type)

    prompt = f"""You are triaging a citizen flood emergency report for municipal rescue responders.
Need type requested: {need_type}
Report description: "{description}"

Assess this emergency and return ONLY a JSON object with:
- "urgency": "critical" (life-threatening/trapped/infant/injured), "high" (needs help within 1-2 hours), "medium" (needs shelter/food/aid), or "low" (informational/receding).
- "credibility": "high" (specific details, landmarks, coherent), "medium", or "low" (spam/vague).
- "reasoning": a single concise sentence justifying the urgency score.

Return strictly JSON format without markdown code fences."""

    parts: list = [{"text": prompt}]

    if photo_bytes:
        try:
            b64_data = base64.b64encode(photo_bytes).decode("utf-8")
            parts.append({
                "inlineData": {
                    "mimeType": photo_mime,
                    "data": b64_data
                }
            })
        except Exception:
            pass

    # Try Gemini 2.5 Flash, then 1.5 Flash
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": parts}],
                        "generationConfig": {"maxOutputTokens": 300, "temperature": 0.2}
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    cleaned = re.sub(r"^```(json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                    cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
                    parsed = json.loads(cleaned)
                    urgency = parsed.get("urgency", "").lower()
                    credibility = parsed.get("credibility", "").lower()
                    reasoning = parsed.get("reasoning", "")
                    return {
                        "urgency": urgency if urgency in VALID_URGENCY else "medium",
                        "credibility": credibility if credibility in VALID_CREDIBILITY else "high",
                        "reasoning": reasoning or "AI scored based on reported situation details."
                    }
        except Exception:
            continue

    # Fallback to intelligent heuristic
    return heuristic_score(description, need_type)
