
#pip install requests google-api-python-client google-auth
# ✅ Creates a Supabase project
# ✅ Waits until it’s ready
# ✅ Enables Google OAuth in Supabase (adds client ID + secret)
# ✅ Configures redirect URLs in Supabase
# ✅ Adds the redirect URL to the Google OAuth Web Client

import os
import time
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# =======================
# Config
# =======================

SUPABASE_TOKEN = os.environ["SUPABASE_TOKEN"]
SUPABASE_ORG_ID = os.environ["SUPABASE_ORG_ID"]

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
GOOGLE_OAUTH_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]

SERVICE_ACCOUNT_FILE = "service_account.json"

PROJECT_NAME = "auto-full-project"
DB_PASSWORD = "StrongPassword123!"
REGION = "us-east-1"

SITE_URL = "http://localhost:3000"
CALLBACK_PATH = "/auth/v1/callback"

HEADERS = {
    "Authorization": f"Bearer {SUPABASE_TOKEN}",
    "Content-Type": "application/json"
}

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# =======================
# Supabase Functions
# =======================

def create_supabase_project():
    url = "https://api.supabase.com/v1/projects"
    payload = {
        "organization_id": SUPABASE_ORG_ID,
        "name": PROJECT_NAME,
        "db_pass": DB_PASSWORD,
        "region": REGION,
        "plan": "free"
    }

    r = requests.post(url, json=payload, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def wait_for_project_ready(project_id):
    url = f"https://api.supabase.com/v1/projects/{project_id}"

    print("Waiting for Supabase project provisioning...")

    while True:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        status = r.json()["status"]

        print("Status:", status)

        if status == "ACTIVE":
            break

        time.sleep(10)

def configure_supabase_auth(project_id):
    url = f"https://api.supabase.com/v1/projects/{project_id}/config/auth"

    payload = {
        "external": {
            "google": {
                "enabled": True,
                "client_id": GOOGLE_CLIENT_ID,
                "secret": GOOGLE_CLIENT_SECRET
            }
        },
        "site_url": SITE_URL,
        "additional_redirect_urls": [
            f"{SITE_URL}/auth/callback"
        ]
    }

    r = requests.patch(url, json=payload, headers=HEADERS)
    r.raise_for_status()

# =======================
# Google OAuth Functions
# =======================

def add_google_redirect_uri(supabase_project_ref):
    new_redirect_url = f"https://{supabase_project_ref}.supabase.co{CALLBACK_PATH}"

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    service = build("oauth2", "v2", credentials=creds)

    name = f"projects/{GCP_PROJECT_ID}/clients/{GOOGLE_OAUTH_CLIENT_ID}"

    client = service.clients().get(name=name).execute()

    redirect_uris = client.get("redirectUris", [])

    if new_redirect_url in redirect_uris:
        print("Google redirect URI already exists.")
        return

    redirect_uris.append(new_redirect_url)
    client["redirectUris"] = redirect_uris

    service.clients().patch(
        name=name,
        body=client
    ).execute()

    print("Added Google redirect URI:")
    print(new_redirect_url)

# =======================
# Main Flow
# =======================

def main():
    project = create_supabase_project()
    project_id = project["id"]
    project_ref = project["ref"]

    print("Supabase project created:", project_ref)

    wait_for_project_ready(project_id)

    configure_supabase_auth(project_id)
    print("Supabase Google OAuth configured")

    add_google_redirect_uri(project_ref)

    print("\n✅ Automation complete")
    print("Supabase URL:", f"https://{project_ref}.supabase.co")
    print("OAuth callback:", f"https://{project_ref}.supabase.co{CALLBACK_PATH}")

if __name__ == "__main__":
    main()
