"""
Pre-flight checklist script.
Validates that the environment is properly configured before running the app.
"""
import sys
import os
from pathlib import Path


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Create it by copying .env.example:")
        print("   cp .env.example .env")
        return False
    print("✅ .env file exists")
    return True


def check_env_variables():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
        "DATABASE_URL",
        "API_KEY_SECRET_KEY"
    ]
    
    missing = []
    # More lenient placeholder check - only check for obvious placeholders
    placeholder_values = ["your-", "xxxxx", "your_", "placeholder"]
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        elif any(placeholder.lower() in value.lower() for placeholder in placeholder_values):
            print(f"⚠️  {var} appears to have a placeholder value")
            missing.append(var)
    
    if missing:
        print(f"❌ Missing or invalid environment variables: {', '.join(missing)}")
        print("   Update your .env file with real values from Supabase")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import supabase
        import pydantic
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e.name}")
        print("   Install dependencies with: pip install -r requirements.txt")
        return False


def check_database_connection():
    """Check if database connection works."""
    try:
        from config import get_settings
        from database import engine
        
        settings = get_settings()
        
        # Try to connect
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Check your DATABASE_URL in .env")
        return False


def check_supabase_connection():
    """Check if Supabase connection works."""
    try:
        from utils.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        # Try a simple query
        result = client.table('profiles').select('*').limit(1).execute()
        
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        print("   Check your Supabase credentials in .env")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("FastAPI + Supabase Auth - Pre-flight Checklist")
    print("=" * 60)
    print()
    
    checks = [
        ("Environment File", check_env_file),
        ("Environment Variables", check_env_variables),
        ("Dependencies", check_dependencies),
        ("Database Connection", check_database_connection),
        ("Supabase Connection", check_supabase_connection),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during check: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    
    if all(results):
        print("✅ All checks passed! You're ready to run the application.")
        print("\nStart the server with:")
        print("  uvicorn main:app --reload")
        print("\nThen visit:")
        print("  http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("  - QUICKSTART.md")
        print("  - SUPABASE_SETUP.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
