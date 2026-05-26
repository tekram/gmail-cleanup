"""
Optional Ollama-powered scoring for email senders.
All functions degrade gracefully when Ollama is unavailable.
"""

import json

_ollama_available = None


def _check_ollama():
    global _ollama_available
    if _ollama_available is not None:
        return _ollama_available
    try:
        import ollama
        ollama.list()
        _ollama_available = True
    except Exception:
        _ollama_available = False
    return _ollama_available


def score_senders(rows, model="llama3"):
    """
    Add a 'score' field (0-10, higher = safer to delete) to each sender row.
    Falls back to score=None if Ollama is unavailable.
    """
    if not _check_ollama():
        print("  [AI] Ollama not available — skipping AI scoring.")
        for row in rows:
            row["score"] = None
        return rows

    import ollama

    print(f"  [AI] Scoring {len(rows)} senders with {model}...")
    for row in rows:
        subjects_str = "; ".join(row.get("subjects", [])[:5]) or "(no subjects)"
        prompt = (
            f"You are helping clean up an email inbox. "
            f"Rate how safe it is to bulk-delete ALL emails from this sender on a scale of 0-10. "
            f"10 = definitely safe to delete (newsletter, promo, automated), "
            f"0 = risky (personal contact, important service). "
            f"Sender: {row['name']} <{row['address']}>\n"
            f"Recent subjects: {subjects_str}\n"
            f"Reply with ONLY a JSON object: {{\"score\": <number>, \"reason\": \"<one line>\"}}"
        )
        try:
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0},
            )
            text = response["message"]["content"].strip()
            # Extract JSON even if model adds extra text
            start = text.find("{")
            end = text.rfind("}") + 1
            parsed = json.loads(text[start:end])
            row["score"] = int(parsed.get("score", 5))
            row["ai_reason"] = parsed.get("reason", "")
        except Exception as e:
            row["score"] = None
            row["ai_reason"] = f"error: {e}"

    return rows


def translate_query(natural_language, model="llama3"):
    """
    Convert a natural language description into a Gmail search query string.
    Returns the query string, or None if Ollama is unavailable.
    """
    if not _check_ollama():
        print("  [AI] Ollama not available — cannot translate natural language query.")
        return None

    import ollama

    prompt = (
        "Convert this description into a valid Gmail search query. "
        "Use Gmail search operators like: from:, older_than:, category:, is:unread, has:attachment, label:, subject:, size:. "
        "Combine operators with spaces (implicit AND) or OR. "
        f"Description: {natural_language}\n"
        'Reply with ONLY a JSON object: {"query": "<gmail search query>"}'
    )
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0},
        )
        text = response["message"]["content"].strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        parsed = json.loads(text[start:end])
        return parsed.get("query", "")
    except Exception as e:
        print(f"  [AI] Query translation failed: {e}")
        return None


def summarize_sender(row, model="llama3"):
    """Return a one-line summary of what a sender's emails are about."""
    if not _check_ollama():
        return None

    import ollama

    subjects = "; ".join(row.get("subjects", [])[:5])
    if not subjects:
        return None

    prompt = (
        f"Summarize in one short sentence what kind of emails '{row['address']}' sends, "
        f"based on these subject lines: {subjects}"
    )
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0},
        )
        return response["message"]["content"].strip()
    except Exception:
        return None
