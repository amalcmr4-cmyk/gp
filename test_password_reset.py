"""
Password Reset Flow - Testing & Utility Script

This script helps test the password reset functionality without email setup.
It's useful for development and testing purposes.

Usage:
    python test_password_reset.py

Requirements:
    pip install requests
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "InitialPassword123"
NEW_PASSWORD = "NewPassword456"

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_step(step, description):
    """Print a test step"""
    print(f"[STEP {step}] {description}")

def print_success(message):
    """Print success message"""
    print(f"  ✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"  ✗ {message}")

def print_info(message):
    """Print info message"""
    print(f"  → {message}")

def test_registration():
    """Test 1: User Registration"""
    print_step(1, "User Registration")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"User registered successfully")
            print_info(f"User ID: {data['id']}")
            print_info(f"Email: {data['email']}")
            return True
        elif response.status_code == 409:
            print_info(f"User already exists, skipping registration")
            return True
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_info(f"Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_login():
    """Test 2: User Login"""
    print_step(2, "User Login with Original Password")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Login successful")
            print_info(f"Access Token: {data['access_token'][:50]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            print_info(f"Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_forgot_password():
    """Test 3: Forgot Password Request"""
    print_step(3, "Request Password Reset")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/forgot-password",
            json={
                "email": TEST_EMAIL
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Forgot password request successful")
            print_info(f"Response: {data['detail']}")
            print_info(f"NOTE: In production, reset link would be sent to email")
            return True
        else:
            print_error(f"Forgot password failed: {response.status_code}")
            print_info(f"Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_forgot_password_nonexistent_email():
    """Test 3b: Forgot Password with Non-existent Email"""
    print_step("3b", "Request Password Reset for Non-existent Email")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/forgot-password",
            json={
                "email": "nonexistent@example.com"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Generic response received (security feature)")
            print_info(f"Response: {data['detail']}")
            print_info(f"✓ Email enumeration prevented!")
            return True
        else:
            print_error(f"Request failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def get_reset_token_from_db():
    """
    Retrieve reset token from database for testing.
    
    NOTE: In production, the token would be sent via email.
    This is a development utility only.
    """
    print_step("3c", "Retrieve Reset Token from Database")
    
    try:
        # This is a development utility - in production, tokens come via email
        # For now, we'll make a database query via SQLite
        import sqlite3
        
        db_path = "backend/app.db"  # Adjust path based on your setup
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT reset_token, reset_token_expiry FROM users WHERE email = ?",
            (TEST_EMAIL,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            token = result[0]
            expiry = result[1]
            print_success(f"Reset token retrieved from database")
            print_info(f"Token: {token[:20]}...")
            print_info(f"Expiry: {expiry}")
            return token
        else:
            print_error(f"No reset token found or token is NULL")
            print_info(f"Database path: {db_path}")
            print_info(f"Check if database file exists at this location")
            return None
    except Exception as e:
        print_error(f"Could not retrieve token: {str(e)}")
        print_info(f"This is expected if database is not accessible")
        print_info(f"Manual method: Check database or server logs for token")
        return None

def test_reset_password(reset_token):
    """Test 4: Reset Password"""
    print_step(4, "Reset Password with Token")
    
    if not reset_token:
        print_error(f"No reset token provided")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/reset-password",
            json={
                "token": reset_token,
                "new_password": NEW_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Password reset successful")
            print_info(f"Response: {data['detail']}")
            return True
        else:
            print_error(f"Password reset failed: {response.status_code}")
            print_info(f"Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_login_with_new_password():
    """Test 5: Login with New Password"""
    print_step(5, "Login with New Password")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": NEW_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Login with new password successful")
            print_info(f"Access Token: {data['access_token'][:50]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            print_info(f"Response: {response.json()}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_invalid_token():
    """Test 6: Reset Password with Invalid Token"""
    print_step(6, "Reset Password with Invalid Token")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/reset-password",
            json={
                "token": "invalid_token_12345",
                "new_password": NEW_PASSWORD
            }
        )
        
        if response.status_code == 400:
            data = response.json()
            print_success(f"Invalid token rejected correctly")
            print_info(f"Response: {data['detail']}")
            print_info(f"✓ Security check passed!")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def test_weak_password():
    """Test 7: Reset Password with Weak Password"""
    print_step(7, "Reset Password with Weak Password")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/reset-password",
            json={
                "token": "some_token",
                "new_password": "weak"  # Too short, no special requirements met
            }
        )
        
        if response.status_code in [400, 422]:  # 422 is validation error
            data = response.json()
            print_success(f"Weak password rejected")
            print_info(f"Response: {str(data)[:100]}...")
            print_info(f"✓ Password strength validation working!")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print_header("PASSWORD RESET FLOW - TEST SUITE")
    
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Test Email: {TEST_EMAIL}")
    print_info(f"Test Password: {TEST_PASSWORD}")
    print_info(f"New Password: {NEW_PASSWORD}")
    
    results = {
        "Registration": False,
        "Login (Original)": False,
        "Forgot Password": False,
        "Forgot Password (Non-existent)": False,
        "Retrieve Token": False,
        "Reset Password": False,
        "Login (New Password)": False,
        "Invalid Token": False,
        "Weak Password": False,
    }
    
    # Test 1: Registration
    results["Registration"] = test_registration()
    if not results["Registration"]:
        print_error("Registration failed, stopping tests")
        return results
    
    time.sleep(0.5)
    
    # Test 2: Login with original password
    results["Login (Original)"] = test_login()
    
    time.sleep(0.5)
    
    # Test 3: Forgot password
    results["Forgot Password"] = test_forgot_password()
    
    time.sleep(0.5)
    
    # Test 3b: Forgot password with non-existent email
    results["Forgot Password (Non-existent)"] = test_forgot_password_nonexistent_email()
    
    time.sleep(0.5)
    
    # Test 3c: Retrieve reset token
    reset_token = get_reset_token_from_db()
    results["Retrieve Token"] = reset_token is not None
    
    time.sleep(0.5)
    
    # Test 4: Reset password (only if we got the token)
    if reset_token:
        results["Reset Password"] = test_reset_password(reset_token)
        time.sleep(0.5)
        
        # Test 5: Login with new password
        results["Login (New Password)"] = test_login_with_new_password()
    
    time.sleep(0.5)
    
    # Test 6: Invalid token
    results["Invalid Token"] = test_invalid_token()
    
    time.sleep(0.5)
    
    # Test 7: Weak password
    results["Weak Password"] = test_weak_password()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"  {status:10} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Password reset flow is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    return results

if __name__ == "__main__":
    run_all_tests()
