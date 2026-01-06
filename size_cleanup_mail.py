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
    mbox = mailbox.mbox(file_path)
    
    for message in mbox:
        try:
            sender = extract_sender(message)
            email_size = len(message.as_bytes())  # Calculate email size in bytes
            sender_sizes[sender] += email_size
        except Exception as e:
            print(f"Error processing message: {e}")
    
    # Sort senders by total email size in descending order
    sorted_senders = sorted(sender_sizes.items(), key=lambda x: x[1], reverse=True)
    return sorted_senders

def main():
    file_path = "mails.mbox"  # Replace with your mbox file path
    sender_sizes = parse_mbox(file_path)
    
    # Print the top 50 senders with their total email sizes
    print("Top 50 Senders by Email Size:")
    for sender, size in sender_sizes[:50]:  # Slice the top 50 senders
        print(f"{sender}: {size / 1024:.2f} KB")  # Convert size to KB for readability

if __name__ == "__main__":
    main()
