# 🔥 QUICK REFERENCE — Internet Exposure Setup

## ✅ COMPLETED (Agent Did This)

```
✅ Vagrantfile updated with:
   - Static IP: 192.168.56.50
   - Port forward: 2222→2222
   
✅ VM reloaded with new network config

✅ Honeypot started and listening on port 2222
   (verified with netstat)

✅ Shared folder synced
```

---

## 🚨 YOUR TURN (YOU DO THIS NOW)

### **STEP 1: Configure Your Router**

**Time needed:** 5 minutes

1. Find your router gateway IP:
   - Usually: `192.168.1.1` or `192.168.0.1`
   - To be sure, open PowerShell and run:
     ```powershell
     ipconfig | Select-String "Default Gateway"
     ```

2. Open in browser: `http://[YOUR-GATEWAY-IP]`
   - Login (default: admin/admin or check your router label)

3. Find **Port Forwarding** (exact location varies by brand):
   - **TP-Link**: Advanced → NAT → Port Forwarding
   - **ASUS**: WAN → Port Forwarding
   - **Netgear**: Advanced → Port Forwarding
   - **Linksys**: Advanced → Port Forwarding

4. Add new rule:
   ```
   External Port: 2222
   Internal IP: 192.168.56.50
   Internal Port: 2222
   Protocol: TCP
   ```

5. **Save and REBOOT the router** (important!)

**See:** `C:\project\INTERNET_EXPOSURE_GUIDE.md` for detailed instructions per router model

---

### **STEP 2: Verify Your Exposure (5 minutes)**

1. Find your public IP: https://www.whatismyip.com
2. Go to: https://canyouseeme.org/
3. Enter: `2222`
4. Click: "Check Port"

**Expected result:**
```
Success: I can see your service on port 2222
```

If you see error → go back to STEP 1, check port forwarding setup

---

### **STEP 3: Wait for Real Attackers (5 min to 2 hours)**

Real attack traffic will arrive automatically. You will see new folders:

```
C:\project\data\sessions\
├── S-1762797430\         ← First real attacker
├── S-1762797555\         ← Second attacker
├── S-1762797890\         ← Third attacker
└── ...
```

**To monitor in real-time, run:**

```powershell
cd C:\project
.\monitor_attacks.ps1
```

This shows each new attack as it arrives with attacker IP and event count.

---

### **STEP 4: View Real Attacks on Dashboard**

```powershell
cd C:\project
.\.venv\Scripts\python.exe -m streamlit run src/app_auto.py
```

Open: http://127.0.0.1:8501

You will see:
- Real attacker IP addresses
- Real countries (GeoIP)
- Real malware samples
- Attack classifications
- Incident response actions

---

## 📋 Checklist Before You Start

- [ ] I know my router gateway IP (192.168.x.x)
- [ ] I have admin password for my router
- [ ] I found the Port Forwarding section in my router
- [ ] I understand the safety (VM is isolated, only port 2222 open)
- [ ] I have the reset procedure memorized:
  ```powershell
  vagrant destroy -f
  vagrant up
  ```

---

## 🎯 Expected Timeline

| Time | What Happens |
|------|--------------|
| **Now** | You configure router |
| **5 min after** | Port forward test passes (canyouseeme.org) |
| **5-15 min after** | First Mirai botnet probes appear |
| **15-60 min** | Password brute-force attempts |
| **1+ hour** | Malware delivery attempts, wget/curl |
| **2-24 hours** | Sophisticated exploitation attempts |

---

## ⚡ Critical Safety Rules

✅ **SAFE because:**
- VM is network-isolated from Windows
- Only port 2222 is exposed
- Everything else is firewalled
- Attacker sees fake Ubuntu, not your real system

❌ **DANGEROUS (DO NOT DO):**
- ❌ Expose port 22 (SSH) — attracts aggressive botnets
- ❌ Expose Windows directly — you WILL get hacked
- ❌ Use bridged networking — your PC is on same network as attackers
- ❌ Share Windows home folder with VM

---

## 🚨 If Anything Goes Wrong

VM gets wrecked? Easy fix:

```powershell
cd C:\project
vagrant destroy -f
vagrant up
```

VM is completely rebuilt. Your Windows is untouched.

---

## 💬 Next: What Do You Want?

After you complete the above steps and attacks start arriving, let me know if you want:

1. **Telegram alerts** when attackers hit (real-time notifications)
2. **More attackers** (add Telnet/HTTP honeypots on different ports)
3. **Fake services** (pretend to be CCTV, router, IoT device)
4. **Auto-export reports** (daily Excel/PDF of all attacks)

---

**YOU'RE NOW READY TO EXPOSE TO THE INTERNET** 🔥

Once your router is configured and canyouseeme.org test passes, real hacker traffic will start flowing in automatically.

Your dashboard will show **real attack data from real attackers** within hours.

