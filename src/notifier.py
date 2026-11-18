import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

NTFY_SERVER = "https://ntfy.sh"
MAX_LENGTH = 3500


def send_alert(title, text, priority="default", tags=""):
    topic = os.getenv("NTFY_TOPIC")
    if not topic:
        print("[!] NTFY_TOPIC is missing in .env")
        return False
    headers = {"Title": title, "Priority": priority}
    if tags:
        headers["Tags"] = tags
    try:
        response = requests.post(
            f"{NTFY_SERVER}/{topic}",
            data=text[:MAX_LENGTH].encode("utf-8"),
            headers=headers,
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[!] Alert not sent ({type(e).__name__})")
        return False
    if response.ok:
        return True
    print(f"[!] ntfy error {response.status_code}")
    return False


def format_drift(added, removed):
    lines = [f"- {line}" for line in removed]
    lines += [f"+ {line}" for line in added]
    return "\n".join(lines)


def notify_drift(name, added, removed):
    title = f"Config drift on {name}"
    summary = f"{len(added)} added, {len(removed)} removed\n"
    text = summary + format_drift(added, removed)
    return send_alert(title, text, priority="high", tags="warning")


if __name__ == "__main__":
    # simulated drift, only to test the alert
    ok = notify_drift("router1", ["set system test 'x'"], [])
    print("[+] Alert sent" if ok else "[!] Alert not sent")