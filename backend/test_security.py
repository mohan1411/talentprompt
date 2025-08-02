#!/usr/bin/env python3
"""
Security testing script for Promtitude
Run this to verify all security enhancements are working
"""

import requests
import time
import sys
import json
from urllib.parse import urljoin


class SecurityTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_security_headers(self):
        """Test if security headers are present."""
        print("\n🔍 Testing Security Headers...")
        
        response = self.session.get(f"{self.base_url}/api/v1/health")
        headers = response.headers
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": None,  # Just check existence
            "Content-Security-Policy": None,  # Just check existence
        }
        
        # Check for production-only headers
        if "production" in self.base_url:
            required_headers["Strict-Transport-Security"] = None
        
        missing_headers = []
        present_headers = []
        
        for header, expected_value in required_headers.items():
            if header in headers:
                if expected_value is None or headers[header] == expected_value:
                    present_headers.append(f"✓ {header}: {headers[header][:50]}...")
                else:
                    missing_headers.append(f"✗ {header}: Expected '{expected_value}', got '{headers[header]}'")
            else:
                missing_headers.append(f"✗ {header}: Missing")
        
        # Check that server header is removed
        if "Server" not in headers:
            present_headers.append("✓ Server header removed")
        else:
            missing_headers.append(f"✗ Server header still present: {headers.get('Server')}")
        
        for header in present_headers:
            print(f"  {header}")
        
        for header in missing_headers:
            print(f"  {header}")
        
        self.results.append({
            "test": "Security Headers",
            "passed": len(missing_headers) == 0,
            "details": {"present": len(present_headers), "missing": len(missing_headers)}
        })
    
    def test_rate_limiting(self):
        """Test rate limiting on login endpoint."""
        print("\n🔍 Testing Rate Limiting...")
        
        # Test login endpoint (5/minute)
        print("  Testing login endpoint (5 requests/minute limit)...")
        
        responses = []
        for i in range(7):
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": "test@example.com", "password": "wrongpass"}
            )
            responses.append(response.status_code)
            print(f"    Attempt {i+1}: Status {response.status_code}")
            time.sleep(0.5)
        
        # Check if rate limiting kicked in
        rate_limited = any(status == 429 for status in responses[5:])
        
        if rate_limited:
            print("  ✓ Rate limiting is working (429 status received)")
        else:
            print("  ✗ Rate limiting not detected (no 429 status)")
        
        self.results.append({
            "test": "Rate Limiting",
            "passed": rate_limited,
            "details": {"responses": responses}
        })
    
    def test_api_docs_disabled(self):
        """Test if API docs are disabled in production."""
        print("\n🔍 Testing API Documentation Access...")
        
        # Skip this test for localhost
        if "localhost" in self.base_url:
            print("  ⚠ Skipping docs test on localhost (should be enabled)")
            return
        
        docs_endpoints = ["/docs", "/redoc", "/api/v1/openapi.json"]
        blocked_count = 0
        
        for endpoint in docs_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint}")
            if response.status_code == 404:
                print(f"  ✓ {endpoint}: Blocked (404)")
                blocked_count += 1
            else:
                print(f"  ✗ {endpoint}: Accessible ({response.status_code})")
        
        all_blocked = blocked_count == len(docs_endpoints)
        
        self.results.append({
            "test": "API Docs Disabled",
            "passed": all_blocked,
            "details": {"blocked": blocked_count, "total": len(docs_endpoints)}
        })
    
    def test_cors_restrictions(self):
        """Test CORS restrictions."""
        print("\n🔍 Testing CORS Restrictions...")
        
        # Test with malicious origin
        headers = {"Origin": "https://malicious-site.com"}
        response = self.session.get(f"{self.base_url}/api/v1/health", headers=headers)
        
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        
        if cors_header == "https://malicious-site.com":
            print("  ✗ CORS allows any origin (security risk)")
            passed = False
        elif cors_header in ["*", None]:
            if cors_header == "*":
                print("  ✗ CORS uses wildcard (security risk)")
            else:
                print("  ✓ CORS header not set for unauthorized origin")
            passed = cors_header is None
        else:
            print(f"  ✓ CORS restricted to: {cors_header}")
            passed = True
        
        self.results.append({
            "test": "CORS Restrictions",
            "passed": passed,
            "details": {"cors_header": cors_header}
        })
    
    def test_auth_cache_headers(self):
        """Test cache headers on auth endpoints."""
        print("\n🔍 Testing Auth Endpoint Cache Headers...")
        
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": "test@example.com", "password": "test"}
        )
        
        cache_control = response.headers.get("Cache-Control")
        pragma = response.headers.get("Pragma")
        
        has_no_store = cache_control and "no-store" in cache_control
        has_no_cache = cache_control and "no-cache" in cache_control
        has_pragma = pragma == "no-cache"
        
        if has_no_store and has_no_cache:
            print("  ✓ Cache-Control: no-store, no-cache")
        else:
            print(f"  ✗ Cache-Control: {cache_control}")
        
        if has_pragma:
            print("  ✓ Pragma: no-cache")
        else:
            print(f"  ✗ Pragma: {pragma}")
        
        passed = has_no_store and has_no_cache and has_pragma
        
        self.results.append({
            "test": "Auth Cache Headers",
            "passed": passed,
            "details": {"cache_control": cache_control, "pragma": pragma}
        })
    
    def run_all_tests(self):
        """Run all security tests."""
        print(f"\n🔒 Security Testing for: {self.base_url}")
        print("=" * 60)
        
        self.test_security_headers()
        self.test_rate_limiting()
        self.test_api_docs_disabled()
        self.test_cors_restrictions()
        self.test_auth_cache_headers()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        
        for result in self.results:
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"{status} - {result['test']}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed < total:
            print("\n⚠️  Some security tests failed. Please review and fix the issues.")
            return False
        else:
            print("\n✅ All security tests passed!")
            return True


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Promtitude security features")
    parser.add_argument(
        "--url",
        default="http://localhost:8001",
        help="Base URL to test (default: http://localhost:8001)"
    )
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()