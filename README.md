# MediClaimX — Medical Claims Processor (India)

An AI-powered Streamlit application that automates medical reimbursement claim verification using Google Gemini. The actual application lives in the `OCR/` folder.

---

## 🚀 Quick start (Windows)
1. Clone the repository:
   ```powershell
   git clone <repo-url>
   cd <repo-root>
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies (the project `requirements.txt` is inside the `OCR/` folder):
   ```powershell
   pip install -r OCR/requirements.txt
   ```
4. Configure secrets:
   - Create `OCR/config.py` (do NOT commit real keys):
     ```python
     # Example values
     GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
     ADMIN_PASSWORD = "change-me"
     ```
   - Alternatively export env vars or use your preferred secrets manager.
5. Run the app (from repository root or `OCR/`):
   ```powershell
   cd OCR
   streamlit run app.py
   ```
6. Open the app in your browser: http://localhost:8501/

---

## ✅ What you should NOT commit
- Local virtual environments (`venv/`, `.venv/`) and `OCR/venv/`
- `config.py` and any real API keys or secrets
- `__pycache__/`, `.pytest_cache/`, logs, local IDE settings (e.g., `.vscode/`)
- Large generated data files (add only small sample files if useful)

A `.gitignore` has already been added to the `OCR/` folder to cover these items.

---

## 🧪 Tests
Run tests from the `OCR/` folder:
```powershell
cd OCR
pytest
```

---

## 🛠️ Notes & Next Steps
- Replace the placeholder Google API key in `OCR/config.py` with a valid key to enable AI-powered features.
- I can add a `OCR/config.example.py` with safe placeholders and update the README to show how to create `config.py` from it — tell me if you'd like me to add that.

---

## 📄 More documentation
The detailed project README and feature notes are in `OCR/README.md` (keeps in-depth docs close to the app).


---

Maintainers: Chandan785 / MediClaimX
