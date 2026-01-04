# 🚀 Setup Guide for Medical Claims Processor

## Prerequisites

- Python 3.10 or higher
- Git
- Google Cloud account with Gemini API access
- Text editor or IDE

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/medical-claims-processor.git
cd medical-claims-processor
```

### 2. Create Virtual Environment

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. **Copy the example environment file:**
```bash
cp .env.example .env
```

2. **Edit the `.env` file with your settings:**
```env
# Required: Get from Google AI Studio
GOOGLE_API_KEY=your-actual-google-api-key-here

# Required: Change from default
ADMIN_PASSWORD=your-secure-password-here

# Optional: Customize as needed
MAX_FILE_SIZE_MB=20
MAX_DAILY_REQUESTS=1000
ENVIRONMENT=development
DEBUG=True
```

### 5. Get Google Gemini API Key

1. **Visit Google AI Studio:**
   - Go to https://aistudio.google.com/
   - Sign in with your Google account

2. **Create API Key:**
   - Click "Get API Key"
   - Create a new API key or use existing one
   - Copy the API key

3. **Enable Gemini API:**
   - Go to Google Cloud Console
   - Enable the "Generative AI API"
   - Ensure billing is set up (free tier available)

4. **Add to Environment:**
   - Paste your API key in the `.env` file
   - Replace `your-actual-google-api-key-here` with your key

### 6. Test the Setup

1. **Run the application:**
```bash
streamlit run app.py
```

2. **Open in browser:**
   - The app will open at `http://localhost:8501`
   - You should see the Medical Claims Processor interface

3. **Test API connection:**
   - Upload sample documents (use files from `data/` folder)
   - Try processing to verify API connectivity

## Configuration Options

### File Upload Limits
- **Default**: 20MB maximum file size
- **Formats**: PDF for policies, PDF/JPG/PNG for bills
- **Modify**: Change `MAX_FILE_SIZE_MB` in `.env`

### API Rate Limits
- **Default**: 1000 requests per day
- **Interval**: 2 seconds between requests
- **Modify**: Change `MAX_DAILY_REQUESTS` in `.env`

### Admin Access
- **Default password**: `admin123` (change this!)
- **Access**: Click admin panel in the app
- **Modify**: Change `ADMIN_PASSWORD` in `.env`

## Troubleshooting

### Common Issues

**1. API Key Error:**
```
Error: Invalid API key or insufficient permissions
```
**Solution:**
- Verify your API key is correct in `.env`
- Check Google Cloud Console for API enablement
- Ensure billing is set up

**2. Module Import Error:**
```
ModuleNotFoundError: No module named 'streamlit'
```
**Solution:**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**3. File Upload Error:**
```
File too large or unsupported format
```
**Solution:**
- Check file size (must be under 20MB)
- Use supported formats: PDF, JPG, PNG
- Compress large files

**4. Environment Variable Error:**
```
GOOGLE_API_KEY not found
```
**Solution:**
- Ensure `.env` file exists in project root
- Check that `GOOGLE_API_KEY` is set in `.env`
- Restart the application after changing `.env`

### Performance Issues

**Slow Processing:**
- Reduce file sizes
- Check internet connection
- Monitor API quota usage

**Memory Issues:**
- Close other applications
- Use smaller files
- Restart the application

## Development Setup

### For Contributors

1. **Fork the repository** on GitHub

2. **Clone your fork:**
```bash
git clone https://github.com/yourusername/medical-claims-processor.git
```

3. **Create feature branch:**
```bash
git checkout -b feature/your-feature-name
```

4. **Install development dependencies:**
```bash
pip install -r requirements.txt
pip install pytest black flake8  # Additional dev tools
```

5. **Run tests:**
```bash
python -m pytest tests/
```

6. **Format code:**
```bash
black src/ app.py
```

### Environment Variables for Development

```env
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
```

## Production Deployment

### For Production Use

1. **Set production environment:**
```env
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
```

2. **Use strong passwords:**
```env
ADMIN_PASSWORD=very-secure-password-here
```

3. **Configure proper limits:**
```env
MAX_FILE_SIZE_MB=10
MAX_DAILY_REQUESTS=500
```

4. **Deploy to cloud platform:**
   - Streamlit Cloud
   - Heroku
   - AWS/GCP/Azure

## Security Checklist

- [ ] Changed default admin password
- [ ] API key stored in environment variables (not in code)
- [ ] `.env` file added to `.gitignore`
- [ ] File upload limits configured
- [ ] Rate limiting enabled
- [ ] Production environment configured

## Next Steps

1. **Test with your documents** - Upload real policy and medical bills
2. **Customize coverage rules** - Modify `src/coverage_engine.py` for your needs
3. **Train your team** - Show admin panel features
4. **Monitor usage** - Watch API quota and performance
5. **Provide feedback** - Report issues or suggest improvements

## Support

- **Documentation**: Check README.md and other .md files
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact maintainers for urgent issues

---

**Happy processing! 🏥💊📋**