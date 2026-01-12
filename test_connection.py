"""
Test Supabase connection and authentication.
"""
import sys
from config import get_settings
from utils.supabase_client import get_supabase_client, get_supabase_anon_client

settings = get_settings()


def test_connection():
    """Test basic Supabase connection."""
    print("Testing Supabase connection...")
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    
    try:
        # Test with anon client
        anon_client = get_supabase_anon_client()
        print("✓ Anon client created successfully")
        
        # Test with service role client
        service_client = get_supabase_client()
        print("✓ Service role client created successfully")
        
        # Try a simple query
        result = service_client.table('profiles').select('*').limit(1).execute()
        print("✓ Database query successful")
        
        print("\n✓ Supabase connection test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Connection test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
