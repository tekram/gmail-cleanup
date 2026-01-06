# Gmail Cleanup Tools

A collection of Python scripts to analyze MBOX email files exported from Gmail. These tools help you identify which senders are contributing the most to your mailbox size and volume.

## Scripts

### 1. `cleanup_email.py`
Analyzes your MBOX file to identify the top senders by **email count**. This script extracts sender names and email addresses, then displays the top 50 senders ranked by the number of emails they've sent.

**Features:**
- Extracts sender names and email addresses from email headers
- Counts occurrences of each sender
- Displays top 50 senders sorted by email count

**Usage:**
```bash
python cleanup_email.py
```

**Output:**
```
Top Senders:
John Doe <john@example.com>: 150 emails
Jane Smith <jane@example.com>: 120 emails
...
```

### 2. `size_cleanup_mail.py`
Analyzes your MBOX file to identify the top senders by **total email size**. This script calculates the total size of all emails from each sender and displays the top 50 senders ranked by total storage used.

**Features:**
- Extracts sender email addresses
- Calculates total size of emails per sender (in bytes)
- Displays top 50 senders sorted by total size (shown in KB)

**Usage:**
```bash
python size_cleanup_mail.py
```

**Output:**
```
Top 50 Senders by Email Size:
newsletter@example.com: 1250.50 KB
marketing@company.com: 980.25 KB
...
```

## Requirements

- Python 3.x
- Standard library modules (no external dependencies required):
  - `mailbox`
  - `collections`
  - `re`
  - `email.header`

## Setup

1. Export your Gmail emails as an MBOX file:
   - Go to [Google Takeout](https://takeout.google.com/)
   - Select Gmail
   - Choose MBOX format
   - Download and extract the archive

2. Place your MBOX file in the project directory and name it `mails.mbox`

   **Note:** Both scripts currently expect the MBOX file to be named `mails.mbox`. If your file has a different name, edit the `mbox_file` or `file_path` variable in the respective script.

3. Run either script:
   ```bash
   python cleanup_email.py
   # or
   python size_cleanup_mail.py
   ```

## Use Cases

- **Identify bulk senders**: Find newsletters, marketing emails, or automated notifications that are cluttering your inbox
- **Free up storage**: Identify senders whose emails are taking up the most space
- **Email cleanup**: Prioritize which senders to unsubscribe from or delete emails from
- **Storage analysis**: Understand which domains or senders are consuming the most storage

## Notes

- Both scripts process the entire MBOX file, which may take some time for large mailboxes
- The scripts handle common email header formats and encoding issues
- Error messages are displayed if individual emails cannot be processed, but the script continues processing the rest of the mailbox

