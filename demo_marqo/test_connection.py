#!/usr/bin/env python3
"""
Marqo Learning - Test Connection Script
Quick script to test if Marqo is running and accessible
"""

import requests
import marqo
import sys

def test_connection():
    print("🔗 Testing Marqo Connection")
    print("=" * 30)
    
    # Test raw HTTP connection
    try:
        response = requests.get("http://localhost:8882", timeout=5)
        print("✅ HTTP connection successful")
        print(f"   Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP connection failed: {e}")
        print("💡 Make sure Marqo is running: docker-compose up -d")
        return False
    
    # Test Marqo client
    try:
        mq = marqo.Client(url="http://localhost:8882")
        
        # Try to get Marqo version/info
        indexes = mq.get_indexes()
        print("✅ Marqo client connection successful")
        print(f"   Current indexes: {len(indexes['results'])}")
        
        # List existing indexes
        if indexes['results']:
            print("   Existing indexes:")
            for idx in indexes['results']:
                print(f"     - {idx}")
        else:
            print("   No existing indexes")
            
    except Exception as e:
        print(f"❌ Marqo client connection failed: {e}")
        return False
    
    print("\n🎉 Connection test passed!")
    print("🚀 Ready to run demos!")
    return True

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
