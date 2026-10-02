# 🏛️ CivicLens AI
> **Autonomous Civic Infrastructure Triage, Geo-Clustered Deduplication & AI Resolution Auditor**

[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2024-orange?style=flat&logo=hacktoberfest)](https://hacktoberfest.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AI Engine](https://img.shields.io/badge/AI-Google%20Gemini%20Vision-blue)](https://ai.google.dev/)
[![Geospatial](https://img.shields.io/badge/Maps-OpenStreetMap%20%2B%20Leaflet-green)](https://leafletjs.com/)

CivicLens AI transforms municipal grievance redressal by combining **Multimodal Computer Vision** with **Autonomous Geo-Triage** and **Closed-Loop Resolution Auditing**.

---

## ⚡ The Civic Problem
* **Complaint Overload & Misrouting:** Municipal boards receive thousands of disorganized complaints with vague descriptions, taking days just to route them to the right department.
* **Redundant Duplicate Tickets:** A single pothole on a busy junction generates dozens of individual tickets, overwhelming civic staff with duplicate clutter.
* **Contractor Fraud & Ghost Closures:** Field crews frequently mark civic issues as "Resolved" without fully completing the repair.

---

## 🌟 Key Features

### 1. 📸 Autonomous Multimodal Vision Triage (Google Gemini Vision)
* Citizens upload or snap a photo of urban infrastructure defects (potholes, overflowing trash dumps, broken streetlights, water pipe bursts).
* AI calculates a **Civil Hazard Severity Score (1 to 5)** with structural rationale.
* Automatically routes the ticket to the responsible department (*PWD, Sanitation, Water Board, Electrical*) with a target SLA.
* Filters out non-civic photos (e.g. selfies, indoor clutter).

### 2. ⚡ Smart Geo-Deduplication & Urgency Clustering
* Uses Haversine geo-radius proximity checks (75-meter threshold).
* When multiple citizens report the same defect, the system **merges them into an Urgency Upvote (+1)** instead of cluttering municipal queues with duplicate tickets.

### 3. 🗺️ Municipal Command Center & Live Heatmap
* Interactive city map with color-coded severity markers (Red = Critical, Amber = Moderate, Green = Low).
* Live KPI metrics tracking total pool, critical hazards, and active work orders.
* AI-ranked dispatch queue with one-click **🚜 Dispatch** and **✅ Resolve** controls.

### 4. ✅ AI Resolution Auditor (Before & After Verification)
* When field contractors submit an "After" photo claiming work completion, Gemini AI cross-audits the original defect image against the repair image.
* Assigns a quality grade (*Excellent, Acceptable, Substandard, Fraudulent*) before closing the ticket.

---

## 🏗️ System Architecture

```
[Citizen Mobile/Web App]       [Municipal Official Dashboard]
      │                                    ▲
      │ (Photo + Voice + GPS)              │ (Heatmaps, Priority Queue)
      ▼                                    │
┌────────────────────────────────────────────────────────┐
│                   CivicLens AI Gateway                 │
│                 (Zero-Latency Python Core)             │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
               ▼                           ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐
│       AI Engine Pipeline     │ │      Geo-Spatial Engine      │
│ • Gemini Multimodal Vision   │ │ • OpenStreetMap & Leaflet    │
│ • Severity Assessment (1-5)  │ │ • 75m Radius Deduplication   │
│ • "Before & After" Auditor   │ │ • Upvote Priority Clustering │
└──────────────────────────────┘ └──────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### Option 1: Zero-Dependency Server (Recommended)
CivicLens AI runs on pure Python standard library with no external dependencies required:

```bash
# 1. Start the server
python server.py

# 2. Open in your browser:
# http://localhost:8000
```

### Option 2: Streamlit Dashboard
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run app.py
```

---

## 👥 Contributing (Hacktoberfest)
Contributions are welcome! Please feel free to submit issues or pull requests.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
