# 🔍 Verify Atomic CSV Writes — Bulletproof Dashboard Proof

Your dashboard now has **atomic CSV writes** with real-time verification. Here's how to prove it's working:

---

## ✅ Step 1: Check the Sidebar (Easiest)

Open the dashboard at **http://localhost:8501**

Look in the **left sidebar** for:

```
📊 CSV File Status
✅ File exists
📝 Path: `honeypot_sessions.csv`
⏰ Last updated: `2025-11-11 14:26:13`
📏 Size: `8,120` bytes
```

This section updates every time Streamlit reruns. It **proves** the CSV file is fresh.

---

## ✅ Step 2: One-Time Verification (Quick Check)

Run this command to check if the CSV is valid and recently written:

```powershell
cd C:\project
python check_csv_writes.py
```

**Expected output:**
```
📊 CSV Atomic Write Verification
======================================================================
✅ PASS: CSV file exists
✅ PASS: File size: 8,120 bytes
✅ PASS: Recently updated (253s ago): 2025-11-11 14:21:23
✅ PASS: Valid CSV with 50 rows, 8 columns
✅ PASS: All required columns present
✅ PASS: 50/50 sessions have country data

🎯 SUMMARY: CSV is being written correctly by the dashboard!
   The atomic write function is working as expected.
```

---

## ✅ Step 3: Watch It Happen (Real-Time Monitor)

Run this script in a separate PowerShell terminal while the dashboard is running:

```powershell
cd C:\project
python verify_csv_writes.py
```

**What you'll see:**
```
🔍 CSV File Freshness Monitor
============================================================
Watching: C:\project\output\honeypot_sessions.csv
Updates every 2 seconds. Press Ctrl+C to stop.

✅ [  1] 2025-11-11 14:26:13 |    8,120 bytes
✅ [  2] 2025-11-11 14:26:13 |    8,120 bytes
✅ [  3] 2025-11-11 14:26:13 |    8,120 bytes
✅ [  4] 2025-11-11 14:26:15 |    8,100 bytes 🔄 UPDATED!
✅ [  5] 2025-11-11 14:26:15 |    8,100 bytes
```

When you see **"🔄 UPDATED!"** — that's the atomic write function firing!

---

## ✅ Step 4: File Timestamp Check (PowerShell)

```powershell
(Get-Item output/honeypot_sessions.csv).LastWriteTime
```

**Output:**
```
Monday, November 11, 2025 2:26:13 PM
```

Run this multiple times. The timestamp should stay fresh whenever:
- Dashboard starts
- VM produces new sessions
- You run `python generate_demo_data.py`

---

## ✅ Step 5: Trigger a Write & See It Update

**Test 1: Restart the dashboard**
```powershell
Stop-Process -Name streamlit -Force
cd C:\project
streamlit run app_auto.py
# Watch the sidebar — it will show a fresh timestamp
```

**Test 2: Generate new demo data**
```powershell
cd C:\project
python generate_demo_data.py
# The dashboard auto-reloads and updates the sidebar timestamp
```

**Test 3: Monitor file in real-time**
```powershell
# In one terminal:
cd C:\project
python verify_csv_writes.py

# In another terminal:
python generate_demo_data.py
# Watch the first terminal — you'll see "🔄 UPDATED!"
```

---

## 🎯 What Proves It's Working?

| Check | Proof |
|-------|-------|
| **Sidebar shows timestamp** | ✅ File is being read and mtime is current |
| **`check_csv_writes.py` passes** | ✅ CSV is valid and recently written |
| **`verify_csv_writes.py` shows 🔄 UPDATED** | ✅ File changed (atomic write happened) |
| **Dashboard auto-reloads** | ✅ Watcher detected mtime change |
| **LastWriteTime updates** | ✅ OS confirms file was modified |

---

## 🔧 How It Works (Under the Hood)

1. **Dashboard starts** → calls `load_vm_sessions()` to read from `data/sessions/*/meta.json`
2. **Data normalized** → `normalize_honeypot_data()` canonicalizes columns
3. **GeoIP enriched** → `enrich_geo()` adds country codes
4. **Atomic write** → `_atomic_write_csv()` writes to temp file, then atomically replaces `output/honeypot_sessions.csv`
5. **Watcher triggered** → `maybe_reload_from_csv()` detects mtime change, calls `st.experimental_rerun()`
6. **Dashboard reloads** → sidebar shows fresh timestamp
7. **No corruption** → atomic replace means no partial/corrupt files

---

## ⚠️ If It's NOT Working

1. Check permissions: `output/` directory must be writable
2. Check VM sessions: `data/sessions/S-*/meta.json` must exist and have valid JSON
3. Check sidebar warning: Look for "Failed to write canonical CSV…" or "CSV write exception:"
4. Run `check_csv_writes.py` — it will show exactly what's wrong

---

## 📝 Key Files

- **`app_auto.py`** — Main dashboard with atomic write integration
- **`_atomic_write_csv()`** — The atomic write function (lines ~195-220)
- **`verify_csv_writes.py`** — Real-time file freshness monitor
- **`check_csv_writes.py`** — One-time validation script
- **`output/honeypot_sessions.csv`** — The file being verified

---

**TL;DR:** Open the dashboard, look at the sidebar — if you see a recent timestamp next to "Last updated", the atomic writes are working. ✅
