# netops-drift

A network automation tool that detects **configuration drift** on network devices.
A controller VM collects each device config over SSH, compares it with a trusted
"golden" config, sends an alert (ntfy.sh) and shows everything in a web dashboard.

Mini project for the course "Programmation Reseaux" (Python).

## How it works

1. **Collect**: connect to each device in `inventory.yaml` over SSH (Netmiko) and read its config.
2. **Store**: save the config in `configs/backups/`.
3. **Compare**: compare it with the golden config in `configs/golden/`.
4. **Alert**: if there is a difference, send a push notification (ntfy.sh).
5. **Report / Dashboard**: generate an HTML report (Jinja2) and show the status in a Streamlit dashboard.

## Architecture

```
Windows (VMware Workstation, NAT 192.168.150.x)
|
|-- router1      VyOS 2026.03          192.168.150.140
|-- mikrotik1    MikroTik CHR 7.24.6   192.168.150.141
|-- securite     Ubuntu 24.04 (CONTROLLER VM)   192.168.150.136
        |-- cron          runs src/run.py every 5 minutes
        |-- dashboard     Streamlit on port 8501 (password protected)
        |-- ntfy.sh       push alert when a drift is found
```

The controller VM connects to the routers over SSH.
The administrator opens the dashboard from a browser: `http://192.168.150.136:8501`

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
    core.py        check_device, check_all (parallel), approve_golden
    run.py         command line: checks all devices
    auth.py        password login for the dashboard
    dashboard.py   Streamlit dashboard
  inventory.yaml   list of devices
  requirements.txt
```

## Supported devices

| Type | Example | Command used |
|---|---|---|
| `vyos` | router1 | `show configuration commands` |
| `mikrotik` | mikrotik1 | `/export` |

Secrets (password hashes, keys) are replaced by `<REDACTED>` before a config is saved.

## Setup on the controller VM (Ubuntu)

```
sudo apt update
sudo apt install -y git python3-venv python3-pip
git clone https://github.com/wassim-benmed/netops-drift.git
cd netops-drift
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (never commit it, use `chmod 600 .env`):

```
ROUTER_USER=your_vyos_user
ROUTER_PASS=your_vyos_password
MIKROTIK_USER=your_mikrotik_user
MIKROTIK_PASS=your_mikrotik_password
NTFY_TOPIC=your_private_topic_name
DASHBOARD_PASSWORD=your_dashboard_password
```

Devices in `inventory.yaml` use `ROUTER_USER` / `ROUTER_PASS` by default.
A device can use other variables with `username_env` and `password_env`:

```
devices:
  - name: router1
    host: 192.168.150.140
    type: vyos
  - name: mikrotik1
    host: 192.168.150.141
    type: mikrotik
    username_env: MIKROTIK_USER
    password_env: MIKROTIK_PASS
```

## Usage

### 1. Command line

```
python src/run.py
```

Example output:

```
[OK] router1: no drift
[DRIFT] mikrotik1: 1 added, 1 removed
[+] Report written to reports/drift_report.html
```

The exit code is `0` when there is no drift and `1` when there is a drift or an error.

### 2. Dashboard

```
streamlit run src/dashboard.py --server.address 0.0.0.0 --server.port 8501
```

Open `http://<controller-ip>:8501` and log in with `DASHBOARD_PASSWORD`.
The dashboard shows:

- metrics and a table with the status of each device (OK / DRIFT / ERROR / NO_GOLDEN)
- details per device: Differences, Current config, Golden config
- **Check now**: runs a check immediately
- **Approve as golden**: the current config becomes the new golden config (with a confirmation)

### 3. Automatic checks (cron)

```
crontab -e
```

```
*/5 * * * * cd /home/securite/netops-drift && /home/securite/netops-drift/venv/bin/python src/run.py >> /home/securite/netops-drift/cron.log 2>&1
```

Note: while a drift is not fixed or approved, an alert is sent at every run.

## Security

- Passwords and hashes are replaced by `<REDACTED>` before a config is saved.
- Credentials are read from `.env`, which is listed in `.gitignore`.
- The dashboard is protected by a password.

## Course concepts used

- **Git and GitHub**: branches, Pull Requests, secrets kept out of the repo
- **REST / HTTP**: alerts are sent with an HTTP request to ntfy.sh
- **Network automation**: Netmiko over SSH, YAML inventory, Jinja2 templating
- **Linux**: controller VM, cron, virtual environment
- **Compliance**: automatic check of the running config against a golden config

## Possible improvements

- Automatic rollback to the golden config
- Compliance rules (rules.yaml) and a compliance score
- Form to add a device from the dashboard
- Only one alert per drift (no repetition)