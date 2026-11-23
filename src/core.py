from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from collector import BACKUP_DIR, fetch_config, load_inventory, save_backup
from drift import GOLDEN_DIR, compare
from notifier import notify_drift, send_alert


def check_device(device, send_alerts=True):
    """Collect one device, compare it with its golden config, return a dict."""
    name = device["name"]
    result = {
        "name": name,
        "host": device["host"],
        "type": device["type"],
        "status": "OK",
        "added": [],
        "removed": [],
        "error": "",
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        config = fetch_config(device)
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        if send_alerts:
            send_alert(
                f"Collection failed on {name}",
                f"Could not read the config of {name}.",
                priority="high",
                tags="x",
            )
        return result

    save_backup(name, config)

    if not (GOLDEN_DIR / f"{name}.cfg").exists():
        result["status"] = "NO_GOLDEN"
        return result

    added, removed = compare(name)
    result["added"], result["removed"] = added, removed
    if added or removed:
        result["status"] = "DRIFT"
        if send_alerts:
            notify_drift(name, added, removed)
    return result


def check_all(send_alerts=True):
    """Check every device of the inventory in parallel."""
    devices = load_inventory()
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(lambda d: check_device(d, send_alerts), devices))


def approve_golden(name):
    """Declare the latest backup as the new reference (golden) config."""
    source = BACKUP_DIR / f"{name}.cfg"
    target = GOLDEN_DIR / f"{name}.cfg"
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")