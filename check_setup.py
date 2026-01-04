#!/usr/bin/env python3
"""
Quick setup check script
"""

import sys
import os

print("🔍 Setup Check")
print("=" * 40)

# Check Python path
print(f"Python executable: {sys.executable}")
if 'venv' in sys.executable:
    print("✅ Running in virtual environment")
else:
    print("❌ NOT running in virtual environment")
    print("   Run: source venv/bin/activate")

# Check required packages
required_packages = ['streamlit', 'google.genai', 'pandas', 'reportlab']
missing_packages = []

for package in required_packages:
    try:
        __import__(package.replace('.', '_') if '.' in package else package)
        print(f"✅ {package} - installed")
    except ImportError:
        print(f"❌ {package} - missing")
        missing_packages.append(package)

# Check API key
try:
    from config import GOOGLE_API_KEY
    if GOOGLE_API_KEY and GOOGLE_API_KEY != "your-google-api-key-here":
        print(f"✅ API key - configured")
    else:
        print(f"❌ API key - not configured")
except Exception as e:
    print(f"❌ API key - error: {e}")

# Summary
print("\n" + "=" * 40)
if missing_packages:
    print(f"❌ Setup incomplete. Missing: {', '.join(missing_packages)}")
    print("   Run: pip install -r requirements.txt")
else:
    print("✅ Setup complete! Ready to run: streamlit run app.py")