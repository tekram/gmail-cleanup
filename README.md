# Gmail Cleanup

A Python CLI that connects directly to your Gmail inbox via the Gmail API to analyze, filter, and bulk-delete emails — no Takeout export required.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Gmail API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select an existing one)
3. Enable the **Gmail API** under "APIs & Services > Library"
4. Create an **OAuth 2.0 Client ID** (choose "Desktop app")
5. Download the JSON file and save it as `credentials.json` in this directory

On first run, a browser window will open asking you to authorize access. Your token is saved to `~/.gmail-cleanup-token.json` for future runs.

### 3. Run

```bash
# See top 50 senders in your inbox
python cleanup.py analyze

# Interactively pick senders to delete
python cleanup.py clean

# See which senders have unsubscribe links
python cleanup.py unsubscribe
```

---

## Commands

### `analyze` — Explore your inbox (no deletion)

```bash
python cleanup.py analyze                          # top 50 senders
python cleanup.py analyze --top 100               # show more
python cleanup.py analyze --domain                 # group by domain
python cleanup.py analyze --category promotions   # filter to Promotions tab
python cleanup.py analyze --older-than 1y         # emails older than 1 year
python cleanup.py analyze --ai                    # add AI delete-safety scores (needs Ollama)
```

### `clean` — Delete emails

**Interactive mode** (pick senders from a ranked list):
```bash
python cleanup.py clean
python cleanup.py clean --ai                      # sort by AI delete-safety score
```

**Filter mode** (specify what to delete):
```bash
python cleanup.py clean --sender newsletters@example.com
python cleanup.py clean --category promotions --older-than 6m
python cleanup.py clean --older-than 1y --unread
python cleanup.py clean --min-size 5mb
python cleanup.py clean --label newsletters
python cleanup.py clean --keyword "unsubscribe"
```

**Presets** (common cleanup combinations):
```bash
python cleanup.py clean --preset nuke-promotions   # Promotions tab > 3 months old
python cleanup.py clean --preset old-unread        # Unread mail > 1 year old
python cleanup.py clean --preset large-senders     # Emails > 5MB
python cleanup.py clean --preset social-noise      # Social tab > 6 months old
python cleanup.py clean --preset old-updates       # Updates tab > 6 months old
```

**Always preview first with `--dry-run`:**
```bash
python cleanup.py clean --preset nuke-promotions --dry-run
```

**Natural language queries** (requires Ollama):
```bash
python cleanup.py clean --ai-query "newsletters I never read" --ai
```

### `unsubscribe` — Manage subscriptions

```bash
python cleanup.py unsubscribe
```

Shows senders that include `List-Unsubscribe` headers. For each, you can open the unsubscribe link in your browser, delete all their emails, or both.

---

## Options Reference

| Flag | Description |
|------|-------------|
| `--sender EMAIL` | Filter by sender address |
| `--category NAME` | Gmail category: `promotions`, `social`, `updates`, `forums` |
| `--label LABEL` | Gmail label name |
| `--older-than AGE` | Age filter: `30d`, `6m`, `1y`, etc. |
| `--unread` | Only unread emails |
| `--min-size SIZE` | Minimum size: `1mb`, `5mb`, etc. |
| `--keyword TERM` | Gmail search keyword |
| `--preset NAME` | Pre-built filter combination (see above) |
| `--top N` | Number of senders to show (default: 50) |
| `--domain` | Group analysis by domain instead of address |
| `--dry-run` | Preview without deleting |
| `--ai` | Enable Ollama AI scoring (optional) |
| `--model MODEL` | Ollama model to use (default: `llama3`) |
| `--ai-query TEXT` | Natural language → Gmail query translation |
| `--max-messages N` | Max emails to scan for analysis (default: 5000) |

---

## AI / Local LLM (Optional)

The `--ai` flag enables Ollama-powered features:

- **Delete-safety scoring**: Rates each sender 0–10 on how safe it is to bulk-delete
- **Natural language queries**: `--ai-query "find newsletters I never read"` translates to Gmail search operators
- **Sender summaries**: One-line description of what a sender's emails are about

The tool works fully without `--ai`. If `--ai` is passed but Ollama is not running, a warning is printed and the tool continues without AI features.

**Setup Ollama:**
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3     # or: mistral, phi3, gemma2
```

---

## Offline MBOX Analysis (Legacy)

The original scripts for analyzing a local MBOX export from Google Takeout are still available:

```bash
python analyze_mailbox.py   # requires mails.mbox in this directory
python cleanup_email.py
python size_cleanup_mail.py
```

---

## File Structure

```
gmail-cleanup/
├── cleanup.py          # Main CLI entry point
├── gmail_auth.py       # OAuth 2.0 authentication
├── analyze_live.py     # Live inbox analysis via Gmail API
├── batch_delete.py     # Chunked deletion with rate-limit handling
├── ai_scorer.py        # Optional Ollama AI scoring
├── requirements.txt    # Python dependencies
├── credentials.json    # Your OAuth credentials (you create this)
├── analyze_mailbox.py  # Legacy: offline MBOX analysis
├── cleanup_email.py    # Legacy: MBOX sender count analysis
└── size_cleanup_mail.py # Legacy: MBOX sender size analysis
```
