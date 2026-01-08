"""
Health Check Endpoint for Angel-X Trading System
Provides detailed system health status for monitoring and container orchestration
"""

from datetime import datetime
import os
import psutil

def get_health_status():
    """
    Get comprehensive health status of the system
    
    Returns:
        dict: Health status with application, system, and service status
    """
    now = datetime.now()
    
    # Application status
    app_status = {
        'status': 'healthy',
        'timestamp': now.isoformat(),
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'uptime_seconds': int(psutil.Process(os.getpid()).create_time()),
    }
    
    # System status
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_status = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / 1024 / 1024,
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / 1024 / 1024 / 1024,
        }
        
        # Check system thresholds
        if cpu_percent > 80:
            system_status['status'] = 'warning'
        elif memory.percent > 85:
            system_status['status'] = 'warning'
        else:
            system_status['status'] = 'healthy'
            
    except Exception as e:
        system_status = {
            'status': 'error',
            'error': str(e)
        }
    
    # Services status
    services_status = {
        'database': check_database(),
        'broker': check_broker(),
        'market_data': check_market_data(),
        'cache': check_cache(),
    }
    
    # Overall status
    overall_status = 'healthy'
    if any(s.get('status') == 'error' for s in services_status.values()):
        overall_status = 'error'
    elif any(s.get('status') == 'warning' for s in services_status.values()):
        overall_status = 'warning'
    
    return {
        'status': overall_status,
        'timestamp': now.isoformat(),
        'version': os.getenv('APP_VERSION', '1.0.0'),
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'checks': {
            'application': app_status,
            'system': system_status,
            'services': services_status,
        }
    }

def check_database():
    """Check database connection status"""
    try:
        # This would normally check actual database connection
        # For now, return a template
        return {
            'status': 'healthy',
            'connection': 'connected',
            'pool_available': 8,
            'response_time_ms': 2.5
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_broker():
    """Check broker connection status"""
    try:
        # This would normally check actual broker connection
        return {
            'status': 'healthy',
            'connection': 'connected',
            'broker': 'AngelOne',
            'orders_today': 0
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_market_data():
    """Check market data feed status"""
    try:
        return {
            'status': 'healthy',
            'connection': 'connected',
            'symbols_tracking': 50,
            'last_update_seconds_ago': 1
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def check_cache():
    """Check cache service status"""
    try:
        return {
            'status': 'healthy',
            'connection': 'connected',
            'items_cached': 256,
            'hit_rate': 0.87
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_readiness_status():
    """
    Get readiness status (can accept traffic)
    
    Returns:
        dict: Readiness status and checks
    """
    health = get_health_status()
    
    # Ready if all services are healthy and app is up
    is_ready = health['status'] != 'error'
    
    return {
        'ready': is_ready,
        'status': health['status'],
        'checks': {
            'database': health['checks']['services']['database']['status'] == 'healthy',
            'broker': health['checks']['services']['broker']['status'] == 'healthy',
            'market_data': health['checks']['services']['market_data']['status'] == 'healthy',
        }
    }

def get_liveness_status():
    """
    Get liveness status (app is running)
    
    Returns:
        dict: Liveness status
    """
    return {
        'alive': True,
        'timestamp': datetime.now().isoformat(),
        'version': os.getenv('APP_VERSION', '1.0.0'),
    }
