# netops-drift

A small network automation tool that detects **configuration drift** on a router.
It collects the running config, compares it with a trusted "golden" config, sends an
alert and builds an HTML report when something has changed.

Mini project for the course "Programmation Reseaux" (Python).

## How it works

1. **Collect**: connect to each device in `inventory.yaml` over SSH (Netmiko) and read its config.
2. **Store**: save the config in `configs/backups/` (versioned with Git).
3. **Compare**: compare it with the golden config in `configs/golden/`.
4. **Alert**: if there is a difference, send a push notification (ntfy.sh).
5. **Report**: generate an HTML report (Jinja2) in `reports/`.

## Project structure

```
netops-drift/
  configs/
    golden/        reference configs (approved)
    backups/       latest configs collected from the devices
  src/
    collector.py   SSH collection + secret redaction
    drift.py       comparison golden vs backup
    notifier.py    alerts through ntfy.sh
    report.py      HTML report with Jinja2
    run.py         runs the whole workflow
  inventory.yaml   list of devices
  requirements.txt
```

## Lab environment

- VyOS 2026.03 router running in VMware Workstation (simulation, no physical router)
- Python 3 on Windows, libraries: Netmiko, Requests, Jinja2, PyYAML, python-dotenv

## Setup

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (never commit it):

```
ROUTER_USER=your_router_user
ROUTER_PASS=your_router_password
NTFY_TOPIC=your_private_topic_name
```

Edit `inventory.yaml`:

```
devices:
  - name: router1
    host: 192.168.150.140
    type: vyos
```

## Usage

Create the golden config once, after checking that the router config is correct:

```
python src\collector.py
copy configs\backups\router1.cfg configs\golden\router1.cfg
```

Then run the full workflow whenever you want to check for drift:

```
python src\run.py
```

Example output when a drift is found:

```
[+] router1: collecting config...
[DRIFT] router1: 1 added, 0 removed
[+] Report written to reports\drift_report.html
```

The exit code is `0` when there is no drift and `1` when there is a drift or an error.

## Security

- Passwords and hashes are replaced by `<REDACTED>` before a config is saved, so no secret reaches the Git repository.
- Credentials are read from `.env`, which is listed in `.gitignore`.

## Course concepts used

- **Git and GitHub**: versioned configs, conventional commits, secrets kept out of the repo
- **REST / HTTP**: alerts are sent with an HTTP request to ntfy.sh
- **Network automation**: Netmiko over SSH, YAML inventory, Jinja2 templating
- **Compliance**: automatic check of the running config against a golden config

## Possible improvements

- Automatic rollback to the golden config
- Several devices and vendors (MikroTik is already prepared in the collector)
- Scheduled runs and a CI pipeline
