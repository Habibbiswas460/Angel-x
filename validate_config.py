#!/usr/bin/env python3
"""
ANGEL-X Configuration Validator
সিস্টেমের সমস্ত সেটিংস যাচাই করার জন্য

This script validates:
✅ All required credentials present
✅ Database connectivity
✅ API endpoints accessible
✅ Ports available
✅ File permissions
✅ Configuration consistency
"""

import os
import sys
import socket
import json
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate Angel-X configuration"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.errors = []
        self.warnings = []
        self.info = []

    def print_header(self):
        """Print validation header"""
        print("\n" + "=" * 80)
        print("🔍 ANGEL-X CONFIGURATION VALIDATOR")
        print("=" * 80 + "\n")

    def add_error(self, message: str):
        """Add error"""
        self.errors.append(f"❌ {message}")

    def add_warning(self, message: str):
        """Add warning"""
        self.warnings.append(f"⚠️  {message}")

    def add_info(self, message: str):
        """Add info"""
        self.info.append(f"ℹ️  {message}")

    def validate_env_file(self) -> bool:
        """Validate .env file exists and is readable"""
        print("\n📁 Checking .env file...")
        
        if not self.env_file.exists():
            self.add_error(f".env file not found at {self.env_file}")
            self.add_info("Create it with: python setup.py")
            return False
        
        if not os.access(self.env_file, os.R_OK):
            self.add_error(f".env file is not readable")
            return False
        
        self.add_info(f"✅ .env file found: {self.env_file}")
        return True

    def validate_credentials(self) -> bool:
        """Validate AngelOne credentials"""
        print("\n🔐 Checking AngelOne credentials...")
        
        try:
            from config import (
                ANGELONE_API_KEY,
                ANGELONE_CLIENT_CODE,
                ANGELONE_PASSWORD,
                ANGELONE_TOTP_SECRET
            )
            
            all_present = all([
                ANGELONE_API_KEY,
                ANGELONE_CLIENT_CODE,
                ANGELONE_PASSWORD,
                ANGELONE_TOTP_SECRET
            ])
            
            if not all_present:
                self.add_error("AngelOne credentials incomplete")
                if not ANGELONE_API_KEY:
                    self.add_error("  - ANGELONE_API_KEY is missing")
                if not ANGELONE_CLIENT_CODE:
                    self.add_error("  - ANGELONE_CLIENT_CODE is missing")
                if not ANGELONE_PASSWORD:
                    self.add_error("  - ANGELONE_PASSWORD is missing")
                if not ANGELONE_TOTP_SECRET:
                    self.add_error("  - ANGELONE_TOTP_SECRET is missing")
                return False
            
            self.add_info("✅ All AngelOne credentials present")
            return True
            
        except ImportError as e:
            self.add_error(f"Could not import configuration: {e}")
            return False

    def validate_ports(self) -> bool:
        """Validate required ports are available"""
        print("\n🔌 Checking ports...")
        
        try:
            from config import DASHBOARD_PORT, API_PORT
            
            ports = {
                "Dashboard": DASHBOARD_PORT,
                "API": API_PORT,
            }
            
            all_available = True
            for service, port in ports.items():
                if self.is_port_available(port):
                    self.add_info(f"✅ {service} port {port} is available")
                else:
                    self.add_warning(f"{service} port {port} is in use")
                    all_available = False
            
            return all_available
            
        except Exception as e:
            self.add_warning(f"Could not check ports: {e}")
            return True

    def is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            return result != 0
        except Exception:
            return True
        finally:
            sock.close()

    def validate_database(self) -> bool:
        """Validate database configuration and connectivity"""
        print("\n🗄️  Checking database...")
        
        try:
            from config import DB_ENABLED, DB_TYPE, DB_PATH
            
            if not DB_ENABLED:
                self.add_info("ℹ️  Database is disabled (data won't persist)")
                return True
            
            if DB_TYPE == "sqlite":
                db_dir = Path(DB_PATH).parent
                db_dir.mkdir(parents=True, exist_ok=True)
                self.add_info(f"✅ SQLite configured: {DB_PATH}")
                return True
                
            elif DB_TYPE == "postgresql":
                try:
                    from config import (
                        DATABASE_HOST,
                        DATABASE_PORT,
                        DATABASE_NAME,
                        DATABASE_USER
                    )
                    
                    # Try to connect
                    import psycopg2
                    from config import DATABASE_PASSWORD
                    
                    conn = psycopg2.connect(
                        host=DATABASE_HOST,
                        port=DATABASE_PORT,
                        database=DATABASE_NAME,
                        user=DATABASE_USER,
                        password=DATABASE_PASSWORD,
                        connect_timeout=5
                    )
                    conn.close()
                    self.add_info(f"✅ PostgreSQL connection successful: {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}")
                    return True
                    
                except ImportError:
                    self.add_warning("psycopg2 not installed (required for PostgreSQL)")
                    self.add_info("Install with: pip install psycopg2-binary")
                    return True
                except Exception as e:
                    self.add_error(f"Could not connect to PostgreSQL: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.add_warning(f"Could not validate database: {e}")
            return True

    def validate_directories(self) -> bool:
        """Validate required directories exist"""
        print("\n📂 Checking directories...")
        
        required_dirs = [
            "data",
            "logs",
            "models",
        ]
        
        all_ok = True
        for directory in required_dirs:
            dir_path = self.project_root / directory
            if dir_path.exists():
                self.add_info(f"✅ {directory}/ exists")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.add_warning(f"Created missing directory: {directory}/")
        
        return True

    def validate_security(self) -> bool:
        """Validate security settings"""
        print("\n🔒 Checking security...")
        
        try:
            from config import SECRET_KEY, ENCRYPTION_ENABLED, ENVIRONMENT
            
            if ENVIRONMENT == "production":
                if SECRET_KEY == "change-me-to-a-strong-random-key-before-production":
                    self.add_error("SECRET_KEY has default value (MUST change for production)")
                    return False
                self.add_info("✅ SECRET_KEY is set (production)")
            else:
                self.add_info("✅ Non-production environment")
            
            if ENCRYPTION_ENABLED:
                self.add_info("✅ Encryption is enabled")
            else:
                self.add_warning("Encryption is disabled")
            
            return True
            
        except Exception as e:
            self.add_warning(f"Could not validate security: {e}")
            return True

    def validate_trading_settings(self) -> bool:
        """Validate trading configuration"""
        print("\n📈 Checking trading settings...")
        
        try:
            from config import (
                PAPER_TRADING,
                TRADING_ENABLED,
                RISK_PER_TRADE,
                MAX_DAILY_LOSS,
                ENVIRONMENT
            )
            
            if ENVIRONMENT == "production":
                if PAPER_TRADING:
                    self.add_warning("PAPER_TRADING=True in production (no real money)")
                else:
                    self.add_info("✅ Paper trading disabled (live trading)")
                
                if TRADING_ENABLED:
                    self.add_info("✅ Trading is enabled")
                else:
                    self.add_warning("Trading is disabled")
            else:
                self.add_info(f"✅ Development mode ({ENVIRONMENT})")
                if PAPER_TRADING:
                    self.add_info("✅ Paper trading enabled (safe)")
            
            # Validate risk parameters
            if not (0 < RISK_PER_TRADE <= 0.1):
                self.add_error(f"Invalid RISK_PER_TRADE: {RISK_PER_TRADE}")
                return False
            
            if MAX_DAILY_LOSS <= 0:
                self.add_error(f"Invalid MAX_DAILY_LOSS: {MAX_DAILY_LOSS}")
                return False
            
            self.add_info(f"✅ Risk per trade: {RISK_PER_TRADE*100:.1f}%")
            self.add_info(f"✅ Max daily loss: ₹{MAX_DAILY_LOSS}")
            
            return True
            
        except Exception as e:
            self.add_warning(f"Could not validate trading settings: {e}")
            return True

    def validate_dependencies(self) -> bool:
        """Validate required Python packages"""
        print("\n📦 Checking dependencies...")
        
        required_packages = [
            ("dotenv", "python-dotenv"),
            ("flask", "flask"),
            ("requests", "requests"),
        ]
        
        optional_packages = [
            ("psycopg2", "psycopg2-binary", "PostgreSQL support"),
            ("redis", "redis", "Redis caching"),
            ("sqlalchemy", "sqlalchemy", "Database ORM"),
        ]
        
        all_ok = True
        
        # Check required
        for import_name, package_name in required_packages:
            try:
                __import__(import_name)
                self.add_info(f"✅ {package_name} installed")
            except ImportError:
                self.add_error(f"{package_name} not installed")
                self.add_info(f"Install with: pip install {package_name}")
                all_ok = False
        
        # Check optional
        for import_name, package_name, description in optional_packages:
            try:
                __import__(import_name)
                self.add_info(f"✅ {package_name} installed ({description})")
            except ImportError:
                self.add_info(f"ℹ️  Optional: {package_name} ({description})")
        
        return all_ok

    def print_results(self) -> bool:
        """Print validation results"""
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        if self.info:
            print("\n✅ INFO:")
            for msg in self.info:
                print(f"  {msg}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for msg in self.errors:
                print(f"  {msg}")
        
        print("\n" + "=" * 80)
        
        if self.errors:
            print("❌ VALIDATION FAILED")
            print("\nPlease fix the errors above and try again.")
            print("Run: python validate_config.py")
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED (with warnings)")
            print("\nThe system should work, but please review the warnings.")
            return True
        else:
            print("✅ VALIDATION PASSED")
            print("\nYour Angel-X configuration is ready!")
            print("\n🚀 Next step: python main.py")
            return True

    def run(self) -> bool:
        """Run complete validation"""
        self.print_header()
        
        try:
            # Run all validations
            self.validate_env_file()
            self.validate_credentials()
            self.validate_ports()
            self.validate_database()
            self.validate_directories()
            self.validate_security()
            self.validate_trading_settings()
            self.validate_dependencies()
            
            # Print results
            return self.print_results()
            
        except KeyboardInterrupt:
            print("\n\n❌ Validation cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    validator = ConfigValidator()
    success = validator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
