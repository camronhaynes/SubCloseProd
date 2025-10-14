#!/usr/bin/env python3
"""
Quick test script for the Web API
Run this to verify the API endpoints work correctly
"""

import requests
import json

API_BASE = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health check passed:", response.json())
            return True
        else:
            print("✗ Health check failed:", response.status_code)
            return False
    except Exception as e:
        print(f"✗ Could not connect to API: {e}")
        print("\nMake sure the Flask server is running:")
        print("  cd backend/app/api && python3 server.py")
        return False


def test_parse_currency():
    """Test currency parsing"""
    print("\n2. Testing Currency Parser...")
    test_values = ["10m", "5M", "2.5m", "500k", "$1,000,000"]

    for value in test_values:
        try:
            response = requests.post(
                f"{API_BASE}/api/parse/currency",
                json={"value": value},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ '{value}' → {result['formatted']}")
            else:
                print(f"  ✗ Failed to parse '{value}': {response.text}")
        except Exception as e:
            print(f"  ✗ Error parsing '{value}': {e}")


def test_parse_date():
    """Test date parsing"""
    print("\n3. Testing Date Parser...")
    test_dates = ["1/15/22", "Jan 15 2023", "2023-01-15"]

    for date_str in test_dates:
        try:
            response = requests.post(
                f"{API_BASE}/api/parse/date",
                json={"value": date_str},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ '{date_str}' → {result['formatted']}")
            else:
                print(f"  ✗ Failed to parse '{date_str}': {response.text}")
        except Exception as e:
            print(f"  ✗ Error parsing '{date_str}': {e}")


def test_calculate_json():
    """Test JSON calculation"""
    print("\n4. Testing JSON Calculation...")

    test_data = {
        "fund_name": "Test Fund IV",
        "capital_calls": [
            {"date": "1/15/22", "percentage": "10"},
            {"date": "6/15/22", "percentage": "15"},
            {"date": "12/15/22", "percentage": "20"}
        ],
        "partners": [
            {"name": "ABC Partners", "commitment": "5m", "close": 1, "issue_date": "1/15/22"},
            {"name": "XYZ Capital", "commitment": "5m", "close": 1, "issue_date": "1/15/22"},
            {"name": "New Investor LLC", "commitment": "3m", "close": 2, "issue_date": "7/1/22"}
        ],
        "prime_rate": "7.5",
        "spread": "2.0",
        "compounding": "simple"
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/calculate/text",
            json=test_data,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Calculation successful!")
            print(f"    Fund: {result['fund_name']}")
            print(f"    Total Collected: ${result['total_late_interest_collected']}")
            print(f"    Total Allocated: ${result['total_late_interest_allocated']}")
            print(f"    New LPs: {len(result['new_lps'])}")
            print(f"    Existing LPs: {len(result['existing_lps'])}")
        else:
            print(f"  ✗ Calculation failed: {response.text}")
    except Exception as e:
        print(f"  ✗ Error during calculation: {e}")


def main():
    print("=" * 80)
    print("Late Interest Engine - API Test Suite".center(80))
    print("=" * 80)

    # Test health first
    if not test_health():
        return 1

    # Run all tests
    test_parse_currency()
    test_parse_date()
    test_calculate_json()

    print("\n" + "=" * 80)
    print("All Tests Completed!".center(80))
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Keep the Flask server running")
    print("  2. In a new terminal, start the frontend:")
    print("     cd frontend && npm install && npm run dev")
    print("  3. Open http://localhost:3000 in your browser")
    print("=" * 80 + "\n")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
