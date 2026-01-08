import mailbox
from collections import Counter
import re

def extract_email_addresses_with_names(mbox_file):
    """Extract all sender names and email addresses from the MBOX file."""
    mbox = mailbox.mbox(mbox_file)
    senders = []
    email_name_regex = r'(.*?)\s*<(.+?)>'  # Regex to extract "Name <email@example.com>"

    for message in mbox:
        if 'From' in message:
            from_header = str(message['From'])
            match = re.search(email_name_regex, from_header)
            if match:
                # Extract name and email
                name = match.group(1).strip('"') if match.group(1) else "Unknown"
                email = match.group(2)
            else:
                # If no match, treat the whole field as the email
                name = "Unknown"
                email = from_header.strip()
            
            senders.append((name, email))
    
    return senders

def main():
    mbox_file = "mails.mbox"  # Replace with your MBOX file name
    output_file = "top_senders_by_count.txt"
    
    print(f"Reading MBOX file: {mbox_file}...")

    senders = extract_email_addresses_with_names(mbox_file)
    print(f"Extracted {len(senders)} sender details.")

    # Count occurrences of each sender (name, email pair)
    senders_count = Counter(senders)
    most_common_senders = senders_count.most_common(50)

    # Write results to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Top 50 Senders by Email Count\n")
        f.write("=" * 70 + "\n\n")
        for (name, email), count in most_common_senders:
            line = f"{name} <{email}>: {count} emails\n"
            f.write(line)
            print(f"{name} <{email}>: {count} emails")
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
