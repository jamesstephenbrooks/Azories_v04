#!/usr/bin/env python3
"""
Performance Testing Script for Azories API
Tests GET endpoints across multiple backend providers
"""

import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
ITERATIONS = 5  # Reduced iterations for faster testing
TIMEOUT = 10  # Request timeout in seconds

# Base URLs for different providers
PROVIDERS = {
    "preview": "https://azories-preview.preview.emergentagent.com",
    "caddy": "https://azories-preview.emergent.host",
    "cloudflare": "https://azories-preview.emergent.host"
}

# GET endpoints to test (prioritized list - core endpoints)
GET_ENDPOINTS = [
    # Health checks - critical
    ("/api/health", "Health Check"),
    ("/api/health/fal", "Health Check FAL"),
    
    # Authentication
    ("/api/auth/me", "Get Current User"),
    ("/api/auth/ai-story-trial", "AI Story Trial Info"),
    
    # Credits
    ("/api/credits/balance", "Get Credits Balance"),
    
    # Books - Most important
    ("/api/books", "Get All Books"),
    ("/api/books/featured", "Get Featured Books"),
    ("/api/books/newly-added", "Get Newly Added Books"),
    ("/api/books/coming-soon", "Get Coming Soon Books"),
    ("/api/books/my", "Get My Books"),
    
    # Series
    ("/api/series", "Get All Series"),
    
    # User/Profile
    ("/api/users/test-user-id/profile", "Get User Profile"),
    
    # Reading
    ("/api/reading-progress/test-book-id", "Get Reading Progress"),
    ("/api/reading-stats", "Get Reading Stats"),
    ("/api/continue-reading", "Get Continue Reading"),
    ("/api/user/recommendations", "Get Recommendations"),
    
    # Voices
    ("/api/voices", "Get Voices"),
    
    # Pro Studio
    ("/api/pro-studio/characters", "Get Pro Studio Characters"),
    ("/api/pro-studio/character-styles", "Get Character Styles"),
    
    # Content
    ("/api/genres", "Get Genres"),
    ("/api/age-ratings", "Get Age Ratings"),
    
    # Payments
    ("/api/payments/packages", "Get Payment Packages"),
    
    # Legal
    ("/api/legal/terms", "Get Terms"),
    ("/api/legal/privacy", "Get Privacy Policy"),
]


def test_endpoint_curl(url: str, timeout: int = TIMEOUT) -> Tuple[float, int, str]:
    """Test endpoint using curl and return latency and status code"""
    try:
        start = time.time()
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"--max-time", str(timeout), url],
            capture_output=True,
            timeout=timeout + 5,
            text=True
        )
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds
        
        try:
            status_code = int(result.stdout.strip())
        except:
            status_code = 0
            
        return elapsed, status_code, ""
    except subprocess.TimeoutExpired:
        return -1, 0, "Timeout"
    except Exception as e:
        return -1, 0, str(e)[:50]


def test_endpoint_iterations(
    provider_name: str,
    base_url: str,
    endpoint: str,
    iterations: int = ITERATIONS
) -> Dict:
    """Run multiple iterations of an endpoint test"""
    full_url = f"{base_url}{endpoint}"
    latencies = []
    error_msg = ""
    
    for i in range(iterations):
        latency, status_code, error = test_endpoint_curl(full_url)
        
        if latency >= 0:
            latencies.append(latency)
        else:
            error_msg = error
        
        # Small delay between requests
        time.sleep(0.2)
    
    if not latencies:
        return {
            "provider": provider_name,
            "latencyInMs": 0,
            "minLatencyInMs": 0,
            "maxLatencyInMs": 0,
            "error": error_msg if error_msg else "No successful requests"
        }
    
    return {
        "provider": provider_name,
        "latencyInMs": round(sum(latencies) / len(latencies), 2),
        "minLatencyInMs": round(min(latencies), 2),
        "maxLatencyInMs": round(max(latencies), 2)
    }


def run_performance_tests() -> Dict:
    """Run performance tests for all endpoints across all providers"""
    
    print("=" * 80)
    print("AZORIES API PERFORMANCE TEST")
    print("=" * 80)
    print(f"Test Date: {datetime.now().isoformat()}")
    print(f"Iterations per endpoint: {ITERATIONS}")
    print(f"Total endpoints: {len(GET_ENDPOINTS)}")
    print(f"Providers: {list(PROVIDERS.keys())}")
    print("=" * 80)
    
    results = []
    total_tests = len(GET_ENDPOINTS) * len(PROVIDERS)
    current_test = 0
    
    for endpoint, description in GET_ENDPOINTS:
        endpoint_result = {
            "description": description,
            "iterations": ITERATIONS,
            "route": endpoint,
            "backend_perf_result": []
        }
        
        print(f"\nTesting: {description:40} ({endpoint})")
        
        for provider_name, base_url in PROVIDERS.items():
            current_test += 1
            progress = (current_test / total_tests) * 100
            
            try:
                result = test_endpoint_iterations(provider_name, base_url, endpoint, ITERATIONS)
                endpoint_result["backend_perf_result"].append(result)
                
                latency = result.get("latencyInMs", "N/A")
                min_lat = result.get("minLatencyInMs", "N/A")
                max_lat = result.get("maxLatencyInMs", "N/A")
                status = "✓" if "error" not in result else "✗"
                
                print(f"  {status} {provider_name:12} - {latency:7}ms (min: {min_lat:7}, max: {max_lat:7})")
                
            except Exception as e:
                print(f"  ✗ {provider_name:12} - Error: {str(e)[:40]}")
                endpoint_result["backend_perf_result"].append({
                    "provider": provider_name,
                    "latencyInMs": 0,
                    "minLatencyInMs": 0,
                    "maxLatencyInMs": 0,
                    "error": str(e)[:40]
                })
        
        results.append(endpoint_result)
        print(f"  Progress: {progress:.1f}%")
    
    return results


def generate_report(results: List[Dict]) -> Dict:
    """Generate performance report"""
    
    test_date = datetime.now()
    
    report = {
        "appName": "azories-preview",
        "testDate": test_date.isoformat(),
        "previewUrl": PROVIDERS["preview"],
        "deployedUrl": PROVIDERS["caddy"],
        "result": results
    }
    
    return report


def main():
    """Main entry point"""
    try:
        # Run all performance tests
        results = run_performance_tests()
        
        # Generate report
        report = generate_report(results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        # Calculate averages per provider
        provider_stats = {}
        for provider in PROVIDERS.keys():
            latencies = []
            for endpoint_result in results:
                for perf_result in endpoint_result["backend_perf_result"]:
                    if perf_result.get("provider") == provider and perf_result.get("latencyInMs", 0) > 0:
                        latencies.append(perf_result["latencyInMs"])
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                provider_stats[provider] = {
                    "avg": round(avg_latency, 2),
                    "min": round(min(latencies), 2),
                    "max": round(max(latencies), 2),
                    "count": len(latencies)
                }
        
        print("\nAverage Latencies by Provider:")
        for provider, stats in provider_stats.items():
            print(f"  {provider:12} - Avg: {stats['avg']:7.2f}ms | Min: {stats['min']:7.2f}ms | Max: {stats['max']:7.2f}ms | Tests: {stats['count']}")
        
        # Save report to file
        output_file = "/app/performance_test_report.json"
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report saved to: {output_file}")
        print("=" * 80)
        
        # Print final report as JSON
        print("\nFinal Performance Report (JSON):")
        print(json.dumps(report, indent=2))
        
        return report
        
    except Exception as e:
        print(f"\n✗ Error during performance testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
