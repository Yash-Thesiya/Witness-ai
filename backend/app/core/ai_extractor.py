"""
AI Commitment Extractor using OpenRouter API.

Sends transcript text to LLM and gets back structured commitments.
"""
import json
import re
import calendar
from datetime import datetime, timedelta
from typing import Optional


import requests

from app.core.config import settings


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert AI that extracts ONLY clear, actionable commitments from transcripts.

========================
WHAT IS A COMMITMENT?
========================

A commitment requires ALL THREE:
1. A specific PERSON taking responsibility
2. A specific ACTION they will do
3. Clear intent (not vague or hypothetical)

INCLUDE:
✓ "I'll send the report by Monday." → Clear commitment
✓ "John will review the document by Friday." → Clear commitment
✓ "I'll complete it within 5 days." → Clear commitment
✓ "I'll send the update by Friday." → Clear commitment

EXCLUDE:
✗ "Maybe I'll investigate the performance issue later." → Too vague, no deadline
✗ "We should discuss infrastructure next month." → Suggestion, not commitment
✗ "Perhaps someone should look into it." → No owner
✗ "I think we should meet sometime." → Not a commitment

========================
TODAY'S DATE & WEEKDAY
========================

The user message will always include:
TODAY_DATE: YYYY-MM-DD
TODAY_WEEKDAY: (e.g., Wednesday)

You MUST use TODAY_DATE as reference for ALL date calculations.

========================
DATE CALCULATION RULES
========================

RULE 1 — TOMORROW:
tomorrow = TODAY_DATE + 1 day

RULE 2 — SPECIFIC WEEKDAY (e.g., "by Friday", "on Monday"):
- Find the NEXT occurrence of that weekday AFTER today
- If today IS that weekday, go to NEXT week's occurrence
- Example: TODAY = Wednesday 2026-06-25
  * "Friday" → 2026-06-27 (this week's Friday, 2 days ahead)
  * "Monday" → 2026-06-29 (next Monday, 4 days ahead)
  * "Wednesday" → 2026-07-01 (next week Wednesday, 7 days ahead)

RULE 3 — "NEXT [weekday]" (e.g., "next Monday", "next Wednesday"):
- Always means the weekday of the FOLLOWING week (7+ days ahead)
- Example: TODAY = Wednesday 2026-06-25
  * "next Monday" → 2026-06-29 (following Monday)
  * "next Wednesday" → 2026-07-01 (following Wednesday, NOT today)
  * "next Friday" → 2026-07-03 (following Friday)

RULE 4 — "THIS [weekday]" (e.g., "this Friday"):
- Means the NEAREST upcoming occurrence this week
- Example: TODAY = Wednesday 2026-06-25
  * "this Friday" → 2026-06-27
  * "this Monday" → already passed → go to next Monday 2026-06-29

RULE 5 — "WITHIN X DAYS":
- Add X days to TODAY_DATE
- Example: TODAY = 2026-06-25
  * "within 5 days" → 2026-06-30
  * "within 2 weeks" → 2026-07-09

RULE 6 — "END OF WEEK":
- Always means the Friday of the current week
- Example: TODAY = Wednesday 2026-06-25 → end of week = 2026-06-27

RULE 7 — "END OF MONTH":
- Last calendar day of the current month
- Example: June 2026 → 2026-06-30

RULE 8 — "NEXT MONTH":
- First day of next month
- Example: June 2026 → 2026-07-01

CRITICAL DATE RULES:
- NEVER return a date before TODAY_DATE
- ALWAYS output dates in YYYY-MM-DD format
- If no deadline mentioned → null
- If date is ambiguous → null

========================
OWNER EXTRACTION
========================

- Use the speaker name if clearly identified
- "I'll do it" when speaker is "John:" → owner = "John"
- If owner unknown → "Speaker"

========================
ACTION EXTRACTION
========================

Write concise, clear action descriptions:
- Start with a verb
- Remove filler words
- Keep the core action

Examples:
"I'll send the final project report tomorrow" → "Send the final project report"
"I need to complete the code review by Friday" → "Complete the code review"

========================
CONFIDENCE SCORING
========================

0.95 → explicit commitment + clear owner + clear deadline
0.85 → explicit commitment + clear owner + no deadline
0.75 → strong implied commitment
0.60 → weak but likely commitment
Below 0.60 → exclude entirely

========================
OUTPUT FORMAT
========================

Return ONLY a valid JSON array. No markdown, no explanation, nothing else.

Schema:
[
  {
    "owner": "string",
    "action": "string",
    "due_date": "YYYY-MM-DD or null",
    "confidence": 0.95
  }
]

If zero commitments found: []"""



def _resolve_relative_date(date_str: Optional[str],reference_date: datetime) -> Optional[str]:
    """
    Convert relative date strings into YYYY-MM-DD format.
    """

    if not date_str:
        return None

    date_str = date_str.strip()

    # Already YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str

    text = date_str.lower()
    today = reference_date.date()

    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    def upcoming_weekday(target_weekday: int):
        """
        Next upcoming weekday.
        If today is same weekday, return next week's occurrence.
        """
        days_ahead = target_weekday - today.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        return today + timedelta(days=days_ahead)

    def next_week_weekday(target_weekday: int):
        """
        'Next Monday', 'Next Friday'
        Always means the weekday in the following week.
        """
        upcoming = upcoming_weekday(target_weekday)
        return upcoming + timedelta(days=7)

    # --------------------------------------------------
    # Exact Relative Dates
    # --------------------------------------------------

    if "day after tomorrow" in text:
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")

    if "tomorrow" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    if "today" in text:
        return today.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # Next Monday / Next Friday
    # --------------------------------------------------

    match = re.search(
        r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        text
    )

    if match:
        weekday_name = match.group(1)
        resolved = next_week_weekday(weekday_map[weekday_name])
        return resolved.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # This Monday / This Friday
    # --------------------------------------------------

    match = re.search(
        r"this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        text
    )

    if match:
        weekday_name = match.group(1)
        resolved = upcoming_weekday(weekday_map[weekday_name])
        return resolved.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # Plain weekday names
    # Example: Friday
    # --------------------------------------------------

    for weekday_name, weekday_num in weekday_map.items():
        if re.search(rf"\b{weekday_name}\b", text):
            resolved = upcoming_weekday(weekday_num)
            return resolved.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # End of week / EOW
    # --------------------------------------------------

    if "end of week" in text or "eow" in text:
        resolved = upcoming_weekday(4)  # Friday
        return resolved.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # Next week
    # Return next Monday
    # --------------------------------------------------

    if "next week" in text:
        days_until_next_monday = (7 - today.weekday()) % 7

        if days_until_next_monday == 0:
            days_until_next_monday = 7

        next_monday = today + timedelta(days=days_until_next_monday)

        return next_monday.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # End of month
    # --------------------------------------------------

    if "end of month" in text:
        last_day = calendar.monthrange(
            today.year,
            today.month
        )[1]

        end_of_month = today.replace(day=last_day)

        return end_of_month.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # In X days
    # Example:
    # in 3 days
    # within 5 days
    # --------------------------------------------------

    match = re.search(
        r"(?:in|within)\s+(\d+)\s+day",
        text
    )

    if match:
        days = int(match.group(1))
        resolved = today + timedelta(days=days)

        return resolved.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # In X weeks
    # Example:
    # in 2 weeks
    # within 3 weeks
    # --------------------------------------------------

    match = re.search(
        r"(?:in|within)\s+(\d+)\s+week",
        text
    )

    if match:
        weeks = int(match.group(1))
        resolved = today + timedelta(weeks=weeks)

        return resolved.strftime("%Y-%m-%d")

    return None


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

def extract_commitments_from_text(transcript_text: str) -> list[dict]:
    """
    Send transcript to OpenRouter LLM and return list of commitment dicts.
    """
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set in .env")

    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")
    weekday_name = now.strftime("%A")  # Monday, Tuesday, etc.

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://witness-app.local",
        "X-Title": "Witness Commitment Tracker",
    }

    user_message = f"""TODAY_DATE: {today_str}
TODAY_WEEKDAY: {weekday_name}

Extract all commitments from this transcript:

{transcript_text}"""

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    try:
        response = requests.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("OpenRouter API timed out after 30 seconds.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"OpenRouter API request failed: {exc}")

    data = response.json()

    try:
        raw_text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError(f"Unexpected OpenRouter response format: {data}")

    commitments = _parse_llm_response(raw_text)

    # Safety pass — Python se verify karo dates
    reference_date = datetime.utcnow()
    for c in commitments:
        if c.get("due_date"):
            resolved = _resolve_relative_date(c["due_date"], reference_date)
            if resolved:
                c["due_date"] = resolved

    return commitments


def _parse_llm_response(raw_text: str) -> list[dict]:
    """
    Parse JSON array from LLM response.
    Handles cases where LLM wraps JSON in markdown code blocks.
    """
    # Remove markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()
    cleaned = cleaned.strip("`").strip()

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON array in the text
        match = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                return []
        else:
            return []

    if not isinstance(result, list):
        return []

    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_commitment(raw: dict) -> Optional[dict]:
    """
    Validate a raw commitment dict from LLM.
    Returns cleaned dict or None if invalid.
    owner + action are required.
    """
    owner = str(raw.get("owner", "")).strip()
    action = str(raw.get("action", "")).strip()

    if not owner or not action:
        return None  # Reject incomplete commitments

    # Clamp confidence between 0 and 1
    confidence = float(raw.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    # Validate due_date format
    due_date = raw.get("due_date")
    if due_date and not re.match(r"\d{4}-\d{2}-\d{2}", str(due_date)):
        due_date = None

    return {
        "owner": owner,
        "action": action,
        "due_date": due_date,
        "confidence": confidence,
    }

def check_fulfillment_with_ai(
    transcript_text: str,
    existing_commitments: list[dict],
) -> list[dict]:
    """
    Ask LLM to check if transcript contains fulfillment evidence
    for any of the existing commitments.
    
    Returns list of fulfilled commitment ids with evidence.
    """
    if not settings.OPENROUTER_API_KEY:
        return []

    if not existing_commitments:
        return []

    commitments_str = "\n".join([
        f"ID {c['id']}: {c['owner']} → {c['action']}"
        for c in existing_commitments
    ])

    prompt = f"""You are validating whether an existing commitment has been COMPLETED.

Existing commitments:
{commitments_str}

Transcript:
{transcript_text}

STRICT RULES:

A commitment is fulfilled ONLY if the transcript contains explicit completion evidence.

Examples of fulfillment:
- "I sent the report"
- "The report has been delivered"
- "Completed"
- "Finished"
- "Done"
- "Shared with the team"
- "I already reviewed it"

NOT fulfillment:
- Mentioning the owner's name
- Mentioning the commitment topic
- Status updates
- Delays
- Extensions
- Future promises
- Repeating the commitment

Example:

Commitment:
John -> Send report

Transcript:
"John"

Result:
[]

Transcript:
"John said he will send the report next Monday."

Result:
[]

Transcript:
"John has sent the report."

Result:
[ID]

Return ONLY JSON array of fulfilled IDs."""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://witness-app.local",
        "X-Title": "Witness Commitment Tracker",
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200,
    }

    try:
        response = requests.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        result = json.loads(cleaned)
        if isinstance(result, list):
            return [int(x) for x in result]
        return []
    except Exception as e:
        print(f"[Fulfillment AI] Error: {e}")
        return []
    
#-----------------------------------
#  modification detect
#-----------------------------------

    
def check_modifications_with_ai(
    transcript_text: str,
    existing_commitments: list[dict],
) -> list[dict]:
    """
    Ask LLM to check if transcript contains modification evidence
    for any existing commitments.
    
    Returns list of dicts:
    [{"id": 1, "new_due_date": "2026-06-30", "new_action": "...", "reason": "..."}]
    """
    if not settings.OPENROUTER_API_KEY or not existing_commitments:
        return []

    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    commitments_str = "\n".join([
        f"ID {c['id']}: {c['owner']} → {c['action']} (due: {c.get('due_date', 'no deadline')})"
        for c in existing_commitments
    ])

    prompt = f"""Today's date is {today_str}.

You are checking whether existing commitments were MODIFIED.

Existing commitments:
{commitments_str}

Transcript:
{transcript_text}

Respond ONLY with a JSON array.

Example:

[
  {{
    "id": 1,
    "new_due_date": "2026-06-29",
    "new_action": null,
    "reason": "deadline moved from Friday to next Monday"
  }}
]

If no modifications found, return:
[]"""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://witness-app.local",
        "X-Title": "Witness Commitment Tracker",
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"].strip()
        cleaned = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        result = json.loads(cleaned)
        if isinstance(result, list):
            return result
        return []
    except Exception as e:
        print(f"[ModificationAI] Error: {e}")
        return []