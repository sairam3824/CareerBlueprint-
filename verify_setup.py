"""
Setup Verification Script
Checks if all components are properly installed and configured
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print("✅ Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("❌ Python 3.9+ required, found:", f"{version.major}.{version.minor}.{version.micro}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = [
        'flask', 'flask_cors', 'sentence_transformers', 'pandas', 
        'openpyxl', 'requests', 'dotenv', 'yaml', 'sklearn'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    return len(missing) == 0

def check_directories():
    """Check if required directories exist"""
    dirs = ['backend', 'frontend', 'data', 'logs', 'tests']
    
    all_exist = True
    for dir_name in dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ - MISSING")
            all_exist = False
    
    return all_exist

def check_config_files():
    """Check if configuration files exist"""
    files = ['config.yaml', '.env.example', 'requirements.txt', 'app.py']
    
    all_exist = True
    for file_name in files:
        if Path(file_name).exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - MISSING")
            all_exist = False
    
    return all_exist

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not Path('.env').exists():
        print("⚠️  .env file not found")
        print("   Run: cp .env.example .env")
        print("   Then add your API keys")
        return False
    
    print("✅ .env file exists")
    
    # Check for required variables
    with open('.env', 'r') as f:
        content = f.read()
    
    required_vars = ['ADZUNA_APP_ID', 'ADZUNA_APP_KEY', 'RAPIDAPI_KEY']
    missing_vars = []
    
    for var in required_vars:
        if var not in content or f"{var}=your_" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing or placeholder values for: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables set")
    return True

def check_modules():
    """Check if backend modules can be imported"""
    modules = [
        'backend.skill_analyzer.skill_analyzer',
        'backend.recommendation_engine.recommendation_engine',
        'backend.job_fetcher.job_fetcher',
        'backend.application_tracker.application_tracker',
        'backend.email_service.email_service'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module} - ERROR: {str(e)[:50]}")
            all_ok = False
    
    return all_ok

def main():
    """Run all checks"""
    print("🔍 AI Job Recommendation Bot - Setup Verification")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Config Files", check_config_files),
        ("Environment Variables", check_env_file),
        ("Backend Modules", check_modules)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        print("-" * 60)
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 All checks passed! You're ready to run the bot.")
        print("\nNext steps:")
        print("1. Start backend: python app.py")
        print("2. Start frontend: cd frontend && python -m http.server 8000")
        print("3. Open browser: http://localhost:8000")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements.txt")
        print("- Create .env file: cp .env.example .env")
        print("- Add API keys to .env file")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
