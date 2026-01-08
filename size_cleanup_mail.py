import mailbox
from email.header import decode_header
from collections import defaultdict
import re

def extract_sender(email_message):
    """Extract sender's email address from the 'From' header."""
    sender = email_message.get('From', '')
    # Use regex to find the email address
    match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
    return match.group(0) if match else sender

def decode_subject(subject):
    """Decode email subject."""
    if subject is None:
        return None
    decoded_parts = decode_header(subject)
    return ''.join(
        part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
        for part, encoding in decoded_parts
    )

def parse_mbox(file_path):
    """Parse the mbox file and calculate email sizes by sender."""
    sender_sizes = defaultdict(int)  # Store total size of emails per sender
    sender_counts = defaultdict(int)  # Store count of emails per sender
    mbox = mailbox.mbox(file_path)
    
    for message in mbox:
        try:
            sender = extract_sender(message)
            email_size = len(message.as_bytes())  # Calculate email size in bytes
            sender_sizes[sender] += email_size  # Accumulate total size
            sender_counts[sender] += 1  # Count emails
        except Exception as e:
            print(f"Error processing message: {e}")
    
    # Combine sizes and counts, then sort by total email size in descending order
    combined = [(sender, sender_sizes[sender], sender_counts[sender]) 
                for sender in sender_sizes]
    sorted_senders = sorted(combined, key=lambda x: x[1], reverse=True)
    return sorted_senders

def main():
    file_path = "mails.mbox"  # Replace with your mbox file path
    output_file = "top_senders_by_size.txt"
    
    sender_sizes = parse_mbox(file_path)
    
    # Write results to file and print to console
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Top 50 Senders by Total Email Size\n")
        f.write("=" * 70 + "\n\n")
        for sender, total_size, email_count in sender_sizes[:50]:  # Slice the top 50 senders
            size_kb = total_size / 1024
            size_mb = total_size / (1024 * 1024)
            # Use MB if >= 1 MB, otherwise KB
            if size_mb >= 1:
                size_str = f"{size_mb:.2f} MB"
            else:
                size_str = f"{size_kb:.2f} KB"
            line = f"{sender}: {size_str} (total from {email_count} email{'s' if email_count != 1 else ''})\n"
            f.write(line)
            print(f"{sender}: {size_str} (total from {email_count} email{'s' if email_count != 1 else ''})")
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
