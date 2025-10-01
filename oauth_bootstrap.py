# oauth_bootstrap.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]  # create/manage files you create

def main():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)
    print("\n--- Save these as GitHub Secrets ---")
    print("OAUTH_CLIENT_ID =", creds.client_id)
    print("OAUTH_CLIENT_SECRET =", creds.client_secret)
    print("OAUTH_REFRESH_TOKEN =", creds.refresh_token)

if __name__ == "__main__":
    main()
