"""Phone notifications through ntfy (https://ntfy.sh): free, no account needed.

Install the ntfy app on your phone, subscribe to a topic name only you know,
and set NTFY_TOPIC to that same name.
"""
from __future__ import annotations

import json
import os
import urllib.request


def notify(title: str, message: str, tags: list[str] | None = None, priority: int = 3) -> bool:
    """Send a push notification. Returns False (and never raises) if it couldn't be sent."""
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    print(f"\n🔔 {title}\n   {message}")
    if not topic:
        print("   (NTFY_TOPIC isn't set, so no phone notification was sent.)")
        return False
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    body = json.dumps({"topic": topic, "title": title, "message": message,
                       "tags": tags or [], "priority": priority}).encode()
    req = urllib.request.Request(server, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception as e:  # a failed notification must never stop the pipeline
        print(f"   (Couldn't send the phone notification: {e})")
        return False
