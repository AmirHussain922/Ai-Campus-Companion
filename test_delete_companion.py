#!/usr/bin/env python3
"""
Test script to verify companion deletion is working properly.

This script tests:
1. Backend API endpoint for deleting companions
2. Database cleanup after deletion
3. Response format

Run this with: python test_delete_companion.py
"""

import asyncio
import sys
import json
from datetime import datetime

# Test configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_EMAIL = "test_delete_user@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_COMPANION_ID = "c1"  # Study Buddy - Oliver

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")

async def test_delete_companion():
    """Main test function"""
    print("=" * 60)
    print("COMPANION DELETE API TEST")
    print("=" * 60)
    print()
    
    # Import here so we can show nice error if not installed
    try:
        import httpx
    except ImportError:
        print_error("httpx is not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
        import httpx
    
    # Create test user and get auth token
    print_info("Step 1: Creating test user and logging in...")
    async with httpx.AsyncClient() as client:
        # Try to register
        try:
            register_resp = await client.post(
                f"{API_BASE_URL}/auth/register",
                json={
                    "full_name": "Test User",
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            )
            if register_resp.status_code == 200:
                print_success("Test user registered successfully")
            else:
                print_warning(f"Registration returned {register_resp.status_code}, user may already exist")
        except Exception as e:
            print_warning(f"Registration error: {e}")
        
        # Login to get token
        try:
            login_resp = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            )
            if login_resp.status_code == 200:
                data = login_resp.json()
                access_token = data["data"]["access_token"]
                print_success("Logged in successfully, got access token")
            else:
                print_error(f"Login failed with status {login_resp.status_code}")
                print(login_resp.text)
                return
        except Exception as e:
            print_error(f"Login error: {e}")
            return
        
        # Test 1: Delete companion endpoint
        print()
        print_info("Step 2: Testing DELETE /companion/{companion_id} endpoint...")
        try:
            delete_resp = await client.delete(
                f"{API_BASE_URL}/companion/{TEST_COMPANION_ID}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            print(f"  Response status: {delete_resp.status_code}")
            
            if delete_resp.status_code == 200:
                data = delete_resp.json()
                print_success(f"Delete successful: {data.get('message', 'OK')}")
            elif delete_resp.status_code == 404:
                print_warning(f"Companion not found (may already be deleted): {delete_resp.text}")
            else:
                print_error(f"Delete failed: {delete_resp.status_code}")
                print(f"  Response: {delete_resp.text}")
                
        except Exception as e:
            print_error(f"Delete request error: {e}")
        
        # Test 2: Verify companion is actually deleted from database
        print()
        print_info("Step 3: Verifying companion is deleted from database...")
        try:
            # Check user's companion_progression
            user_resp = await client.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_resp.status_code == 200:
                user_data = user_resp.json()
                companion_prog = user_data.get("data", {}).get("companion_progression", [])
                companion_ids = [p.get("companion_id") for p in companion_prog]
                
                backend_id = None
                # Map c1 -> study_buddy, etc.
                if TEST_COMPANION_ID == "c1":
                    backend_id = "study_buddy"
                elif TEST_COMPANION_ID == "c2":
                    backend_id = "party_friend"
                elif TEST_COMPANION_ID == "c3":
                    backend_id = "philosopher"
                elif TEST_COMPANION_ID == "c4":
                    backend_id = "rival"
                elif TEST_COMPANION_ID == "c5":
                    backend_id = "freshman"
                
                if backend_id and backend_id in companion_ids:
                    print_error(f"Companion {TEST_COMPANION_ID} (backend: {backend_id}) is STILL in database!")
                else:
                    print_success(f"Companion {TEST_COMPANION_ID} (backend: {backend_id}) has been deleted from database!")
            else:
                print_warning(f"Could not verify: /auth/me returned {user_resp.status_code}")
                
        except Exception as e:
            print_error(f"Verification error: {e}")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_delete_companion())
