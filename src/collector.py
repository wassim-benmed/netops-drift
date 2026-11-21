import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from netmiko import ConnectHandler

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "configs" / "backups"

load_dotenv(BASE_DIR / ".env")

# maps the "type" written in inventory.yaml to the Netmiko driver name
DEVICE_TYPES = {"mikrotik": "mikrotik_routeros", "vyos": "vyos"}

SECRET_WORDS = ("password", "secret", "private-key")

# RouterOS style: key=value or key="value" (password, secret, keys...)
SECRET_PATTERN = re.compile(
    r'(password|secret|private-key|pre-shared-key|passphrase)=("[^"]*"|\S+)'
)


def load_inventory():
    with open(BASE_DIR / "inventory.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["devices"]


def clean_config(raw):
    # 1. RouterOS adds header lines starting with "#" that contain the date.
    #    They change at every export and would look like a false drift.
    # 2. Secrets (password hashes, keys) must never be stored in Git.
    out = []
    for line in raw.splitlines():
        if line.startswith("#"):
            continue
        line = line.rstrip()
        if "'" in line and any(w in line for w in SECRET_WORDS):
            line = line.split("'")[0] + "'<REDACTED>'"
        line = SECRET_PATTERN.sub(r"\1=<REDACTED>", line)
        out.append(line)
    return "\n".join(out).strip() + "\n"


def fetch_config(device):
    # each device can name its own variables in .env (username_env / password_env)
    # otherwise the default ROUTER_USER / ROUTER_PASS are used
    username = os.getenv(device.get("username_env", "ROUTER_USER"))
    password = os.getenv(device.get("password_env", "ROUTER_PASS"))
    conn = ConnectHandler(
        device_type=DEVICE_TYPES[device["type"]],
        host=device["host"],
        username=username,
        password=password,
    )
    try:
        if device["type"] == "vyos":
            raw = conn.send_command("show configuration commands")
        else:
            raw = conn.send_command("/export")
    finally:
        conn.disconnect()
    return clean_config(raw)


def save_backup(name, config):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKUP_DIR / f"{name}.cfg"
    path.write_text(config, encoding="utf-8")
    return path


if __name__ == "__main__":
    for device in load_inventory():
        print(f"[+] Collecting {device['name']} ({device['host']})...")
        try:
            config = fetch_config(device)
            path = save_backup(device["name"], config)
            print(f"    saved to {path}")
        except Exception as e:
            print(f"    ERROR: {e}")