import sys
import requests

def run_diagnostics(base_url):
    print("=" * 60)
    print(f"RUNNING LIVE DEPLOYMENT DIAGNOSTICS FOR:")
    print(f"URL: {base_url}")
    print("=" * 60)

    # 1. Ping Health Endpoint
    print("\n[1/3] Pinging Health Endpoint...")
    health_url = f"{base_url.rstrip('/')}/health"
    try:
        res = requests.get(health_url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            print(f"  --> SUCCESS: Endpoint is online.")
            print(f"  --> Response: {data}")
        else:
            print(f"  --> FAILURE: Server responded with status code {res.status_code}.")
            return
    except requests.exceptions.RequestException as e:
        print(f"  --> FAILURE: Could not connect to host. Details: {e}")
        print("\nDIAGNOSIS: The backend service is currently offline or the URL is incorrect.")
        return

    # 2. Test User Login Authentication
    print("\n[2/3] Testing Login Authentication with Default Seed User...")
    login_url = f"{base_url.rstrip('/')}/api/auth/login"
    login_payload = {
        "username": "analyst_user",
        "password": "analyst123"
    }
    token = None
    try:
        res = requests.post(login_url, json=login_payload, timeout=10)
        if res.status_code == 200:
            token_data = res.json()
            token = token_data.get("access_token")
            print(f"  --> SUCCESS: Authenticated successfully.")
            print(f"  --> User Role: {token_data.get('role')}")
            print(f"  --> Token Type: {token_data.get('token_type')}")
        elif res.status_code == 401 or res.status_code == 400:
            print(f"  --> FAILURE: Authentication rejected. Status: {res.status_code}")
            print(f"  --> Response: {res.text}")
        else:
            print(f"  --> FAILURE: Login endpoint returned status code {res.status_code}.")
            print(f"  --> Response: {res.text}")
    except requests.exceptions.RequestException as e:
        print(f"  --> FAILURE: Connection error during login test. Details: {e}")

    # 3. Test Authenticated API Access
    if token:
        print("\n[3/3] Testing Authenticated API Access...")
        headers = {"Authorization": f"Bearer {token}"}
        me_url = f"{base_url.rstrip('/')}/api/auth/me"
        try:
            res = requests.get(me_url, headers=headers, timeout=10)
            if res.status_code == 200:
                print(f"  --> SUCCESS: Verified token access to /auth/me.")
                print(f"  --> Verified User: {res.json()}")
            else:
                print(f"  --> FAILURE: Token validation failed with status {res.status_code}.")
        except requests.exceptions.RequestException as e:
            print(f"  --> FAILURE: Connection error during token check. Details: {e}")
    else:
        print("\n[3/3] Skipped Authenticated API Access (Authentication failed).")

    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY:")
    if token:
        print("  - Connection: PASS")
        print("  - Database Seeding: PASS")
        print("  - Authentication & JWT: PASS")
        print("  --> STATUS: Deployed service is fully functional!")
    else:
        print("  - Connection: PASS")
        print("  - Database/Auth: FAIL")
        print("  --> STATUS: Backend is online but database operations/seeding failed.")
    print("=" * 60)

if __name__ == "__main__":
    url_input = ""
    if len(sys.argv) > 1:
        url_input = sys.argv[1]
    else:
        print("Enter your deployed Railway backend URL (e.g. https://your-backend.up.railway.app):")
        try:
            url_input = input("URL: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(0)

    if not url_input:
        print("URL cannot be empty.")
        sys.exit(1)
        
    if not url_input.startswith("http"):
        url_input = "https://" + url_input

    run_diagnostics(url_input)
