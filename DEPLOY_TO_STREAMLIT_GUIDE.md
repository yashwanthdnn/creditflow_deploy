# 🚀 Deploying CreditFlow AI to Streamlit Community Cloud

This guide provides step-by-step instructions to deploy the **CreditFlow AI Multi-Agent Credit Assessment & Loan Pre-Screening System** to **Streamlit Community Cloud (100% Free)** in under 2 minutes.

---

## ⚡ Architecture & Deployment Highlights

- **Pure Python 3.10 - 3.14 Compatibility:** Uses modern, pure-Python libraries (`pypdf`, `scikit-learn`, `plotly`, `pandas`, `pydantic`).
- **No Linux System Packages Needed:** Zero apt-get / C++ compilation dependencies — installs in seconds with `uv pip install`.
- **Self-Healing File Bootstrap:** Both `streamlit_app.py` and `app.py` automatically detect and organize packages, whether uploaded with full directory hierarchy or uploaded directly.
- **Embedded ML Pipeline & Pre-Screening Database:** Pre-trained model (`artifacts/credit_risk_model.joblib`) and SQLite database (`data/loan_prescreening.db`) are self-initializing.
- **Zero Paid API Dependencies:** Runs 100% autonomously with local deterministic policies and machine learning inference.

---

## 🌐 Quick Deployment Steps (Streamlit Community Cloud)

### Step 1: Upload Your Files to GitHub

A pre-packaged, ready-to-deploy clean folder has been prepared on your computer:
📂 **`C:\Users\HP\Downloads\creditflow_deploy`** (or zip file **`C:\Users\HP\Downloads\creditflow_deploy.zip`**)

#### How to upload to GitHub:
1. Open [github.com/new](https://github.com/new) in your browser and sign in.
2. Name your repository (for example, `creditflow-fintech` or `fintech-app`).
3. Set visibility to **Public** (required for free Streamlit Community Cloud).
4. Click **Create repository**.
5. On the empty repo page, click the link: **"uploading an existing file"**.
6. Open your folder `C:\Users\HP\Downloads\creditflow_deploy` in File Explorer:
   - Select all files and folders (or extract `creditflow_deploy.zip` and drag all contents).
   - Drag and drop them into the GitHub upload box.
   - Key files to ensure are present:
     - `app.py`
     - `streamlit_app.py`
     - `requirements.txt`
     - `.streamlit/config.toml`
     - Folders: `agents/`, `config/`, `data/`, `ml/`, `models/`, `services/`, `ui_pages/`, `artifacts/`
7. Click **Commit changes** (wait 10-20 seconds for GitHub to finish saving).

---

### Step 2: Deploy on Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and log in with your GitHub account.
2. Click the blue **"Create app"** button (top right).
3. Select **"I already have an app"**.
4. Configure the 3 fields:
   - **Repository:** Choose your newly created repository (e.g. `YOUR_USERNAME/creditflow-fintech`).
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py` *(or `app.py`)*
   - **App URL (Optional):** Pick a custom subdomain (e.g. `creditflow-ai.streamlit.app`).
5. Click **"Deploy!"**

---

### Step 3: Watch It Boot!

Streamlit Community Cloud will:
1. Clone your repository (`main` branch).
2. Install dependencies via `uv pip install` from `requirements.txt` in ~3 seconds.
3. Automatically launch `streamlit_app.py`.
4. Your application will be live at:
   👉 **`https://YOUR-SUBDOMAIN.streamlit.app`**

---

## 🔐 Demonstration Logins (Ready Out-of-the-Box)

The live app features 1-click demo login buttons directly on the login screen:

| Role | Username | Password | Features & Permissions |
| :--- | :--- | :--- | :--- |
| 👮 **Credit Officer** | `officer` | `password123` | Underwriter Queue, Verification, Analytics, Sandboxes |
| 🕵️ **Fraud Investigator** | `investigator` | `password123` | Fraud Queue, Tamper Inspection, Risk Flags |
| 🛡️ **Administrator** | `admin` | `password123` | Full Audit Logs, Responsible AI & Settings, Sandboxes |
| 👤 **Applicant (Borrower)** | `applicant` | `password123` | Submit Applications (Personal / Education), Track Status |

---

## 💻 Local Testing Commands

If you ever want to run or test locally:
```powershell
# Run the 52 automated tests
python -m pytest tests/ -v

# Run the application locally
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.
