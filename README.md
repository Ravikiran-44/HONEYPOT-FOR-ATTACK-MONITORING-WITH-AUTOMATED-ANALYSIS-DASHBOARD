
## 🛡️ Honeypot for Attack Monitoring with Automated Analysis Dashboard

**Developer:** Ravikiran.U
**Stack:** Python • Streamlit • Pandas • NumPy • VM-based Honeypot • Automated Analysis

---

## 🚀 Project Overview

This project implements a **honeypot-based attack monitoring system** designed to capture, analyze, and visualize real-world cyber attack behavior within a controlled environment.

The system deploys **intentionally exposed honeypot services inside a virtual machine**, records attacker interactions at the **session level**, validates and preprocesses the collected data, and performs **automated attack analysis** using rule-based and AI-ready logic.
All analyzed results are presented through an **interactive Streamlit dashboard**, enabling clear forensic inspection and actionable security insights.

---

## ⚙️ Architecture Overview

| Phase | Name                | Description                                                   |
| ----- | ------------------- | ------------------------------------------------------------- |
| 1     | Honeypot Deployment | Vulnerable services deployed inside a VM to attract attackers |
| 2     | Session Capture     | Attacker interactions captured as structured session logs     |
| 3     | Data Validation     | Integrity checks and session verification                     |
| 4     | Automated Analysis  | Attack classification and behavior analysis                   |
| 5     | Visualization       | Analytical insights displayed via Streamlit dashboard         |

---

## 🧩 Technologies Used

| Layer                | Tools / Libraries                     |
| -------------------- | ------------------------------------- |
| Honeypot Environment | VirtualBox / Vagrant                  |
| Backend Processing   | Python                                |
| Data Handling        | pandas, numpy                         |
| Analysis Logic       | Rule-based logic with ML-ready design |
| Visualization        | Streamlit                             |
| Data Storage         | CSV-based session datasets            |
| Testing & Validation | pytest                                |

---

## 📦 Project Setup

### Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🧰 requirements.txt

```
pandas
numpy
streamlit
pytest
geoip2
```

---

## 🧠 Phase-Wise Execution Guide

### 🔹 Phase 1: Honeypot Execution

Runs the honeypot services inside a virtual machine to capture attacker interactions.

**Output structure:**

```
data/sessions/
 ├─ <session_id>/
 │   ├─ meta.json
 │   ├─ payload_*.bin
```

---

### 🔹 Phase 2: Session Validation

Validates captured data and removes incomplete or corrupted sessions.

```bash
python verify_meta_integrity.py
```

Only verified sessions are forwarded for analysis.

---

### 🔹 Phase 3: Data Processing & Enrichment

Converts raw session data into a structured dataset and enriches it with metadata.

```bash
python merge_sessions.py
```

**Output:**

```
output/honeypot_sessions.csv
```

---

### 🔹 Phase 4: Automated Attack Analysis

Applies analytical logic to identify:

* Attack types
* Suspicious behavior
* Session-level patterns

```bash
python generate_report.py
```

**Output includes:**

* Automated attack insights
* Summary statistics
* Evidence-ready analytical reports

---

### 🔹 Phase 5: Visualization & Dashboard

Launches the interactive Streamlit dashboard.

```bash
streamlit run streamlit_app.py
```

**Dashboard Features:**

* Top attacker IPs
* Attack type distribution
* Port usage analysis
* Time-series attack trends
* Geographic attack visualization
* Downloadable charts and reports

---

## 🖥️ Streamlit Dashboard

**Key Highlights:**

* Automatic graph generation
* Live monitoring of processed session data
* Clean and readable user interface
* Export to Excel and PNG formats
* Evidence-focused security insights

The dashboard strictly reads data from:

```
output/honeypot_sessions.csv
```

---

## 🧑‍💻 Recruiter Highlights

* Real-world attack monitoring
* VM-based honeypot deployment
* Automated intrusion analysis
* Session-level forensic evidence
* Interactive analytics dashboard
* Final-year project ready

---

## 🧩 Example Use Case

1. Honeypot VM is deployed
2. Attackers interact with exposed services
3. Sessions are logged and validated
4. Automated analysis detects attack patterns
5. Dashboard visualizes threats and trends

---

## 🧠 Future Enhancements

* Machine learning–based anomaly detection
* Multi-honeypot correlation
* Real-time alert generation
* Advanced attacker profiling

---

## 🏁 Author

**Ravikiran.U**

AI & Data Science | Cybersecurity & Networking Enthusiast

🔗 LinkedIn: [https://www.linkedin.com/in/ravikiranumapathy](https://www.linkedin.com/in/ravikiranumapathy)

---

⚡ **“Monitor the Attack. Analyze the Behavior. Strengthen the Defense.”** ⚡



