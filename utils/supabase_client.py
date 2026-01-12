"""
Supabase client initialization and utilities.
"""
from supabase import create_client, Client
from config import get_settings

settings = get_settings()


def get_supabase_client() -> Client:
    """
    Get Supabase client with service role key.
    Use for server-side operations that bypass RLS.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )


def get_supabase_anon_client() -> Client:
    """
    Get Supabase client with anon key.
    Use for operations that respect RLS.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )
