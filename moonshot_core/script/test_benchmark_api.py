#!/usr/bin/env python3
"""Quick test script for /api/run-benchmark endpoint.

This script tests the /api/run-benchmark endpoint by sending multiple requests
sequentially and in parallel to verify that background tasks work correctly.

Usage:
    cd moonshot_core
    python script/test_benchmark_api.py

Prerequisites:
    - FastAPI server should be running (e.g., via run_api.py)
    - Default URL is http://localhost:8000 (modify API_URL if different)
"""

import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
API_URL = "http://localhost:8000/api/run-benchmark"
DEFAULT_DATASET = "test_sample_dataset"
DEFAULT_METRIC = "accuracy_adapter"
DEFAULT_CONNECTOR = "my-gpt-4o"


def test_benchmark(test_name, dataset=DEFAULT_DATASET, 
                   metric=DEFAULT_METRIC, connector=DEFAULT_CONNECTOR):
    """Test a single benchmark request.
    
    Args:
        test_name: Unique identifier for the test
        dataset: Dataset name to use
        metric: Metric name to use
        connector: Connector name to use
        
    Returns:
        dict: Response JSON or None if error
    """
    payload = {
        "test_name": test_name,
        "dataset": dataset,
        "metric": metric,
        "connector": connector
    }
    
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        elapsed = time.time() - start_time
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {test_name}: "
              f"Status {response.status_code} (took {elapsed:.2f}s)")
        if response.status_code == 200:
            result = response.json()
            print(f"  Response: {result}")
            return result
        else:
            print(f"  Error: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {test_name}: "
              f"ERROR - Could not connect to {API_URL}")
        print("  Make sure the FastAPI server is running!")
        return None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {test_name}: ERROR - {e}")
        return None


def test_single_request():
    """Test a single benchmark request."""
    print("=" * 60)
    print("Test 1: Single request")
    print("=" * 60)
    test_benchmark("single_test")
    time.sleep(1)


def test_sequential_requests(num_requests=3):
    """Test multiple sequential requests.
    
    Args:
        num_requests: Number of sequential requests to send
    """
    print("\n" + "=" * 60)
    print(f"Test 2: Multiple sequential requests ({num_requests})")
    print("=" * 60)
    for i in range(1, num_requests + 1):
        test_benchmark(f"sequential_test_{i}")
        time.sleep(0.5)  # Small delay between requests


def test_parallel_requests(num_requests=5):
    """Test multiple parallel requests.
    
    Args:
        num_requests: Number of parallel requests to send
    """
    print("\n" + "=" * 60)
    print(f"Test 3: Multiple parallel requests ({num_requests})")
    print("=" * 60)
    print("(All requests should return quickly since they run in background)")
    
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [
            executor.submit(test_benchmark, f"parallel_test_{i}")
            for i in range(1, num_requests + 1)
        ]
        
        results = []
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    print(f"\nCompleted {len([r for r in results if r])} out of {num_requests} requests")
    return results


def main():
    """Main test function."""
    print("=" * 60)
    print("Testing /api/run-benchmark endpoint")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Default dataset: {DEFAULT_DATASET}")
    print(f"Default metric: {DEFAULT_METRIC}")
    print(f"Default connector: {DEFAULT_CONNECTOR}")
    print()
    
    # Test 1: Single request
    test_single_request()
    
    # Test 2: Sequential requests
    test_sequential_requests(3)
    
    # Test 3: Parallel requests
    test_parallel_requests(5)
    
    print("\n" + "=" * 60)
    print("All tests submitted!")
    print("=" * 60)
    print("\nNote: The actual benchmarks run in the background.")
    print("Check the following to verify execution:")
    print("  1. Server logs for [BenchmarkExecutionService] messages")
    print("  2. data/results/ directory for new JSON result files")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
