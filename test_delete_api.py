#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8003"

print("=== Testing Delete API ===\n")

# Test with invalid token to see if endpoint exists
try:
    response = requests.delete(
        f"{BASE_URL}/student/test-builder/tests/999",
        headers={"Authorization": "Bearer invalid-token"}
    )
    print(f"DELETE /student/test-builder/tests/999 response: {response.status_code}")
    print(f"Response body: {response.text}\n")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}\n")

# Check if tests endpoint works
try:
    response = requests.get(
        f"{BASE_URL}/student/tests",
        headers={"Authorization": "Bearer invalid-token"}
    )
    print(f"GET /student/tests response: {response.status_code}")
    if response.status_code == 401:
        print("✓ Authentication required (expected)\n")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}\n")

print("✓ Backend endpoints are reachable")
