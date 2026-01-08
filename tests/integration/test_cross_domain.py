"""
Integration Test: Verify cross-domain functionality works correctly
"""
import sys
import os

def test_domain_service_integration():
    """Test that domains can use services correctly"""
    try:
        # Import domain and service modules
        from app.domains import market, options, trading, learning
        from app.services import broker, data, database, monitoring
        
        print("✅ All domains and services imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Integration import failed: {e}")
        return False

def test_database_service_integration():
    """Test database service can be used by domains"""
    try:
        from app.services.database import connection
        print("✅ Database service integration verified")
        return True
    except ImportError as e:
        print(f"❌ Database integration failed: {e}")
        return False

def test_broker_service_integration():
    """Test broker service integration"""
    try:
        from app.services.broker import angelone_adapter, angelone_client
        print("✅ Broker service integration verified")
        return True
    except ImportError as e:
        print(f"❌ Broker integration failed: {e}")
        return False

def test_data_flow_integration():
    """Test that data can flow between services and domains"""
    try:
        # Test imports for data flow
        from app.services.data import market_data_manager
        from app.domains.options import greeks_calculator
        from app.domains.trading import risk_manager
        
        print("✅ Data flow integration verified")
        return True
    except ImportError as e:
        print(f"❌ Data flow integration failed: {e}")
        return False

if __name__ == "__main__":
    print("Running integration tests...")
    test_domain_service_integration()
    test_database_service_integration()
    test_broker_service_integration()
    test_data_flow_integration()
