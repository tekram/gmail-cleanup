"""
Gmail Cleanup Analysis Tool
Runs both email count and size analysis on your MBOX file.
"""

import cleanup_email
import size_cleanup_mail

def main():
    print("=" * 70)
    print("Gmail Cleanup Analysis")
    print("=" * 70)
    print()
    
    # Run email count analysis
    print("PART 1: Analyzing senders by email count...")
    print("-" * 70)
    cleanup_email.main()
    
    print()
    print()
    
    # Run size analysis
    print("PART 2: Analyzing senders by email size...")
    print("-" * 70)
    size_cleanup_mail.main()
    
    print()
    print("=" * 70)
    print("Analysis complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()

