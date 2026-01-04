#!/usr/bin/env python3
"""
Installation verification script for Angel-X v10.0.0
Tests all production components and dependencies
"""

import sys
import importlib

def check_python_version():
    """Verify Python version compatibility"""
    print("=" * 60)
    print("Angel-X Production Installation Verification")
    print("=" * 60)
    print()
    
    version = sys.version_info
    print(f"✓ Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERROR: Python 3.8+ required")
        return False
    
    if version.minor > 11:
        print("⚠ WARNING: Python 3.12+ not officially tested")
    
    print()
    return True

def check_imports():
    """Verify all Angel-X modules can be imported"""
    print("Checking Angel-X Module Imports:")
    print("-" * 60)
    
    modules_to_check = [
        # Core
        ("src", "Main package"),
        ("src.models", "Data models"),
        ("src.config", "Configuration"),
        ("src.__version__", "Version info"),
        
        # Core modules
        ("src.core", "Core trading"),
        ("src.engines", "Trading engines"),
        ("src.adaptive", "Adaptive learning"),
        ("src.dashboard", "Dashboard"),
        
        # Utilities
        ("src.utils.logger", "Logging"),
        ("src.utils.angelone_adapter", "AngelOne adapter"),
        ("src.utils.greeks_calculator", "Greeks calculator"),
    ]
    
    failed = []
    
    for module_name, description in modules_to_check:
        try:
            mod = importlib.import_module(module_name)
            print(f"✓ {description:.<40} OK")
        except ImportError as e:
            print(f"❌ {description:.<40} FAILED")
            failed.append((module_name, str(e)))
    
    print()
    
    if failed:
        print("❌ Import Failures:")
        for module, error in failed:
            print(f"   {module}: {error}")
        return False
    
    return True

def check_dependencies():
    """Verify required Python packages"""
    print("Checking Required Dependencies:")
    print("-" * 60)
    
    dependencies = [
        "pandas",
        "numpy",
        "requests",
        "websocket",
        "flask",
        "scipy",
        "sklearn",
    ]
    
    failed = []
    
    for package in dependencies:
        try:
            mod = importlib.import_module(package)
            version = getattr(mod, "__version__", "unknown")
            print(f"✓ {package:.<40} {version}")
        except ImportError:
            print(f"❌ {package:.<40} NOT INSTALLED")
            failed.append(package)
    
    print()
    
    if failed:
        print("❌ Missing Dependencies:")
        print(f"   Install with: pip install {' '.join(failed)}")
        return False
    
    return True

def check_version_info():
    """Display Angel-X version information"""
    try:
        from src import __version__, PHASE_STATUS, CAPABILITIES, get_full_version
        
        print("Angel-X Version Information:")
        print("-" * 60)
        print(f"Version: {__version__}")
        print()
        
        # Phase status
        completed = sum(1 for status in PHASE_STATUS.values() if status == "Complete")
        total = len(PHASE_STATUS)
        print(f"Phase Completion: {completed}/{total}")
        
        for phase, status in sorted(PHASE_STATUS.items()):
            emoji = "✅" if status == "Complete" else "⚠"
            print(f"  {emoji} {phase}: {status}")
        
        print()
        
        # Capabilities
        print(f"System Capabilities ({len(CAPABILITIES)}):")
        for i, capability in enumerate(CAPABILITIES, 1):
            print(f"  {i}. {capability}")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error loading version info: {e}")
        return False

def check_configuration():
    """Verify configuration files"""
    import os
    
    print("Configuration Status:")
    print("-" * 60)
    
    config_dir = "config"
    
    # Check config directory exists
    if not os.path.exists(config_dir):
        print(f"❌ Config directory not found: {config_dir}")
        return False
    
    print(f"✓ Config directory: {config_dir}")
    
    # Check for config files
    config_example = os.path.join(config_dir, "config.example.py")
    config_file = os.path.join(config_dir, "config.py")
    
    if os.path.exists(config_example):
        print(f"✓ Example config: {config_example}")
    else:
        print(f"❌ Missing: {config_example}")
    
    if os.path.exists(config_file):
        print(f"✓ User config: {config_file}")
    else:
        print(f"⚠ User config not found: {config_file}")
        print(f"   Copy from: cp {config_example} {config_file}")
    
    print()
    return True

def check_directories():
    """Verify required directories exist"""
    import os
    
    print("Directory Structure:")
    print("-" * 60)
    
    required_dirs = [
        ("src", "Source code"),
        ("config", "Configuration"),
        ("scripts", "Test scripts"),
        ("docs", "Documentation"),
        ("logs", "Log files"),
    ]
    
    for dir_path, description in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {description:.<40} {dir_path}")
        else:
            print(f"⚠ {description:.<40} {dir_path} (missing)")
            if dir_path == "logs":
                print(f"   Creating: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
    
    print()
    return True

def run_verification():
    """Run complete verification"""
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Angel-X Modules", check_imports),
        ("Dependencies", check_dependencies),
        ("Version Info", check_version_info),
        ("Configuration", check_configuration),
        ("Directories", check_directories),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results[name] = False
        print()
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:.<50} {name}")
    
    print()
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("🎉 Angel-X is production-ready!")
        print()
        print("Next steps:")
        print("1. Configure API credentials in config/config.py")
        print("2. Run: python3 scripts/test_credentials.py")
        print("3. Run: python3 scripts/test_adaptive_integration.py")
        print("4. Start trading: python3 main.py")
        print()
        return True
    else:
        print()
        print("⚠ Some checks failed. Please fix the issues above.")
        print()
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
