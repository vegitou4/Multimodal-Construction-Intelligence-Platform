# 🏗️ Multimodal Construction Intelligence Platform

**Skill Wallet — Capstone Project 1**

An AI-powered Streamlit application combining Google Gemini multimodal AI with domain-specific construction engineering logic.

---

## ✨ Features

| Module | Description | Epic |
|--------|-------------|------|
| 🦺 Site Safety & PPE Audit | Upload site photos → AI detects PPE compliance, identifies hazards, generates OSHA/IS 456 report | 2 |
| 🔍 Crack Diagnostics | Upload concrete/wall photos → classify defect type, estimate crack width, recommend repairs | 2 |
| 📊 Planning & Valuation | Interactive inputs → project budget, asset valuation (INR), material estimates, 3D rendering | 3 |
| 💬 Site Assistant | Weather-aware safety alerts + multi-turn construction engineering chatbot | 5 |

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone / navigate to the project
cd Capstone-Project-1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

### Streamlit Community Cloud (1-Click Deploy)

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo and set `app.py` as the main file
4. (Optional) Add `GEMINI_API_KEY` in Secrets

## 🔑 API Key

- Get a free Google Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- Enter it in the sidebar when the app loads
- **No key?** The app runs in **Demo Mode** with simulated results

## 🏗️ Architecture

```
┌─────────────────────────┐
│   Streamlit Frontend    │
│  (Tabs · Widgets · CSS) │
└────────┬────────────────┘
         │  multimodal prompts
         ▼
┌─────────────────────────┐
│  Google Gemini 2.0 Flash│
│  (Vision + Language)    │
└────────┬────────────────┘
         │  structured JSON
         ▼
┌─────────────────────────┐
│  Domain Logic Layer     │
│  PPE · Crack · Valuation│
│  Weather · Chat         │
└─────────────────────────┘
```

## 📦 Dependencies

- `streamlit` — UI framework
- `google-generativeai` — Gemini SDK
- `Pillow` — Image processing

**Zero external database dependencies.**

## 📄 License

MIT
