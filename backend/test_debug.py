"""
Test script to debug delete companion and unlock level issues
"""
import requests
import asyncio
import json

API_BASE = "http://localhost:8000/api"

# Test credentials
TEST_EMAIL = "test_debug@example.com"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Test Debug User"

async def test_endpoints():
    """Test the delete and unlock endpoints"""
    
    # Step 1: Register/Login
    print("=" * 60)
    print("Step 1: Authenticating...")
    print("=" * 60)
    
    # Try login first
    login_resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    print(f"Login attempt status: {login_resp.status_code}")
    
    if login_resp.status_code != 200:
        print("Login failed, trying to register...")
        register_resp = requests.post(
            f"{API_BASE}/auth/register",
            json={"full_name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        print(f"Register status: {register_resp.status_code}")
        print(f"Register response: {register_resp.text[:200]}")
        
        # Try login again
        login_resp = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        print(f"Second login attempt status: {login_resp.status_code}")
    
    if login_resp.status_code != 200:
        print("ERROR: Failed to authenticate!")
        print(f"Response: {login_resp.text}")
        return
    
    login_data = login_resp.json()
    token = login_data.get("data", {}).get("access_token")
    if not token:
        print("ERROR: No access token in response!")
        print(f"Response data: {login_data}")
        return
    
    print(f"✓ Successfully authenticated! Token: {token[:20]}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Test DELETE endpoint with frontend ID
    print("\n" + "=" * 60)
    print("Step 2: Testing DELETE /companion/{id} with frontend ID (c3)")
    print("=" * 60)
    
    frontend_id = "c3"  # Julian's frontend ID
    delete_resp = requests.delete(
        f"{API_BASE}/companion/{frontend_id}",
        headers=headers
    )
    print(f"DELETE /companion/{frontend_id}")
    print(f"Status: {delete_resp.status_code}")
    print(f"Response: {delete_resp.text[:300]}")
    
    if delete_resp.status_code == 200:
        print("✓ Delete successful!")
    elif delete_resp.status_code == 404:
        print("⚠ Companion not found (may already be deleted)")
    else:
        print("✗ Delete failed!")
    
    # Step 3: Test POST unlock-level endpoint with frontend ID
    print("\n" + "=" * 60)
    print("Step 3: Testing POST /companion/{id}/unlock-level with frontend ID (c3)")
    print("=" * 60)
    
    unlock_resp = requests.post(
        f"{API_BASE}/companion/{frontend_id}/unlock-level",
        headers=headers
    )
    print(f"POST /companion/{frontend_id}/unlock-level")
    print(f"Status: {unlock_resp.status_code}")
    print(f"Response: {unlock_resp.text[:300]}")
    
    if unlock_resp.status_code == 200:
        print("✓ Unlock level successful!")
    elif unlock_resp.status_code == 400:
        print("⚠ No pending level up (need to earn XP first)")
    elif unlock_resp.status_code == 404:
        print("⚠ Companion not found")
    else:
        print("✗ Unlock level failed!")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_endpoints())
