#!/usr/bin/env python3
"""
Test script for Arkime MCP Server.

This script verifies that the package structure is correct and modules can be imported.
"""

import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from arkime_mcp_server.client import ArkimeClient, DigestAuth
        print("  ✓ Client module")
    except Exception as e:
        print(f"  ✗ Client module: {e}")
        return False

    try:
        from arkime_mcp_server.config import Config
        print("  ✓ Config module")
    except Exception as e:
        print(f"  ✗ Config module: {e}")
        return False

    try:
        from arkime_mcp_server.utils import (
            format_bytes,
            format_timestamp,
            protocol_name,
            summarize_session
        )
        print("  ✓ Utils module")
    except Exception as e:
        print(f"  ✗ Utils module: {e}")
        return False

    return True


def test_utils():
    """Test utility functions."""
    print("\nTesting utility functions...")

    from arkime_mcp_server.utils import format_bytes, protocol_name, format_timestamp

    # Test format_bytes
    assert format_bytes(1024) == "1.0 KB", "format_bytes(1024) failed"
    assert format_bytes(1048576) == "1.0 MB", "format_bytes(1048576) failed"
    assert format_bytes(0) == "0 B", "format_bytes(0) failed"
    print("  ✓ format_bytes()")

    # Test protocol_name
    assert protocol_name(6) == "TCP", "protocol_name(6) failed"
    assert protocol_name(17) == "UDP", "protocol_name(17) failed"
    assert protocol_name(1) == "ICMP", "protocol_name(1) failed"
    print("  ✓ protocol_name()")

    # Test format_timestamp
    assert format_timestamp(None) == "—", "format_timestamp(None) failed"
    assert format_timestamp(1000000000000) != "—", "format_timestamp with value failed"
    print("  ✓ format_timestamp()")

    return True


def test_digest_auth():
    """Test DigestAuth class."""
    print("\nTesting DigestAuth class...")

    from arkime_mcp_server.client import DigestAuth

    auth = DigestAuth("testuser", "testpass")
    assert auth.username == "testuser", "DigestAuth username failed"
    assert auth.password == "testpass", "DigestAuth password failed"
    print("  ✓ DigestAuth initialization")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Arkime MCP Server - Package Tests")
    print("=" * 60)

    tests = [
        ("Import Tests", test_imports),
        ("Utility Function Tests", test_utils),
        ("DigestAuth Tests", test_digest_auth),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
