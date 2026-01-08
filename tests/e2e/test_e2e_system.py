"""
End-to-End System Tests
Tests complete ultra-professional architecture structure
"""
import pytest
import sys
from pathlib import Path


def test_e2e_app_package_structure():
    """TEST-0: Verify app package exists and is importable"""
    import app
    assert app is not None
    assert hasattr(app, '__path__')


def test_e2e_domains_layer():
    """TEST-1: Verify all 4 domains exist"""
    from app import domains
    assert domains is not None
    
    # Check domain subdirectories
    from app.domains import market, options, trading, learning
    assert all([market, options, trading, learning])


def test_e2e_services_layer():
    """TEST-2: Verify all 4 services exist"""
    from app import services
    assert services is not None
    
    # Check service subdirectories  
    from app.services import broker, data, database, monitoring
    assert all([broker, data, database, monitoring])


def test_e2e_api_layer():
    """TEST-3: API layer structure and components"""
    from app import api
    from app.api import routes, handlers, middleware, schemas
    
    assert all([api, routes, handlers, middleware, schemas])


def test_e2e_utils_layer():
    """TEST-4: Utility modules accessibility"""
    from app import utils
    from app.utils import logger, helpers, decorators, validators
    
    assert all([utils, logger, helpers, decorators, validators])


def test_e2e_monitoring_service():
    """TEST-5: Monitoring infrastructure complete"""
    from app.services.monitoring import health_checker
    from app.services.monitoring import metrics_collector
    from app.services.monitoring import performance_monitor
    from app.services.monitoring import alert_system
    
    assert all([health_checker, metrics_collector, performance_monitor, alert_system])


def test_e2e_database_service():
    """TEST-6: Database persistence layer"""
    from app.services.database import connection
    from app.services.database import repositories
    from app.services.database import schema
    
    assert all([connection, repositories, schema])


def test_e2e_import_path_migration():
    """TEST-7: Verify no old src.* imports remain in app/"""
    app_dir = Path('/home/lora/git_clone_projects/Angel-x/app')
    
    old_imports = []
    for py_file in app_dir.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        content = py_file.read_text()
        if 'from src.' in content or 'import src.' in content:
            old_imports.append(str(py_file))
    
    assert len(old_imports) == 0, f"Found old imports in: {old_imports}"


def test_e2e_architecture_completeness():
    """TEST-8: Verify complete ultra-professional structure"""
    base_path = Path('/home/lora/git_clone_projects/Angel-x')
    
    required_dirs = [
        base_path / 'app',
        base_path / 'app/domains',
        base_path / 'app/services',
        base_path / 'app/api',
        base_path / 'app/utils',
        base_path / 'tests',
        base_path / 'tests/unit',
        base_path / 'tests/integration',
        base_path / 'tests/e2e',
        base_path / 'infra',
        base_path / 'tools',
        base_path / 'docs',
    ]
    
    missing_dirs = [d for d in required_dirs if not d.exists()]
    assert len(missing_dirs) == 0, f"Missing directories: {missing_dirs}"
