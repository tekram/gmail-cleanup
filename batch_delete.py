import time
from googleapiclient.errors import HttpError

BATCH_SIZE = 1000  # Gmail API max per batchDelete call


def batch_delete(service, message_ids, dry_run=False, quiet=False):
    """Delete messages in batches of 1000. Returns count deleted."""
    if not message_ids:
        return 0

    if dry_run:
        if not quiet:
            print(f"  [dry-run] Would delete {len(message_ids)} emails.")
        return len(message_ids)

    total = len(message_ids)
    deleted = 0
    chunks = [message_ids[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    for i, chunk in enumerate(chunks, 1):
        if not quiet:
            print(f"  Deleting batch {i}/{len(chunks)} ({len(chunk)} emails)...", end=" ", flush=True)
        _delete_with_retry(service, chunk)
        deleted += len(chunk)
        if not quiet:
            print(f"done. ({deleted}/{total} total)")

    return deleted


def _delete_with_retry(service, ids, max_retries=4):
    delay = 2
    for attempt in range(max_retries):
        try:
            service.users().messages().batchDelete(
                userId="me",
                body={"ids": ids}
            ).execute()
            return
        except HttpError as e:
            if e.resp.status == 429 and attempt < max_retries - 1:
                print(f"\n  Rate limited. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise


def fetch_all_message_ids(service, query, quiet=False):
    """Page through Gmail search results and return all message IDs."""
    ids = []
    page_token = None

    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token

        result = service.users().messages().list(**kwargs).execute()
        messages = result.get("messages", [])
        ids.extend(m["id"] for m in messages)

        if not quiet:
            print(f"  Found {len(ids)} emails so far...", end="\r", flush=True)

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    if not quiet:
        print()  # newline after \r

    return ids
