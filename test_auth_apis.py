#!/usr/bin/env python3
"""
Test script for Authentication APIs
Run this script to test all auth endpoints
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_user_registration():
    """Test user registration endpoint"""
    print("🔍 Testing User Registration...")
    
    url = f"{BASE_URL}/auth/register/"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "password_confirm": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "risk_tolerance": "moderate",
        "investment_experience": "beginner",
        "initial_cash": "5000.00"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("Registration successful!")
            return response.json().get('token')
        else:
            print("Registration failed!")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def test_user_login():
    """Test user login endpoint"""
    print("\n🔍 Testing User Login...")
    
    url = f"{BASE_URL}/auth/login/"
    data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("Login successful!")
            return response.json().get('token')
        else:
            print("Login failed!")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def test_user_profile(token):
    """Test get user profile endpoint"""
    print("\n🔍 Testing User Profile...")
    
    url = f"{BASE_URL}/auth/profile/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("Profile retrieval successful!")
        else:
            print("Profile retrieval failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def test_portfolio_access(token):
    """Test accessing portfolio with authentication"""
    print("\n🔍 Testing Portfolio Access with Auth...")
    
    url = f"{BASE_URL}/portfolios/portfolio/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("Portfolio access successful!")
        else:
            print("Portfolio access failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def test_user_logout(token):
    """Test user logout endpoint"""
    print("\n🔍 Testing User Logout...")
    
    url = f"{BASE_URL}/auth/logout/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.post(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("Logout successful!")
        else:
            print("Logout failed!")
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def test_unauthorized_access():
    """Test accessing protected endpoints without authentication"""
    print("\n Testing Unauthorized Access...")
    
    url = f"{BASE_URL}/portfolios/portfolio/"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("Unauthorized access properly blocked!")
        else:
            print("Security issue: unauthorized access allowed!")
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def main():
    """Run all authentication tests"""
    print("Starting Authentication API Tests...")
    print("=" * 50)
    
    # Test 1: User Registration
    token = test_user_registration()
    
    if token:
        # Test 2: User Profile (with token from registration)
        test_user_profile(token)
        
        # Test 3: Portfolio Access (authenticated)
        test_portfolio_access(token)
        
        # Test 4: User Logout
        test_user_logout(token)
    
    # Test 5: User Login (separate from registration)
    login_token = test_user_login()
    
    if login_token:
        # Test 6: Profile with login token
        test_user_profile(login_token)
    
    # Test 7: Unauthorized access
    test_unauthorized_access()
    
    print("\n" + "=" * 50)
    print("Authentication tests completed!")

if __name__ == "__main__":
    main()