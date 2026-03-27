#!/usr/bin/env python3
"""
Check AgentMail inbox for new messages.
Handles attachments properly with correct message_id encoding.

Usage:
    python check_inbox.py [--limit 10] [--download-attachments] [--save-dir DIR]
"""

import argparse
import os
import sys
import base64
import requests
import urllib.parse

API_KEY = os.environ.get('AGENTMAIL_API_KEY', 'am_us_6939bd2e9b766b89e61a67258f580d691cfd89df803c366fc228ad7e69a62fb2')
BASE_URL = 'https://api.agentmail.to/v0'


def get_messages(inbox_id: str = 'sallysquirrel@agentmail.to', limit: int = 10):
    """Fetch recent messages from inbox."""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    url = f'{BASE_URL}/inboxes/{inbox_id}/messages?limit={limit}'
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return data.get('messages', [])


def get_attachment(inbox_id: str, message_id: str, attachment_id: str):
    """
    Get attachment with correct message_id encoding.
    
    The API requires the message_id to be URL-encoded with angle brackets:
    <message@example.com> becomes %3Cmessage@example.com%3E
    """
    headers = {'Authorization': f'Bearer {API_KEY}'}
    
    # URL-encode the message_id (it has angle brackets that need to be preserved)
    encoded_msg_id = urllib.parse.quote(message_id, safe='')
    
    # First get the attachment metadata (which includes download_url)
    url = f'{BASE_URL}/inboxes/{inbox_id}/messages/{encoded_msg_id}/attachments/{attachment_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    attachment_data = response.json()
    download_url = attachment_data.get('download_url')
    
    if not download_url:
        return None
    
    # Download the actual file
    download_response = requests.get(download_url)
    download_response.raise_for_status()
    
    return {
        'filename': attachment_data.get('filename'),
        'content_type': attachment_data.get('content_type'),
        'content': download_response.content,
        'size': attachment_data.get('size')
    }


def download_attachment_to_file(inbox_id: str, message_id: str, attachment_id: str, save_dir: str = '.'):
    """Download an attachment and save to file."""
    attachment = get_attachment(inbox_id, message_id, attachment_id)
    
    if not attachment:
        print(f"  Could not download attachment {attachment_id}")
        return None
    
    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(save_dir, attachment['filename'])
    with open(filepath, 'wb') as f:
        f.write(attachment['content'])
    
    return filepath


def main():
    parser = argparse.ArgumentParser(description='Check AgentMail inbox')
    parser.add_argument('--limit', type=int, default=10, help='Number of messages to fetch')
    parser.add_argument('--download-attachments', action='store_true', help='Download any attachments')
    parser.add_argument('--save-dir', default='./downloads', help='Directory to save attachments')
    parser.add_argument('--inbox', default='sallysquirrel@agentmail.to', help='Inbox to check')
    
    args = parser.parse_args()
    
    print(f"Checking inbox: {args.inbox}")
    print(f"Fetching {args.limit} recent messages...\n")
    
    messages = get_messages(args.inbox, args.limit)
    
    if not messages:
        print("No messages found.")
        return
    
    for msg in messages:
        # Parse from field
        from_field = msg.get('from', 'Unknown')
        subject = msg.get('subject', '(No subject)')
        preview = msg.get('preview', '').strip()[:80]
        timestamp = msg.get('timestamp', '')[:19]
        
        print(f"From: {from_field}")
        print(f"Subject: {subject}")
        print(f"Date: {timestamp}")
        print(f"Preview: {preview}")
        
        # Handle attachments
        attachments = msg.get('attachments', [])
        if attachments:
            print(f"Attachments: {len(attachments)}")
            for att in attachments:
                att_id = att.get('attachment_id')
                filename = att.get('filename')
                size = att.get('size')
                print(f"  - {filename} ({size} bytes) [ID: {att_id}]")
                
                if args.download_attachments:
                    print(f"    Downloading...")
                    filepath = download_attachment_to_file(
                        args.inbox, 
                        msg.get('message_id'), 
                        att_id, 
                        args.save_dir
                    )
                    if filepath:
                        print(f"    Saved to: {filepath}")
        
        print("-" * 60)


if __name__ == '__main__':
    main()
