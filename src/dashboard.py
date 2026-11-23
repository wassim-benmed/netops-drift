import streamlit as st

from collector import BACKUP_DIR
from core import approve_golden, check_all
from drift import GOLDEN_DIR

st.set_page_config(page_title="NetOps Controller", layout="wide")

STATUS_LABEL = {
    "OK": ":green[OK]",
    "DRIFT": ":red[DRIFT]",
    "ERROR": ":orange[ERROR]",
    "NO_GOLDEN": ":gray[NO GOLDEN]",
}


def read_config(folder, name):
    path = folder / f"{name}.cfg"
    return path.read_text(encoding="utf-8") if path.exists() else "(file not found)"


def run_check(send_alerts):
    with st.spinner("Checking devices..."):
        st.session_state["results"] = check_all(send_alerts=send_alerts)


def do_approve(name):
    approve_golden(name)
    for r in st.session_state["results"]:
        if r["name"] == name:
            r["status"], r["added"], r["removed"] = "OK", [], []
    st.session_state[f"confirm_{name}"] = False
    st.session_state["flash"] = f"{name}: golden config updated."


st.title("NetOps Controller")
st.caption("Configuration drift detection for network devices")

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

with st.sidebar:
    st.header("Actions")
    send_alerts = st.checkbox("Send ntfy alerts", value=True)
    if st.button("Check now", type="primary"):
        run_check(send_alerts)

# first load: quiet check (no alert), so the page is not empty
if "results" not in st.session_state:
    run_check(send_alerts=False)

results = st.session_state["results"]
if not results:
    st.info("No device found in inventory.yaml")
    st.stop()

# ---- overview ----
counts = {s: sum(1 for r in results if r["status"] == s) for s in STATUS_LABEL}
c1, c2, c3, c4 = st.columns(4)
c1.metric("Devices", len(results))
c2.metric("OK", counts["OK"])
c3.metric("Drift", counts["DRIFT"])
c4.metric("Errors", counts["ERROR"])

st.subheader("Devices")
widths = [2, 2, 1, 2, 3]
header = st.columns(widths)
for col, title in zip(header, ["Name", "Address", "Type", "Status", "Last check"]):
    col.markdown(f"**{title}**")
for r in results:
    row = st.columns(widths)
    row[0].write(r["name"])
    row[1].write(r["host"])
    row[2].write(r["type"])
    row[3].markdown(STATUS_LABEL[r["status"]])
    row[4].write(r["checked_at"])

# ---- details ----
st.divider()
st.subheader("Device details")
selected = st.selectbox("Choose a device", [r["name"] for r in results])
current = next(r for r in results if r["name"] == selected)

st.markdown(f"Status: {STATUS_LABEL[current['status']]}")
if current["status"] == "ERROR":
    st.error(f"Could not collect the config: {current['error']}")

tab_diff, tab_current, tab_golden = st.tabs(
    ["Differences", "Current config", "Golden config"]
)
with tab_diff:
    if current["status"] == "DRIFT":
        lines = [f"- {line}" for line in current["removed"]]
        lines += [f"+ {line}" for line in current["added"]]
        st.code("\n".join(lines), language="diff")
    elif current["status"] == "OK":
        st.success("The running config matches the golden config.")
    elif current["status"] == "NO_GOLDEN":
        st.warning("No golden config yet. Approve the current config to create it.")
with tab_current:
    st.code(read_config(BACKUP_DIR, selected), language="text")
with tab_golden:
    st.code(read_config(GOLDEN_DIR, selected), language="text")

# ---- approve ----
st.subheader("Approve")
can_approve = current["status"] in ("DRIFT", "NO_GOLDEN")
confirm = st.checkbox(
    "I confirm that the current config is correct and becomes the new golden config",
    key=f"confirm_{selected}",
    disabled=not can_approve,
)
st.button(
    "Approve as golden",
    disabled=not (can_approve and confirm),
    on_click=do_approve,
    args=(selected,),
)