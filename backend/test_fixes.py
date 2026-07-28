import requests
import asyncio
import motor.motor_asyncio

API_BASE = "http://localhost:8000/api"

# Test user credentials (replace if needed)
test_email = "test@example.com"
test_password = "test1234"

async def main():
    # Step 1: Get auth token
    print("--- Step 1: Logging in ---")
    login_resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": test_email, "password": test_password}
    )
    print("Login status:", login_resp.status_code)
    if login_resp.status_code != 200:
        print("Login failed! Let's register...")
        register_resp = requests.post(
            f"{API_BASE}/auth/register",
            json={"full_name": "Test User", "email": test_email, "password": test_password}
        )
        print("Register status:", register_resp.status_code)
        login_resp = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": test_email, "password": test_password}
        )
    
    login_data = login_resp.json()
    token = login_data["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Got token!")

    # Step 2: Test unlock-level endpoint with FRONTEND ID (c3)
    print("\n--- Step 2: Testing unlock-level with frontend ID (c3) ---")
    test_frontend_id = "c3"
    unlock_resp = requests.post(
        f"{API_BASE}/companion/{test_frontend_id}/unlock-level",
        headers=headers
    )
    print("Unlock status:", unlock_resp.status_code)
    print("Unlock response:", unlock_resp.text)

    # Step 3: Test delete endpoint with frontend ID
    print("\n--- Step 3: Testing delete endpoint with frontend ID ---")
    delete_resp = requests.delete(
        f"{API_BASE}/companion/{test_frontend_id}",
        headers=headers
    )
    print("Delete status:", delete_resp.status_code)
    print("Delete response:", delete_resp.text)

    # Step 4: Check MongoDB
    print("\n--- Step 4: Checking MongoDB ---")
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.ai_companions
    user = await db.users.find_one({"email": test_email})
    if user:
        print("User found!")
        print("Companion progression:", user.get("companion_progression"))
    else:
        print("User not found in MongoDB!")

if __name__ == "__main__":
    asyncio.run(main())
