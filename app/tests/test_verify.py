import httpx
import time
import uuid
import sys

BASE_URL = "http://localhost:8000"

def test_multitenancy_flow():
    client = httpx.Client(timeout=60)
    
    print("--- Starting Multi-Tenancy SaaS Test ---")
    
    # 1. Register a new tenant
    email = f"tenant_{uuid.uuid4().hex[:6]}@example.com"
    password = "secure_password_123"
    print(f"Step 1: Registering new user {email}...")
    resp = client.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password})
    if resp.status_code != 200:
        print(f"FAILED: Registration returned {resp.status_code} - {resp.text}")
        return
    print("SUCCESS: User registered.")
    
    # 2. Login to get token
    print("Step 2: Logging in...")
    resp = client.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
    if resp.status_code != 200:
        print(f"FAILED: Login returned {resp.status_code} - {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("SUCCESS: Token obtained.")
    
    # 3. Add a Database Connection
    # We use the internal DB settings for this test
    print("Step 3: Adding a database connection...")
    db_payload = {
        "name": "Production Finances",
        "host": "db",
        "port": 5432,
        "db_name": "financedb",
        "username": "financeuser",
        "password": "financepass",
        "blocked_tables": ["users", "mdl_schemas", "database_connections"]
    }
    resp = client.post(f"{BASE_URL}/databases", json=db_payload, headers=headers)
    if resp.status_code != 201:
        print(f"FAILED: Adding database returned {resp.status_code} - {resp.text}")
        return
    db_id = resp.json()["id"]
    print(f"SUCCESS: Database added with ID: {db_id}")
    
    # 4. Trigger MDL Refresh
    print("Step 4: Triggering MDL refresh (background)...")
    resp = client.post(f"{BASE_URL}/mdl/refresh", json={"database_id": db_id, "name": "finance_mdl"}, headers=headers)
    if resp.status_code != 200:
        print(f"FAILED: MDL refresh returned {resp.status_code} - {resp.text}")
        return
    print("SUCCESS: MDL generation started.")
    
    # 5. Poll for MDL Readiness
    print("Step 5: Waiting for MDL to be generated...")
    ready = False
    for i in range(20):
        resp = client.get(f"{BASE_URL}/mdl/latest?database_id={db_id}", headers=headers)
        if resp.status_code == 200:
            mdl = resp.json()
            if not mdl.get("is_generating"):
                print(f"SUCCESS: MDL is ready! (Version {mdl['version']})")
                ready = True
                break
        elif resp.status_code == 404:
            print(f"  Wait... (attempt {i+1}/20)")
        else:
            print(f"Unexpected status polling MDL: {resp.status_code}")
            break
        time.sleep(3)
    
    if not ready:
        print("FAILED: MDL generation timed out.")
        return
        
    # 6. Ask a Question via Agent
    print("Step 6: Asking a question via the AI Agent...")
    query_payload = {
        "question": "What is the total balance of the Account?",
        "database_id": db_id
    }
    resp = client.post(f"{BASE_URL}/agent/ask", json=query_payload, headers=headers)
    if resp.status_code != 200:
        print(f"FAILED: Agent query returned {resp.status_code} - {resp.text}")
        return
    
    result = resp.json()
    print("\n--- TEST COMPLETE ---")
    print(f"AI RESPONSE:\n{result.get('answer')}")
    print("\nAGENT STEPS:")
    for step in result.get('steps', []):
        print(f"  {step}")

if __name__ == "__main__":
    test_multitenancy_flow()
