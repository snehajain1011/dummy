#!/usr/bin/env python3
"""
Test Runner - Runs all test suites
"""

import asyncio
import sys
import time
from loguru import logger

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")

async def run_auth_tests():
    """Run authentication tests"""
    print(f"\n{'='*80}")
    print(f"🔐 RUNNING AUTHENTICATION TESTS")
    print(f"{'='*80}")
    
    try:
        from test_auth_complete import AuthTestSuite
        auth_suite = AuthTestSuite()
        await auth_suite.run_all_tests()
        return True
    except Exception as e:
        print(f"❌ Auth tests failed: {e}")
        return False

async def run_sse_tests():
    """Run SSE tests"""
    print(f"\n{'='*80}")
    print(f"📡 RUNNING SSE TESTS")
    print(f"{'='*80}")
    
    try:
        from test_sse_complete import SSETestSuite
        sse_suite = SSETestSuite()
        await sse_suite.run_all_tests()
        return True
    except Exception as e:
        print(f"❌ SSE tests failed: {e}")
        return False

async def main():
    """Main test runner"""
    print(f"\n🚀 STARTING COMPLETE TEST SUITE")
    print(f"⏰ Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    results = {}
    
    # Run auth tests
    print(f"\n📋 Running authentication tests...")
    results['auth'] = await run_auth_tests()
    
    # Wait between test suites
    await asyncio.sleep(2)
    
    # Run SSE tests
    print(f"\n📋 Running SSE tests...")
    results['sse'] = await run_sse_tests()
    
    # Final summary
    duration = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"🎉 ALL TESTS COMPLETED")
    print(f"{'='*80}")
    print(f"⏱️ Total duration: {duration:.2f} seconds")
    print(f"🔐 Auth tests: {'✅ PASSED' if results['auth'] else '❌ FAILED'}")
    print(f"📡 SSE tests: {'✅ PASSED' if results['sse'] else '❌ FAILED'}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📊 FINAL RESULT: {passed}/{total} test suites passed")
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())