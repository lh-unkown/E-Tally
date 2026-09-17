# ⚓ HIPG e-Tally System for Local Import & Transshipment RORO Cargo

> **Hambantota International Port Group (HIPG)** - Comprehensive Digital e-Tally Process Web Application.

The **HIPG e-Tally System** replaces paper vehicle tally sheets (Doc Ref: 20586) with an end-to-end digital solution. It automates vehicle accessories checklists, AI photo auto-identification, interactive damage canvas annotations, supervisor update approvals, security discharged condition verification, Work Point audit logging, and bulk vector PDF generation.

---

## ✨ Features Breakdown

- **🔒 Mandatory Full-Screen Login Portal Wall**: Full system lockdown requiring valid User ID & Password authentication. Includes role-based access for Admin, Surveyor, Supervisor, Security Officer, and Driver.
- **🚢 On-board Tally Workflow**:
  - **Vessel Selection**: Select from berthed RORO vessels (`VIKING DRIVE`, `HOEGH STRIKER`, `EUKOR HORIZON`).
  - **Chassis / VIN Search**: Instant lookup by last 6 digits of VIN/Chassis number.
  - **Accessories Checklist**: Mode toggle between **AI Mode** (photo identification) and **Manual Mode** (3-column checklist matching paper Doc Ref 20586).
  - **Vehicle Damage Recording & Photo Canvas**: 15 standard damage codes + **HTML5 Touch/Mouse Photo Canvas Tool** to outline and circle damage areas on photographs using touch devices or stylus.
  - **Save & Lock Confirmation**: Confirms and locks document permanently with user ID and date/time audit trail.
- **🏗️ Yard Tally Workflows**:
  - **Export Tally**: Gate receipt cargo tallying for pre-advised VINs.
  - **Tally Update**: Authorization workflow where locked tallies appear for editing **only after supervisor/admin approval**.
  - **Security Check**: Security team condition verification (`Verified` vs `Unverified` discrepancy logging).
- **🔍 Inquire & Work Point Audit Trail**: Search by last 6 VIN digits, view digital e-Tally layout with official HIPG logo, damage photos, and complete Work Point audit table matrix (Onboard, Yard Shift, Update, Delivery Gate).
- **📄 Bulk Tally Generate (PDF)**: Multi-line VIN entry, bulk validation counter, and batch vector jsPDF generation.
- **⚙️ Admin Control Panel**:
  - User Account CRUD (Create, Edit, Deactivate users).
  - Master Tally Override (Force unlock, Purge tally).
  - Vessel & Manifest Registry Manager.
  - Global System Audit Log.
- **📱 Multi-Device Cross-Platform Responsiveness**: PC Desktop, Tablet, and Mobile Smartphone/HHT viewport compatibility.

---

## 🚀 Quick Start & Local Execution

### Prerequisites
- Python 3.8+ (No external pip dependencies required).

### Installation & Run Commands

```bash
# Clone repository
git clone https://github.com/lh-unkown/E-Tally.git
cd E-Tally

# Initialize database & start web server
python server.py
```

Open your browser and navigate to: **http://localhost:8080**

---

## 🔑 Default Login Credentials

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `admin123` | Full Superuser & Admin Panel |
| **IMPL Surveyor** | `surveyor298` | `pass123` | On-board & Export Tallying |
| **Port Supervisor** | `supervisor352` | `pass123` | Tally Update Approvals |
| **Security Officer** | `security5958` | `pass123` | Discharged Vehicle Verification |
| **Yard Driver** | `driver60664` | `pass123` | Yard Movement Scanning |

---

## 📁 Repository Structure

```
E-Tally/
├── database.py       # SQLite database initialization & seed manifests
├── server.py         # HTTP web server & REST API endpoints
├── static/
│   ├── index.html    # Single Page Application HTML5 frontend
│   ├── app.js        # Client-side application logic & PDF generator
│   ├── styles.css    # HIPG port theme & responsive CSS
│   └── hipg_logo.png # Official HIPG logo asset
├── .gitignore
└── README.md
```

---

## 📄 License & Ownership
Copyright © 2026 Hambantota International Port Group Pvt Ltd (HIPG). All rights reserved.
