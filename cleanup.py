#!/usr/bin/env python3
"""
Gmail Cleanup CLI
=================

Commands:
  analyze      Show top senders in your inbox (no deletion)
  clean        Interactively delete emails by sender, filter, or preset
  unsubscribe  List senders with unsubscribe links

Run with --help for full usage.
"""

import argparse
import sys
import webbrowser
from gmail_auth import get_gmail_service
from analyze_live import fetch_senders, group_by_domain, print_sender_table
from batch_delete import fetch_all_message_ids, batch_delete

PRESETS = {
    "nuke-promotions": "category:promotions older_than:3m",
    "old-unread":      "is:unread older_than:1y -label:important",
    "large-senders":   "size:5mb",
    "social-noise":    "category:social older_than:6m",
    "old-updates":     "category:updates older_than:6m",
}


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------

def build_query(args):
    parts = []

    if getattr(args, "preset", None):
        if args.preset not in PRESETS:
            print(f"Unknown preset '{args.preset}'. Available: {', '.join(PRESETS)}")
            sys.exit(1)
        return PRESETS[args.preset]

    if getattr(args, "ai_query", None):
        from ai_scorer import translate_query
        model = getattr(args, "model", "llama3")
        query = translate_query(args.ai_query, model=model)
        if query:
            print(f"  [AI] Translated to Gmail query: {query}")
            return query
        else:
            print("  Falling back to empty query (all mail).")
            return ""

    if getattr(args, "sender", None):
        parts.append(f"from:{args.sender}")
    if getattr(args, "category", None):
        parts.append(f"category:{args.category}")
    if getattr(args, "label", None):
        parts.append(f"label:{args.label}")
    if getattr(args, "older_than", None):
        parts.append(f"older_than:{args.older_than}")
    if getattr(args, "unread", False):
        parts.append("is:unread")
    if getattr(args, "min_size", None):
        parts.append(f"size:{args.min_size}")
    if getattr(args, "keyword", None):
        parts.append(args.keyword)

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_analyze(args, service):
    query = build_query(args)
    if query:
        print(f"\nAnalyzing emails matching: {query!r}")
    else:
        print("\nAnalyzing all mail...")

    rows = fetch_senders(service, query=query, max_messages=args.max_messages)

    use_ai = getattr(args, "ai", False)
    if use_ai:
        from ai_scorer import score_senders
        rows = score_senders(rows, model=args.model)
        rows.sort(key=lambda r: (r.get("score") or 0), reverse=True)
        print(f"\nTop {args.top} senders (sorted by AI delete-score):\n")
    else:
        print(f"\nTop {args.top} senders:\n")

    if args.domain:
        domain_rows = group_by_domain(rows)
        print_sender_table(domain_rows, top=args.top, by_domain=True)
    else:
        print_sender_table(rows, top=args.top)

    if use_ai and not args.domain:
        print("\n  Score: 10 = very safe to delete, 0 = risky")
        for row in rows[:args.top]:
            if row.get("score") is not None:
                print(f"  [{row['score']:>2}/10] {row['address']}: {row.get('ai_reason', '')}")


def cmd_clean(args, service):
    dry_run = args.dry_run

    # Non-interactive: if --sender specified, clean directly
    if getattr(args, "sender", None) and not getattr(args, "interactive", False):
        query = build_query(args)
        _clean_query(service, query, dry_run=dry_run)
        return

    # If a direct filter is set (no interactive flag needed), just run it
    query = build_query(args)

    if query:
        print(f"\nFilter: {query!r}")
        print("Counting matching emails...")
        ids = fetch_all_message_ids(service, query)
        if not ids:
            print("  No emails found matching that filter.")
            return

        print(f"\n  Found {len(ids)} emails.")

        if dry_run:
            print("  [dry-run] No emails deleted.")
            return

        confirm = input(f"\nDelete all {len(ids)} emails? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            return

        deleted = batch_delete(service, ids, dry_run=False)
        print(f"\nDeleted {deleted} emails.")
        return

    # Interactive sender-selection mode
    print("\nFetching top senders for interactive selection...")
    rows = fetch_senders(service, query="", max_messages=args.max_messages)

    use_ai = getattr(args, "ai", False)
    if use_ai:
        from ai_scorer import score_senders, summarize_sender
        rows = score_senders(rows, model=args.model)
        rows.sort(key=lambda r: (r.get("score") or 0), reverse=True)

    print(f"\nTop {args.top} senders (pick which to delete):\n")
    print_sender_table(rows, top=args.top)

    print("\nEnter numbers to delete (e.g. 1,3,5-8) or 'q' to quit:")
    selection = input("> ").strip()
    if selection.lower() == "q":
        print("Aborted.")
        return

    selected_rows = _parse_selection(selection, rows[:args.top])
    if not selected_rows:
        print("No valid selection.")
        return

    print(f"\nSelected {len(selected_rows)} senders:")
    total_ids = []
    for row in selected_rows:
        sender_query = f"from:{row['address']}"
        if use_ai and row.get("subjects"):
            summary = summarize_sender(row, model=args.model)
            if summary:
                print(f"  {row['address']} — {summary}")
            else:
                print(f"  {row['address']} ({row['count']} emails)")
        else:
            print(f"  {row['address']} ({row['count']} emails)")
        ids = fetch_all_message_ids(service, sender_query, quiet=True)
        total_ids.extend(ids)

    print(f"\nTotal: {len(total_ids)} emails to delete from {len(selected_rows)} senders.")

    if dry_run:
        print("[dry-run] No emails deleted.")
        return

    confirm = input(f"\nProceed with deletion? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    deleted = batch_delete(service, total_ids)
    print(f"\nDeleted {deleted} emails.")


def cmd_unsubscribe(args, service):
    print("\nFetching senders with unsubscribe links...")
    rows = fetch_senders(service, query="", max_messages=args.max_messages)
    unsub_rows = [r for r in rows if r["unsubscribable"]]

    if not unsub_rows:
        print("No unsubscribable senders found.")
        return

    print(f"\nFound {len(unsub_rows)} senders with List-Unsubscribe headers:\n")
    print_sender_table(unsub_rows, top=len(unsub_rows))

    print("\nFor each sender, would you like to:")
    print("  1) Fetch their unsubscribe link and open it in your browser")
    print("  2) Just delete all their emails")
    print("  3) Both")
    print("  q) Quit")

    for row in unsub_rows[:args.top]:
        print(f"\n--- {row['address']} ({row['count']} emails) ---")
        choice = input("Action (1/2/3/q): ").strip().lower()

        if choice == "q":
            break
        if choice in ("1", "3"):
            link = _get_unsubscribe_link(service, row["address"])
            if link:
                print(f"  Opening: {link}")
                webbrowser.open(link)
            else:
                print("  Could not find unsubscribe link.")
        if choice in ("2", "3"):
            ids = fetch_all_message_ids(service, f"from:{row['address']}")
            print(f"  Deleting {len(ids)} emails from {row['address']}...")
            batch_delete(service, ids)
            print("  Done.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_query(service, query, dry_run=False):
    print(f"\nQuery: {query!r}")
    print("Counting matching emails...")
    ids = fetch_all_message_ids(service, query)
    print(f"Found {len(ids)} emails.")
    if dry_run:
        print("[dry-run] No emails deleted.")
        return
    confirm = input(f"Delete all {len(ids)} emails? (yes/no): ").strip().lower()
    if confirm == "yes":
        deleted = batch_delete(service, ids)
        print(f"Deleted {deleted} emails.")
    else:
        print("Aborted.")


def _parse_selection(text, rows):
    """Parse '1,3,5-8' into a list of row dicts."""
    selected = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            for n in range(int(a), int(b) + 1):
                if 1 <= n <= len(rows):
                    selected.append(rows[n - 1])
        elif part.isdigit():
            n = int(part)
            if 1 <= n <= len(rows):
                selected.append(rows[n - 1])
    # Deduplicate while preserving order
    seen = set()
    result = []
    for r in selected:
        if r["address"] not in seen:
            seen.add(r["address"])
            result.append(r)
    return result


def _get_unsubscribe_link(service, sender_address):
    """Fetch the List-Unsubscribe header from the most recent email from sender."""
    try:
        result = service.users().messages().list(
            userId="me", q=f"from:{sender_address}", maxResults=1
        ).execute()
        messages = result.get("messages", [])
        if not messages:
            return None
        meta = service.users().messages().get(
            userId="me",
            id=messages[0]["id"],
            format="metadata",
            metadataHeaders=["List-Unsubscribe"],
        ).execute()
        headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
        raw = headers.get("List-Unsubscribe", "")
        # Extract URL from <url> or mailto: format
        import re
        urls = re.findall(r"<(https?://[^>]+)>", raw)
        if urls:
            return urls[0]
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _add_filter_args(parser):
    parser.add_argument("--sender", metavar="EMAIL", help="Filter by sender email address")
    parser.add_argument("--category", metavar="NAME",
                        choices=["promotions", "social", "updates", "forums"],
                        help="Gmail category tab")
    parser.add_argument("--label", metavar="LABEL", help="Gmail label name")
    parser.add_argument("--older-than", metavar="AGE", dest="older_than",
                        help="e.g. 6m, 1y, 30d")
    parser.add_argument("--unread", action="store_true", help="Only unread emails")
    parser.add_argument("--min-size", metavar="SIZE", dest="min_size",
                        help="Minimum email size, e.g. 5mb, 1mb")
    parser.add_argument("--keyword", metavar="TERM", help="Gmail search keyword")
    parser.add_argument("--preset", choices=list(PRESETS.keys()),
                        help="Use a pre-built filter combination")
    parser.add_argument("--ai-query", metavar="TEXT", dest="ai_query",
                        help="Natural language query (requires --ai or Ollama)")


def _add_ai_args(parser):
    parser.add_argument("--ai", action="store_true",
                        help="Enable Ollama AI scoring (optional, falls back if unavailable)")
    parser.add_argument("--model", default="llama3", metavar="MODEL",
                        help="Ollama model name (default: llama3)")


def main():
    parser = argparse.ArgumentParser(
        prog="cleanup.py",
        description="Gmail Cleanup CLI — analyze and delete email directly from your inbox.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup.py analyze
  python cleanup.py analyze --domain --top 30
  python cleanup.py analyze --category promotions
  python cleanup.py analyze --ai

  python cleanup.py clean
  python cleanup.py clean --sender newsletters@example.com --dry-run
  python cleanup.py clean --preset nuke-promotions --dry-run
  python cleanup.py clean --older-than 1y --unread
  python cleanup.py clean --ai-query "marketing emails I never read" --ai

  python cleanup.py unsubscribe

Available presets:
""" + "\n".join(f"  {k:20s} {v}" for k, v in PRESETS.items()),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # analyze
    p_analyze = sub.add_parser("analyze", help="Show top senders (read-only)")
    _add_filter_args(p_analyze)
    _add_ai_args(p_analyze)
    p_analyze.add_argument("--top", type=int, default=50, metavar="N",
                           help="Number of senders to show (default: 50)")
    p_analyze.add_argument("--domain", action="store_true",
                           help="Group results by domain instead of individual address")
    p_analyze.add_argument("--max-messages", type=int, default=5000, dest="max_messages",
                           metavar="N", help="Max emails to scan (default: 5000)")

    # clean
    p_clean = sub.add_parser("clean", help="Delete emails interactively or by filter")
    _add_filter_args(p_clean)
    _add_ai_args(p_clean)
    p_clean.add_argument("--dry-run", action="store_true", dest="dry_run",
                         help="Preview deletion count without actually deleting")
    p_clean.add_argument("--top", type=int, default=50, metavar="N",
                         help="Number of senders shown in interactive mode (default: 50)")
    p_clean.add_argument("--max-messages", type=int, default=5000, dest="max_messages",
                         metavar="N", help="Max emails to scan in interactive mode (default: 5000)")

    # unsubscribe
    p_unsub = sub.add_parser("unsubscribe", help="List and act on unsubscribable senders")
    p_unsub.add_argument("--top", type=int, default=50, metavar="N",
                         help="Max senders to show (default: 50)")
    p_unsub.add_argument("--max-messages", type=int, default=5000, dest="max_messages",
                         metavar="N", help="Max emails to scan (default: 5000)")

    args = parser.parse_args()

    try:
        service = get_gmail_service()
    except FileNotFoundError as e:
        print(f"\nSetup required:\n{e}")
        sys.exit(1)

    if args.command == "analyze":
        cmd_analyze(args, service)
    elif args.command == "clean":
        cmd_clean(args, service)
    elif args.command == "unsubscribe":
        cmd_unsubscribe(args, service)


if __name__ == "__main__":
    main()
