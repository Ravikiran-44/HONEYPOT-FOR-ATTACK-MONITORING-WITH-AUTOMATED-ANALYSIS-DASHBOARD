# ✅ **DEPLOYMENT CHECKLIST & QUICK START**

---

## **PRE-DEPLOYMENT (Agent Completed)**

### Infrastructure ✅

- [x] Vagrantfile updated (static IP 192.168.56.50)
- [x] Port forwarding configured in Vagrantfile (2222→2222)
- [x] VM reloaded successfully
- [x] Honeypot service started
- [x] Dependencies installed (joblib, paramiko, etc.)
- [x] Shared folder synced and operational
- [x] Port 2222 listening: `netstat -an | Select-String "2222"` ✅

### Documentation ✅

- [x] 00_READ_ME_FIRST.md (main summary)
- [x] START_HERE.md (3-step visual guide)
- [x] INTERNET_EXPOSURE_GUIDE.md (router setup by brand)
- [x] QUICK_START_INTERNET.md (quick reference)
- [x] DEPLOYMENT_STATUS.md (technical details)
- [x] COMPLETE_STATUS.md (full report)
- [x] QUICK_SUMMARY.md (one-page overview)
- [x] INDEX.md (navigation)
- [x] BLUEPRINT.md (from zero to live)
- [x] README.md (updated)

### Tools ✅

- [x] get_router_ip.ps1 (auto-detect router IP)
- [x] monitor_attacks.ps1 (live attack monitor)
- [x] run_all.ps1 (launcher script)

---

## **STEP 1: CONFIGURE ROUTER (Do This Now)**

### [ ] Find Your Router

```powershell
cd C:\project
.\get_router_ip.ps1
```

Output: `Your Default Gateway: 192.168.1.1` (or 192.168.0.1)

### [ ] Open Router Admin

```
Open browser: http://192.168.1.1
Login: admin / admin (or your password)
```

### [ ] Find Port Forwarding Section

**By Router Brand:**

- **TP-Link**: Advanced → NAT → Port Forwarding
- **ASUS**: WAN → Port Forwarding  
- **Netgear**: Advanced → Port Forwarding
- **Linksys**: Advanced → Port Forwarding
- **Other**: Look for "Port Forwarding", "NAT", or "Virtual Server"

**If stuck:** Open `INTERNET_EXPOSURE_GUIDE.md` (find your exact model)

### [ ] Add Port Forward Rule

```
External Port: 2222
Internal IP: 192.168.56.50
Internal Port: 2222
Protocol: TCP
Enabled: YES
```

### [ ] Save and Reboot Router

```
Click: SAVE (or APPLY)
Wait: Router reboots (2-3 minutes)
```

✅ **STEP 1 COMPLETE when router lights stop blinking**

---

## **STEP 2: TEST EXPOSURE (Do This After Router Reboots)**

### [ ] Get Your Public IP

Open: https://www.whatismyip.com  
Copy your IP (e.g., 203.45.67.89)

### [ ] Test With canyouseeme.org

1. Go to: https://canyouseeme.org/
2. Enter: `2222`
3. Click: "Check Port"

### [ ] Verify Success

**Expected Result:**
```
Success: I can see your service on port 2222 on 203.45.67.89
```

**If error:**
- Port forward is wrong → Check router settings
- Router needs more time → Wait 5 minutes and retry
- ISP blocking port → Contact ISP or try different port

✅ **STEP 2 COMPLETE when test shows "Success"**

---

## **STEP 3: MONITOR REAL ATTACKS (Automatic)**

### [ ] Start Live Monitor

```powershell
cd C:\project
.\monitor_attacks.ps1
```

**Expected Output (within 5 min to 2 hours):**

```
[14:32:01] ⚠️  NEW ATTACK(S) DETECTED! (1 new)
  ➤ S-1762797430 from 203.45.67.89:55184 with 8 events
```

### [ ] Verify New Session Folders

```powershell
Get-ChildItem C:\project\data\sessions -Directory | 
Sort-Object CreationTime -Descending | 
Select-Object -First 5
```

Should show new **S-XXXXXXX** folders (not just old ones)

### [ ] View Latest Attack

```powershell
$latest = (Get-ChildItem C:\project\data\sessions -Directory | 
           Sort-Object CreationTime -Descending | 
           Select-Object -First 1).FullName
Get-Content "$latest\meta.json" | ConvertFrom-Json | Format-List
```

Should show **real attacker IP** (not 127.0.0.1)

✅ **STEP 3 COMPLETE when you see real attack data**

---

## **STEP 4: VIEW ON DASHBOARD**

### [ ] Start Streamlit

```powershell
cd C:\project
.\.venv\Scripts\python.exe -m streamlit run src/app_auto.py
```

### [ ] Open Dashboard

```
Browser: http://127.0.0.1:8501
```

### [ ] Verify Real Data

Should show:
- [ ] Real attacker IPs
- [ ] Real countries (GeoIP)
- [ ] Real commands
- [ ] Real malware samples
- [ ] AI classifications

✅ **DEPLOYMENT COMPLETE when dashboard shows real attacks**

---

## **EXPECTED TIMELINE**

| Time | Action | Status |
|------|--------|--------|
| T+0 | Read this checklist | 📄 |
| T+5 | Configure router | 🚀 |
| T+10 | Test canyouseeme.org | ✅ |
| T+15 | First Mirai probes hit | 🚨 |
| T+30 | Password brute-force | 💥 |
| T+1h | Malware delivery | 📥 |
| T+2h | Real shell interaction | 🔥 |
| T+6h | Multiple attacks visible | 📊 |
| T+24h | Rich attack dataset | ✨ |

---

## **TROUBLESHOOTING**

### Router Port Forward Not Working

**Problem:** canyouseeme.org says "Connection refused"

**Solution:**
1. Verify rule in router (IP should be 192.168.56.50)
2. Reboot router again (rules take time to activate)
3. Check VM is running: `vagrant ssh` (should connect)
4. Check VM IP: `vagrant ssh -c "hostname -I"` (should show 192.168.56.50)

### No Attacks After 2 Hours

**Problem:** Monitor shows 0 attacks, no new folders

**Solution:**
1. Verify canyouseeme.org test passes
2. Check honeypot is listening: `netstat -an | Select-String "LISTENING" | Select-String "2222"`
3. SSH to VM and check: `vagrant ssh -c "ps aux | grep run_honeypot"`

### Dashboard Shows Old Data

**Problem:** Streamlit not updating with new attacks

**Solution:**
1. Restart Streamlit (Ctrl+C and rerun)
2. Check shared folder: `vagrant ssh -c "ls /home/vagrant/project/data/sessions/" | wc -l`
3. Clear browser cache (Ctrl+Shift+Delete)

### VM Crashed

**Problem:** Can't SSH into VM

**Solution (Emergency Reset):**
```powershell
cd C:\project
vagrant destroy -f
vagrant up
```

**Result:** 
- VM completely rebuilt (clean Ubuntu image)
- Takes ~3 minutes
- Windows untouched
- All attack data in C:\project\data\sessions preserved

---

## **QUICK COMMAND REFERENCE**

### Essential Commands

```powershell
# Find router IP
.\get_router_ip.ps1

# Monitor live attacks
.\monitor_attacks.ps1

# View latest attack
$latest = (Get-ChildItem C:\project\data\sessions -Directory | Sort-Object CreationTime -Descending | Select-Object -First 1).FullName; Get-Content "$latest\meta.json" | ConvertFrom-Json | Format-List

# Count attacks
(Get-ChildItem C:\project\data\sessions -Directory).Count

# Start dashboard
.\.venv\Scripts\python.exe -m streamlit run src/app_auto.py

# SSH to VM
vagrant ssh

# Restart VM
vagrant reload

# Reset VM (emergency)
vagrant destroy -f; vagrant up
```

### Testing Commands

```powershell
# Check if port 2222 is listening
netstat -an | Select-String "2222"

# Verify shared folder
vagrant ssh -c "ls /home/vagrant/project/data/sessions/"

# Check honeypot running
vagrant ssh -c "ps aux | grep run_honeypot"
```

---

## **DOCUMENTATION QUICK REFERENCE**

| File | Purpose | Read Time |
|------|---------|-----------|
| `00_READ_ME_FIRST.md` | Full deployment report | 20 min |
| `START_HERE.md` | Visual 3-step guide | 5 min |
| `QUICK_SUMMARY.md` | One-page overview | 3 min |
| `INTERNET_EXPOSURE_GUIDE.md` | Router setup (by brand) | 10 min |
| `QUICK_START_INTERNET.md` | Quick reference | 2 min |
| `BLUEPRINT.md` | Zero to live honeypot | 10 min |
| `DEPLOYMENT_STATUS.md` | Technical details | 15 min |
| `COMPLETE_STATUS.md` | Full technical report | 20 min |
| `INDEX.md` | Navigation guide | 2 min |

---

## **SUCCESS CHECKLIST**

- [ ] **STEP 1 Complete:** Router port forwarding configured and router rebooted
- [ ] **STEP 2 Complete:** canyouseeme.org test shows "Success"
- [ ] **STEP 3 Complete:** New attack folder appears in data/sessions/
- [ ] **STEP 4 Complete:** Dashboard displays real attacker data

**All 4 steps complete = Honeypot is live!** 🔥

---

## **OPTIONAL ENHANCEMENTS** (After Attacks Start)

Ask for:

- **Telegram Alerts** — Real-time push notifications
- **More Honeypots** — HTTP (80), Telnet (23), DNS (53)
- **Fake Services** — CCTV, router, IoT device identities
- **Auto-Reports** — Daily Excel/PDF summaries
- **Advanced Analysis** — ML-based attack pattern detection

---

## **🎯 YOU ARE HERE**

```
✅ Agent: Setup complete
✅ Infrastructure: Running
✅ Documentation: Ready

🚨 YOU: Configure router (THIS CHECKLIST)
🚨 YOU: Test exposure (2 min)
⏳ AUTOMATIC: Attacks arrive (5 min-2 hours)
✅ DASHBOARD: Shows real data

Expected completion: 20 minutes total
Expected first attacks: Within 1 hour
```

---

## **NEXT IMMEDIATE ACTION**

1. **Open this checklist**
2. **Find your router IP:** `.\get_router_ip.ps1`
3. **Open INTERNET_EXPOSURE_GUIDE.md** (find your router brand)
4. **Follow the exact steps for your router**
5. **Test with canyouseeme.org**
6. **Watch monitor_attacks.ps1**

---

**Everything is ready. Go configure your router!** 🔥

