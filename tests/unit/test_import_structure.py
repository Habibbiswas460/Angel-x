"""
Unit Test: Verify new app/ structure imports work correctly
"""

def test_app_structure_imports():
    """Test that app package structure is importable"""
    try:
        import app
        import app.domains
        import app.services
        import app.utils
        assert hasattr(app, '__version__')
        print("✅ App structure imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_domain_imports():
    """Test that domain modules are accessible"""
    success = True
    domains = ['market', 'options', 'trading', 'learning']
    
    for domain in domains:
        try:
            module = __import__(f'app.domains.{domain}', fromlist=[''])
            print(f"✅ app.domains.{domain} imported")
        except ImportError as e:
            print(f"❌ app.domains.{domain} failed: {e}")
            success = False
    
    return success

def test_service_imports():
    """Test that service modules are accessible"""
    success = True
    services = ['broker', 'data', 'database', 'monitoring']
    
    for service in services:
        try:
            module = __import__(f'app.services.{service}', fromlist=[''])
            print(f"✅ app.services.{service} imported")
        except ImportError as e:
            print(f"❌ app.services.{service} failed: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    print("Running unit tests for app structure...")
    test_app_structure_imports()
    test_domain_imports()
    test_service_imports()
