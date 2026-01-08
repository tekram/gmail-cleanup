# Gmail Cleanup Tools

A collection of Python scripts to analyze MBOX email files exported from Gmail. These tools help you identify which senders are contributing the most to your mailbox size and volume.

## Scripts

### 🚀 `analyze_mailbox.py` (Recommended)
**Run both analyses at once!** This unified script runs both the email count and size analysis sequentially, giving you a complete overview of your mailbox.

**Usage:**
```bash
python analyze_mailbox.py
```

**Output:**
Runs both analyses in sequence, showing:
1. Top senders by email count
2. Top senders by email size

Results are saved to:
- `top_senders_by_count.txt` - Top 50 senders by email count
- `top_senders_by_size.txt` - Top 50 senders by email size

### 1. `cleanup_email.py`
Analyzes your MBOX file to identify the top senders by **email count**. This script extracts sender names and email addresses, then displays the top 50 senders ranked by the number of emails they've sent.

**Features:**
- Extracts sender names and email addresses from email headers
- Counts occurrences of each sender
- Displays top 50 senders sorted by email count
- Saves results to `top_senders_by_count.txt` for easy copy and paste

**Usage:**
```bash
python cleanup_email.py
```

**Output:**
Results are displayed in the console and saved to `top_senders_by_count.txt`:
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
- Saves results to `top_senders_by_size.txt` for easy copy and paste

**Usage:**
```bash
python size_cleanup_mail.py
```

**Output:**
Results are displayed in the console and saved to `top_senders_by_size.txt`:
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

2. **Place your MBOX file in the project root directory** (the same folder where `cleanup_email.py` and `size_cleanup_mail.py` are located)

3. **Rename your MBOX file to `mails.mbox`**
   
   **Important:** Both scripts require the file to be named exactly `mails.mbox` and located in the project root directory. The scripts use relative paths, so the file must be in the same directory as the Python scripts.
   
   **Example directory structure:**
   ```
   gmail-cleanup/
   ├── analyze_mailbox.py      ← Run this to execute both analyses
   ├── cleanup_email.py
   ├── size_cleanup_mail.py
   ├── mails.mbox              ← Your MBOX file must be here with this exact name
   ├── top_senders_by_count.txt  ← Generated after running cleanup_email.py
   └── top_senders_by_size.txt   ← Generated after running size_cleanup_mail.py
   ```
   
   **Note:** If your exported MBOX file has a different name (e.g., `mail.mbox` or `All mail Including Spam and Trash.mbox`), you must rename it to `mails.mbox`. Alternatively, you can edit the `mbox_file` variable in `cleanup_email.py` (line 29) or the `file_path` variable in `size_cleanup_mail.py` (line 41) to match your file name.

4. Run the analysis:
   
   **Option A: Run both analyses together (Recommended)**
   ```bash
   python analyze_mailbox.py
   ```
   
   **Option B: Run individual analyses**
   ```bash
   python cleanup_email.py      # Email count analysis only
   # or
   python size_cleanup_mail.py  # Email size analysis only
   ```

## Use Cases

- **Identify bulk senders**: Find newsletters, marketing emails, or automated notifications that are cluttering your inbox
- **Free up storage**: Identify senders whose emails are taking up the most space
- **Email cleanup**: Prioritize which senders to unsubscribe from or delete emails from
- **Storage analysis**: Understand which domains or senders are consuming the most storage

## Output Files

Both scripts automatically save their results to text files for easy copy and paste:

- **`top_senders_by_count.txt`** - Contains the top 50 senders ranked by email count
- **`top_senders_by_size.txt`** - Contains the top 50 senders ranked by total email size

These files are created in the same directory as the scripts and can be easily opened, copied, or shared.

## Notes

- Both scripts process the entire MBOX file, which may take some time for large mailboxes
- The scripts handle common email header formats and encoding issues
- Error messages are displayed if individual emails cannot be processed, but the script continues processing the rest of the mailbox
- Results are saved to text files automatically - no need to copy from the console!

