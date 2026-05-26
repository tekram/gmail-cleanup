import re
import time
from collections import defaultdict
from email.header import decode_header as _decode_header
from googleapiclient.errors import HttpError

# Headers we fetch per message (metadata only — fast, no body download)
FETCH_HEADERS = ["From", "Date", "Subject", "List-Unsubscribe"]


def _decode(value):
    if not value:
        return ""
    parts = _decode_header(value)
    result = []
    for raw, enc in parts:
        if isinstance(raw, bytes):
            result.append(raw.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(raw)
    return "".join(result)


def _parse_sender(from_header):
    """Return (display_name, email_address) from a From header string."""
    decoded = _decode(from_header)
    match = re.search(r"(.*?)\s*<(.+?)>", decoded)
    if match:
        name = match.group(1).strip().strip('"')
        addr = match.group(2).strip().lower()
    else:
        name = ""
        addr = decoded.strip().lower()
    return name or addr, addr


def _root_domain(addr):
    """Extract registrable domain from an email address."""
    parts = addr.split("@")
    if len(parts) != 2:
        return addr
    domain_parts = parts[1].split(".")
    if len(domain_parts) >= 2:
        return ".".join(domain_parts[-2:])
    return parts[1]


def fetch_senders(service, query="", max_messages=5000, quiet=False):
    """
    Fetch message metadata from Gmail matching `query` and aggregate by sender.

    Returns a list of dicts:
        {
          "name": str,
          "address": str,
          "domain": str,
          "count": int,
          "unsubscribable": bool,
          "subjects": [str, ...]   # up to 5 recent subjects
        }
    """
    sender_data = defaultdict(lambda: {
        "name": "",
        "count": 0,
        "unsubscribable": False,
        "subjects": [],
    })

    page_token = None
    fetched = 0

    while fetched < max_messages:
        kwargs = {
            "userId": "me",
            "q": query,
            "maxResults": min(500, max_messages - fetched),
        }
        if page_token:
            kwargs["pageToken"] = page_token

        result = _retry(lambda: service.users().messages().list(**kwargs).execute())
        messages = result.get("messages", [])
        if not messages:
            break

        # Batch-fetch metadata for this page
        batch_ids = [m["id"] for m in messages]
        metas = _batch_get_metadata(service, batch_ids)

        for meta in metas:
            headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
            from_raw = headers.get("From", "")
            subject_raw = headers.get("Subject", "")
            unsub = bool(headers.get("List-Unsubscribe"))

            name, addr = _parse_sender(from_raw)
            domain = _root_domain(addr)
            subject = _decode(subject_raw)

            entry = sender_data[addr]
            entry["name"] = entry["name"] or name
            entry["count"] += 1
            if unsub:
                entry["unsubscribable"] = True
            if len(entry["subjects"]) < 5:
                entry["subjects"].append(subject)

        fetched += len(messages)
        if not quiet:
            print(f"  Analyzed {fetched} emails...", end="\r", flush=True)

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    if not quiet:
        print()

    rows = []
    for addr, entry in sender_data.items():
        rows.append({
            "address": addr,
            "name": entry["name"],
            "domain": _root_domain(addr),
            "count": entry["count"],
            "unsubscribable": entry["unsubscribable"],
            "subjects": entry["subjects"],
        })

    rows.sort(key=lambda r: r["count"], reverse=True)
    return rows


def _batch_get_metadata(service, message_ids):
    """Fetch metadata for a list of message IDs using a batch HTTP request."""
    results = []
    errors = []

    def callback(request_id, response, exception):
        if exception:
            errors.append(exception)
        else:
            results.append(response)

    # Split into sub-batches of 100 (Gmail API limit per HTTP batch)
    for i in range(0, len(message_ids), 100):
        chunk = message_ids[i:i + 100]
        batch = service.new_batch_http_request(callback=callback)
        for mid in chunk:
            batch.add(
                service.users().messages().get(
                    userId="me",
                    id=mid,
                    format="metadata",
                    metadataHeaders=FETCH_HEADERS,
                )
            )
        _retry(batch.execute)

    return results


def _retry(fn, max_retries=4):
    delay = 2
    for attempt in range(max_retries):
        try:
            return fn()
        except HttpError as e:
            if e.resp.status == 429 and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise


def group_by_domain(rows):
    """Aggregate sender rows by root domain."""
    domain_data = defaultdict(lambda: {"count": 0, "addresses": [], "unsubscribable": False})
    for row in rows:
        d = row["domain"]
        domain_data[d]["count"] += row["count"]
        domain_data[d]["addresses"].append(row["address"])
        if row["unsubscribable"]:
            domain_data[d]["unsubscribable"] = True

    result = [
        {
            "domain": domain,
            "count": data["count"],
            "addresses": data["addresses"],
            "unsubscribable": data["unsubscribable"],
        }
        for domain, data in domain_data.items()
    ]
    result.sort(key=lambda r: r["count"], reverse=True)
    return result


def print_sender_table(rows, top=50, by_domain=False):
    """Pretty-print a ranked sender table to stdout."""
    rows = rows[:top]
    if not rows:
        print("  No emails found matching your filters.")
        return

    if by_domain:
        header = f"{'#':>4}  {'Domain':<35} {'Emails':>8}  {'Unsub':>5}"
        print(header)
        print("-" * len(header))
        for i, row in enumerate(rows, 1):
            unsub = "yes" if row["unsubscribable"] else ""
            print(f"{i:>4}  {row['domain']:<35} {row['count']:>8}  {unsub:>5}")
    else:
        header = f"{'#':>4}  {'Sender':<45} {'Emails':>8}  {'Unsub':>5}"
        print(header)
        print("-" * len(header))
        for i, row in enumerate(rows, 1):
            label = f"{row['name']} <{row['address']}>" if row["name"] != row["address"] else row["address"]
            if len(label) > 44:
                label = label[:41] + "..."
            unsub = "yes" if row["unsubscribable"] else ""
            print(f"{i:>4}  {label:<45} {row['count']:>8}  {unsub:>5}")
