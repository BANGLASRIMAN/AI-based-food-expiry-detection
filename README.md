# FoodGuard AI — Streamlit Version

**AI-Based Food Expiry Detection and Smart Reminder System**

This version replaces the Flask web interface with **Streamlit** while keeping the main project functionality.

## Features

- 📊 Dashboard with inventory statistics
- ➕ Manual food-product entry
- 📷 Food-package image upload
- 🔍 EasyOCR expiry-date detection
- 📅 Automatic expiry-day calculation
- 🟢 Fresh / 🟠 Near Expiry / 🔴 Expired classification
- 🔔 Smart expiry reminders
- 📦 SQLite inventory
- 📈 Basic analytics
- 🤖 AI visual-freshness integration point

## Recommended Python

Python **3.12** is recommended for compatibility with EasyOCR and its ML dependencies.

## Run on Windows

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run streamlit_app.py
```

If PowerShell blocks activation, run without activation:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Streamlit will normally open the application at `http://localhost:8501`.

## Project structure

```text
FoodGuard_AI_Streamlit_Project/
├── app/
│   ├── services/
│   │   ├── expiry.py
│   │   ├── freshness.py
│   │   └── ocr.py
│   └── uploads/
├── database.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

## Important note about AI freshness

The visual-freshness function is currently a placeholder for a trained CNN/transfer-learning model. It should be replaced with a validated model before claiming real freshness-detection accuracy. The printed manufacturer expiry date remains the primary reference for the expiry feature.
