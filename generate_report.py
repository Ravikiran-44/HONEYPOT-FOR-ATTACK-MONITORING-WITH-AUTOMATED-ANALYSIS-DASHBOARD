# generate_report.py
# Read the latest session meta.json and produce a concise console summary + OUTPUT.md
import pathlib, json, time, hashlib, textwrap, sys

DATA = pathlib.Path("data/sessions")
if not DATA.exists():
    print("No data/sessions folder found.")
    sys.exit(1)

sessions = sorted(DATA.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
if not sessions:
    print("No sessions found.")
    sys.exit(1)

latest = sessions[0]
meta_file = latest / "meta.json"
if not meta_file.exists():
    print("meta.json missing for", latest)
    sys.exit(1)

meta = json.loads(meta_file.read_text(encoding="utf-8"))

def human_time(ts):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return str(ts)

# Summary fields
session_id = meta.get("session_id")
src_ip = meta.get("src_ip")
src_port = meta.get("src_port")
events = meta.get("events", [])

# Extract useful markers
labels = []
payloads = []
engagements = []
commands = []
for ev in events:
    t = ev.get("text","")
    if t.startswith("[CLASS]="):
        labels.append(t)
    if t.startswith("[PAYLOAD_SAVED]="):
        # payload saved entry may be dict-as-string
        payloads.append(t)
    if "ENG=" in t or t.startswith("[HIGH_ENGAGEMENT]") or t.startswith("[ACTION]"):
        engagements.append(t)
    # attacker commands inside high engagement prefixed by "ATTACKER_CMD" in our logs
    if "ATTACKER_CMD" in t or t.endswith("ls -la") or t.endswith("whoami"):
        commands.append(t)
    # also capture raw lines that look like commands (simple heuristic)
    if not t.startswith("[") and ("wget " in t or "curl " in t or "ssh " in t or "ls " in t):
        commands.append(t)

# Build a small report
lines = []
lines.append(f"# Latest Session Report — {session_id}")
lines.append(f"- Source: {src_ip}:{src_port}")
lines.append(f"- Events recorded: {len(events)}")
lines.append(f"- Time window: {human_time(events[0]['ts'])}  to  {human_time(events[-1]['ts']) if events else 'N/A'}")
lines.append("")
lines.append("## Classifier labels (AI outputs)")
if labels:
    for L in labels:
        lines.append(f"- {L}")
else:
    lines.append("- (none)")

lines.append("")
lines.append("## Engagement actions")
if engagements:
    for e in engagements:
        lines.append(f"- {e}")
else:
    lines.append("- (none)")

lines.append("")
lines.append("## Payload captures (forensic evidence)")
if payloads:
    for p in payloads:
        # try to extract JSON-like dict
        try:
            raw = p.split("=",1)[1].strip()
            if raw.startswith("{"):
                js = json.loads(raw.replace("'", '"'))
                lines.append(f"- file: {js.get('file')}  size: {js.get('size')}  sha256: {js.get('sha256')}")
            else:
                lines.append(f"- {raw}")
        except Exception:
            lines.append(f"- {p}")
else:
    lines.append("- (none)")

lines.append("")
lines.append("## Sample captured attacker commands")
if commands:
    for c in commands[:10]:
        lines.append(f"- {c}")
else:
    lines.append("- (none)")

# Context blurb describing novelty (for viva)
lines.append("")
lines.append("## Why this matters (auto-snippet)")
lines.append(textwrap.fill(
    "This session shows automatic AI classification (labels above), adaptive engagement (hand-off to high engagement), "
    "and forensic evidence capture (payloads saved with SHA256 metadata). These are the project's key innovations.",
    width=80
))

# Print to console
report_text = "\n".join(lines)
print(report_text)

# Write OUTPUT.md
out = pathlib.Path("OUTPUT.md")
out.write_text(report_text, encoding="utf-8")
print("\nWrote OUTPUT.md — open it in VS Code to present or copy-paste into slides.")
