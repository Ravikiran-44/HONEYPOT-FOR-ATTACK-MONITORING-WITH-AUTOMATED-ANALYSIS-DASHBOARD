# 🔥 **COMPLETE INTERNET EXPOSURE GUIDE FOR HONEYPOT**

## **Status: STEPS 1-3 COMPLETE ✅**

Your honeypot is now:
- ✅ **Running** on the VM (listening on 0.0.0.0:2222 inside VM)
- ✅ **Port forwarded** by Vagrant (127.0.0.1:2222 on Windows)
- ✅ **Ready to receive traffic** from the internet

---

## **STEP 4 — CONFIGURE YOUR ROUTER (CRITICAL)**

### **Your Mission:**
Add a **Port Forward rule** so internet traffic on **your public IP:2222** reaches **your VM at 192.168.56.50:2222**

---

## **ROUTER CONFIGURATION BY MODEL**

### **OPTION A: TP-Link Router (Most Common)**

1. Open browser: `http://192.168.0.1` or `http://192.168.1.1`
2. Login (default: admin/admin)
3. Go to: **Advanced** → **NAT** → **Port Forwarding**
4. Add a new rule:
   | Field | Value |
   | --- | --- |
   | **Service Port** | 2222 |
   | **IP Address** | 192.168.56.50 |
   | **Internal Port** | 2222 |
   | **Protocol** | TCP |

5. **Save** → **Reboot router**

---

### **OPTION B: ASUS Router**

1. Open: `http://192.168.1.1`
2. Login (default: admin/admin)
3. Go to: **WAN** → **Port Forwarding** (or **Advanced** → **Port Triggering**)
4. Enable Port Forwarding
5. Add rule:
   | Field | Value |
   | --- | --- |
   | **Service Name** | Honeypot2222 |
   | **Port Range** | 2222 |
   | **IP Address** | 192.168.56.50 |
   | **Local Port** | 2222 |
   | **Protocol** | TCP |

6. **Apply** → **Reboot**

---

### **OPTION C: Netgear / Linksys**

1. Open: `http://192.168.1.1`
2. Login
3. Go to: **Advanced** → **Port Forwarding/Port Triggering**
4. Enable it
5. External Port: `2222`
6. Internal IP: `192.168.56.50`
7. Internal Port: `2222`
8. Protocol: `TCP`
9. **Save** → **Reboot**

---

### **OPTION D: Default Netgear**

1. `http://192.168.1.1`
2. Go to: **Advanced** → **Port Forwarding**
3. Service Type: **TCP**
4. External Port: **2222**
5. Internal IP: **192.168.56.50**
6. Internal Port: **2222**
7. **Apply**

---

### **IF YOU DON'T KNOW YOUR ROUTER GATEWAY:**

Open PowerShell:

```powershell
ipconfig | Select-String "Default Gateway"
```

Copy that IP (usually 192.168.1.1 or 192.168.0.1) → paste in browser

---

## **STEP 5 — VERIFY PUBLIC EXPOSURE**

### **Find Your Public IP:**

1. Go to: https://www.whatismyip.com OR https://www.google.com (search "my ip")
2. Copy your IP (e.g., `203.45.67.89`)

### **Test Your Port:**

1. Go to: https://canyouseeme.org/
2. Enter: `2222`
3. Click: **Check Port**

**You MUST see:**
```
Success: I can see your service on port 2222
```

**If you see ERROR:**
- Router forwarding is wrong → check steps above
- Router is blocking port → try different port (like 22222 → forward to 2222)
- ISP blocking port 2222 → try port 80 or 443 (need firewall change)

---

## **STEP 6 — REAL ATTACKS ARRIVE (PATIENCE REQUIRED)**

### **Timeline:**

- **5-15 minutes**: Mirai bots start probing
- **15-60 minutes**: Password brute-force attempts
- **1-2 hours**: Wget/Curl malware delivery
- **2-24 hours**: More sophisticated intrusions

### **What You'll See:**

New folders appear in `C:\project\data\sessions\`:

```
data/sessions/
├── S-1762797430/
│   ├── meta.json          ← Real attacker metadata
│   ├── payload.bin        ← Captured malware
│   ├── sessions.csv       ← Event log
│   └── ...
├── S-1762797555/          ← Next attack (different attacker)
├── S-1762797890/
└── ...
```

Each folder = **ONE REAL ATTACKER SESSION**

---

## **STEP 7 — VIEW REAL ATTACKS ON DASHBOARD**

### **On Windows, in your project folder:**

```powershell
cd C:\project
.\.venv\Scripts\python.exe -m streamlit run src/app_auto.py
```

Open: http://127.0.0.1:8501

**You will see:**

✅ Real attacker IP addresses
✅ Real countries (GeoIP)
✅ Real commands executed
✅ Real malware files captured
✅ Attack type AI classification
✅ High-engagement shell behavior
✅ Professional incident response playbooks

---

## **STEP 8 — SAFETY CHECKLIST (MUST READ)**

### ✅ **You Are SAFE Because:**

- VM is **isolated** from Windows filesystem
- Only port **2222 is exposed** (not 22, not 80, not your entire network)
- Honeypot runs in **VM** with disposable filesystem
- Attackers can't reach your Windows machine
- Shared folder is **read-only** to the honeypot

### ❌ **NEVER DO THIS:**

- ❌ Forward port 22 (SSH) — attracts **aggressive botnets**
- ❌ Forward port 80/443 (HTTP) — your whole network gets scanned
- ❌ Make /home/vagrant/project writable — malware could escape
- ❌ Share your Windows home directory to VM
- ❌ Expose Windows directly (bridged network) — **YOU WILL GET HACKED**

### ✅ **RESET PROCEDURE (IF VM GETS WRECKED):**

If the VM somehow becomes unusable:

```powershell
cd C:\project
vagrant destroy -f
vagrant up
```

VM is **completely rebuilt** from clean Ubuntu image. Your Windows is unaffected.

---

## **MONITORING COMMANDS**

### **Watch for new attack sessions (PowerShell):**

```powershell
while ($true) {
    Get-ChildItem C:\project\data\sessions -Directory | 
    Sort-Object CreationTime -Descending | 
    Select-Object -First 5 |
    ForEach-Object { Write-Host "$($_.Name) - $(Get-Date $_.CreationTime)" }
    Start-Sleep -Seconds 30
    Clear-Host
}
```

### **Show latest session details (PowerShell):**

```powershell
cd C:\project
$latest = (Get-ChildItem data\sessions -Directory | Sort-Object CreationTime -Descending | Select-Object -First 1).FullName
if ($latest) {
    Get-Content "$latest\meta.json" | ConvertFrom-Json | Format-List
}
```

### **Count total attacks so far:**

```powershell
(Get-ChildItem C:\project\data\sessions -Directory).Count
```

---

## **OPTIONAL ENHANCEMENTS**

If you want MORE attackers (more interesting data), I can add:

### 🔴 **Telnet Honeypot (port 23)**
- Mirai loves Telnet
- Gets 10x more traffic than SSH

### 🔴 **HTTP Honeypot (port 80)**
- Scanners hit this immediately
- Fake CCTV login portals
- Fake WordPress installations

### 🔴 **DNS Honeypot (port 53)**
- Domain enumeration attempts
- DNS poisoning tests

### 🔴 **Weak Credential Simulation**
- username/password: `admin/admin`, `root/root`, `pi/raspberry`
- Attracts brute-force attempts

### 🔴 **Fake IoT Device Identity**
- Pretend to be Hikvision CCTV
- Fake D-Link router
- Fake Ubiquiti device

---

## **NEXT STEPS**

1. **TODAY**: Configure router port forward → test with canyouseeme.org
2. **TONIGHT**: Wait for first attacks (5 min to 2 hours)
3. **TOMORROW**: View real session data on dashboard
4. **THIS WEEK**: Analyze attack patterns

---

## **TROUBLESHOOTING**

### **Problem: canyouseeme.org says "Connection refused"**

**Solution:**
1. Did you reboot the router after adding the forward rule? (Required!)
2. Wrong internal IP? Check VM IP is actually 192.168.56.50
3. Router doesn't support port forwarding? (Rare, but some ISP routers block this)

Try: Restart router, wait 2 minutes, test again.

### **Problem: No attacks appearing after 1 hour**

**Solution:**
1. Port forward might not be working (re-test canyouseeme.org)
2. Honeypot might have crashed (check with `ps aux | grep run_honeypot` on VM)
3. Mirai/scanners haven't found you yet (patience)

### **Problem: Attacks appearing but not showing in dashboard**

**Solution:**
1. Restart Streamlit dashboard
2. Check `data/sessions/` folder exists and has new S-XXXXX folders
3. Make sure shared folder is still mounted: `vagrant ssh -c "ls /home/vagrant/project/data/sessions"`

---

## **FINAL CHECKLIST BEFORE GOING PUBLIC**

- [ ] Vagrantfile has `config.vm.network "private_network", ip: "192.168.56.50"`
- [ ] Vagrantfile has `config.vm.network "forwarded_port", guest: 2222, host: 2222`
- [ ] Router port forward: External 2222 → Internal 192.168.56.50:2222
- [ ] canyouseeme.org test: ✅ "Success: I can see your service on port 2222"
- [ ] Honeypot running in VM (no errors)
- [ ] Streamlit dashboard working on 127.0.0.1:8501
- [ ] You understand VM isolation (read safety checklist)
- [ ] You have reset procedure memorized (vagrant destroy -f; vagrant up)

---

**YOU ARE NOW READY FOR REAL INTERNET ATTACKS** 🔥

Once canyouseeme.org test passes and router is configured, your honeypot will start collecting real attacker sessions within minutes.

