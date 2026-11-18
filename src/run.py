import sys

from collector import fetch_config, load_inventory, save_backup
from drift import GOLDEN_DIR, compare
from notifier import notify_drift, send_alert
from report import main as build_report


def main():
    problems = 0
    for device in load_inventory():
        name = device["name"]
        print(f"[+] {name}: collecting config...")
        try:
            config = fetch_config(device)
        except Exception as e:
            print(f"    ERROR: {e}")
            send_alert(
                f"Collection failed on {name}",
                f"Could not read the config of {name}.",
                priority="high",
                tags="x",
            )
            problems += 1
            continue
        save_backup(name, config)

        if not (GOLDEN_DIR / f"{name}.cfg").exists():
            print(f"    no golden config for {name}, comparison skipped")
            continue

        added, removed = compare(name)
        if added or removed:
            print(f"[DRIFT] {name}: {len(added)} added, {len(removed)} removed")
            notify_drift(name, added, removed)
            problems += 1
        else:
            print(f"[OK] {name}: no drift")

    try:
        build_report()
    except FileNotFoundError as e:
        print(f"[!] Report not generated: {e}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())