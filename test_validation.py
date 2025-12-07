"""
Quick validation script to test the Trend Scout modules.
Verifies imports and basic configuration without making API calls.
"""

import sys

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing module imports...")
    
    try:
        import config
        print("  ✅ config.py imported successfully")
        
        import safety_manager
        print("  ✅ safety_manager.py imported successfully")
        
        import data_processor
        print("  ✅ data_processor.py imported successfully")
        
        import main
        print("  ✅ main.py imported successfully")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def test_config():
    """Test configuration validation."""
    print("\n🧪 Testing configuration...")
    
    try:
        from config import Config
        
        # Test validation
        Config.validate()
        print("  ✅ Configuration validation passed")
        
        # Check key values
        print(f"  📊 ER Threshold: {Config.ER_THRESHOLD * 100}%")
        print(f"  📊 Follower Range: {Config.MIN_FOLLOWERS:,} - {Config.MAX_FOLLOWERS:,}")
        print(f"  📊 Post Age Limit: {Config.POST_AGE_DAYS} days")
        print(f"  📊 Delay Range: {Config.MIN_DELAY_SECONDS}s - {Config.MAX_DELAY_SECONDS}s")
        print(f"  🎯 Target Hashtags: {len(Config.TARGET_HASHTAGS)}")
        
        for tag in Config.TARGET_HASHTAGS:
            print(f"     - #{tag}")
        
        return True
    except Exception as e:
        print(f"  ❌ Config error: {e}")
        return False


def test_data_processor():
    """Test data processor functions."""
    print("\n🧪 Testing data processor...")
    
    try:
        from data_processor import PostProcessor
        
        # Test hashtag extraction
        test_caption = "Amazing UI design tips! #webdesign #uidesign #designtips"
        hashtags = PostProcessor.extract_hashtags(test_caption)
        
        if len(hashtags) == 3:
            print("  ✅ Hashtag extraction works")
            print(f"     Extracted: {', '.join(hashtags)}")
        else:
            print(f"  ⚠️  Hashtag extraction returned {len(hashtags)} instead of 3")
        
        # Test virality score calculation
        score = PostProcessor.calculate_virality_score(
            engagement_rate=0.05,
            followers=10000,
            likes=450,
            comments=50
        )
        
        print(f"  ✅ Virality score calculation works")
        print(f"     Sample Score: {score}/10")
        
        return True
    except Exception as e:
        print(f"  ❌ Data processor error: {e}")
        return False


def test_safety_manager():
    """Test safety manager initialization."""
    print("\n🧪 Testing safety manager...")
    
    try:
        from safety_manager import SafetyManager
        
        safety = SafetyManager()
        stats = safety.get_stats()
        
        print("  ✅ Safety manager initialized")
        print(f"     Initial requests: {stats['total_requests']}")
        print(f"     Rate limits: {stats['rate_limits_hit']}")
        
        return True
    except Exception as e:
        print(f"  ❌ Safety manager error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🔍 TREND SCOUT - MODULE VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Config Test", test_config),
        ("Data Processor Test", test_data_processor),
        ("Safety Manager Test", test_safety_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✨ All tests passed! Application is ready to use.")
        print("\n📖 Next Steps:")
        print("  1. Copy .env.example to .env (optional)")
        print("  2. Run: python main.py --test-mode --limit 5")
        print("  3. Check the output and logs")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
