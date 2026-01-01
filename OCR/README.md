# Medical Claims Processor (India)

An AI-powered Streamlit application that automates medical reimbursement claim verification using Google Gemini API. Optimized for free-tier usage with Indian Rupee (₹) support and comprehensive admin review capabilities.

## Features

- Upload insurance policy (PDF) and medical bill (PDF/image) documents
- AI-powered document analysis using Google Gemini Flash
- **Admin Review & Edit Interface** - Review and modify AI extractions before finalizing
- Deterministic financial calculations using Python/Pandas
- Interactive results display with color-coded approval/rejection status
- CSV and PDF export functionality for approved claims
- **Free-tier optimizations** for cost-effective usage
- **Indian Rupee (₹) currency support**

## New: Admin Review & Edit Features

### Admin Capabilities
- **Password-protected admin panel** for secure access
- **Edit policy information** (name, copay %, client details)
- **Review and modify bill items** (description, cost, coverage status)
- **Add missing items** or remove incorrect extractions
- **Bulk operations** for efficient corrections
- **Real-time recalculation** when data is modified
- **Approval workflow** - must approve before final download
- **Reset to original** AI extraction if needed

### Workflow
1. Process documents with AI
2. Review initial results
3. Admin login for editing access
4. Edit/correct any inaccuracies
5. Approve final data
6. Download approved reports

See [ADMIN_FEATURES.md](ADMIN_FEATURES.md) for detailed documentation.

## Free-Tier Optimizations

This application is optimized for Google Gemini's free tier:

- **File Size Limit**: 20MB (reduced from 200MB for faster processing)
- **Rate Limiting**: 1-second minimum interval between API requests
- **Daily Quota**: 1,500 requests per day with usage monitoring
- **Conservative Retries**: Maximum 2 retry attempts to save quota
- **Optimized Tokens**: Reduced output tokens (2,048) for efficiency
- **Real-time Monitoring**: Quota usage display in the UI

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API key and admin password:
   - Edit `config.py` and replace the API key with your actual Google API key
   - Change the admin password from the default "admin123"
   - Get your API key from: https://aistudio.google.com/

4. Run the application:
```bash
streamlit run app.py
```

## Usage Tips for Free Tier

**File Optimization:**
- Keep files under 20MB for optimal performance
- Use clear, high-contrast images for better AI accuracy
- Compress large PDFs before uploading

**Processing Tips:**
- Process one claim at a time
- Wait for completion before starting another
- Monitor daily quota usage in the app

**Best Results:**
- Ensure text is clearly readable in documents
- Use standard medical bill formats when possible
- Include complete policy information

## Project Structure

```
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── src/               # Source code modules
│   ├── models.py      # Data models (ClaimData, BillItem, etc.)
│   ├── calculator.py  # Calculation engine
│   ├── gemini_processor.py  # AI processing with optimizations
│   └── validation.py  # Input validation
├── tests/             # Test files
├── data/              # Sample data files
└── venv/              # Virtual environment
```

## Requirements

- Python 3.10+
- Google API key for Gemini Flash
- See requirements.txt for complete dependency list

## Currency Support

All amounts are displayed and calculated in **Indian Rupees (₹)**:
- Bills are processed expecting Rupee amounts
- All calculations maintain Rupee precision
- CSV exports include Rupee formatting
- UI displays ₹ symbol throughout
