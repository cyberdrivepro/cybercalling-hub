"""
================================================================================
  🚀 Trigger Test Payload to local n8n Webhook
================================================================================
"""

import requests
import sys

def trigger():
    test_urls = [
        "http://localhost:5678/webhook-test/cybercalling-trigger",
        "http://localhost:5678/webhook/cybercalling-trigger"
    ]
    payload = {
        "phone": "+919876543210",
        "name": "Suraj",
        "message": "Hello Suraj! n8n automated Voice AI campaign triggered successfully.",
        "provider": "OMNIDIM"
    }

    print("Sending test lead to n8n webhook...")
    for url in test_urls:
        try:
            r = requests.post(url, json=payload, timeout=5)
            print(f"URL: {url} -> Status: {r.status_code}")
            if r.status_code in [200, 201]:
                print("🎉 SUCCESS! n8n received the test event!")
                return
        except Exception as e:
            print(f"URL: {url} -> Note: {e}")

if __name__ == "__main__":
    trigger()
