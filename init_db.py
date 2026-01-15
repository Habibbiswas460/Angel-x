#!/usr/bin/env python3
"""
Database initialization script for Angel-X trading system.

This script:
- Creates all database tables
- Verifies database connectivity
- Provides options to reset/migrate database
- Shows database schema information

Usage:
    python init_db.py                    # Initialize database
    python init_db.py --reset            # Drop and recreate tables
    python init_db.py --info             # Show database info
    python init_db.py --test-connection  # Test DB connection only
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.base import (
    init_database,
    check_database_connection,
    get_database_info,
    Base,
    engine,
)
from src.database.models import Trade, Performance, MarketData, AccountHistory


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_header(title):
    """Print a formatted header."""
    print_separator()
    print(f"  {title}")
    print_separator()
    print()


def show_database_info():
    """Show database configuration and schema information."""
    print_header("📊 DATABASE INFORMATION")
    
    info = get_database_info()
    
    print(f"Database Type:     {info['type']}")
    print(f"Connection URL:    {info['url']}")
    
    if info['type'] == 'postgresql':
        print(f"Pool Size:         {info['pool_size']}")
        print(f"Max Overflow:      {info['max_overflow']}")
    
    print(f"Echo SQL:          {info['echo']}")
    print()
    
    if info['tables']:
        print(f"📋 Existing Tables ({len(info['tables'])}):")
        for table_name in sorted(info['tables']):
            print(f"   • {table_name}")
    else:
        print("📋 No tables found (database not initialized)")
    
    print()


def test_connection():
    """Test database connection."""
    print_header("🔌 TESTING DATABASE CONNECTION")
    
    print("Attempting to connect to database...")
    
    if check_database_connection():
        print("✅ Database connection successful!")
        print()
        return True
    else:
        print("❌ Database connection failed!")
        print("Please check your configuration in .env file.")
        print()
        return False


def create_tables(reset=False):
    """Create database tables."""
    if reset:
        print_header("⚠️  RESETTING DATABASE")
        response = input("This will DELETE all existing data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return False
        print()
    else:
        print_header("📊 INITIALIZING DATABASE")
    
    try:
        init_database(drop_existing=reset)
        print("✅ Database initialized successfully!")
        print()
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


def show_schema_details():
    """Show detailed schema information for all models."""
    print_header("📋 DATABASE SCHEMA DETAILS")
    
    models = [
        ("trades", Trade, "Trade records with entry/exit, P&L, and Greeks"),
        ("performance", Performance, "Daily/weekly/monthly performance metrics"),
        ("market_data", MarketData, "OHLC data and Greeks snapshots"),
        ("account_history", AccountHistory, "Account balance and transaction history"),
    ]
    
    for table_name, model, description in models:
        print(f"📄 {table_name}")
        print(f"   {description}")
        print(f"   Columns: {len(model.__table__.columns)}")
        print(f"   Indexes: {len([idx for idx in model.__table__.indexes])}")
        print()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Initialize Angel-X trading database"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: deletes all data)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show database configuration information"
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test database connection only"
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Show detailed schema information"
    )
    
    args = parser.parse_args()
    
    # Show info if requested
    if args.info:
        show_database_info()
        return
    
    # Show schema if requested
    if args.schema:
        show_schema_details()
        return
    
    # Test connection if requested
    if args.test_connection:
        success = test_connection()
        sys.exit(0 if success else 1)
    
    # Main initialization flow
    print_header("🚀 ANGEL-X DATABASE INITIALIZATION")
    
    # Step 1: Test connection
    print("Step 1: Testing database connection...")
    if not check_database_connection():
        print("❌ Cannot connect to database. Please check configuration.")
        sys.exit(1)
    print("✅ Connection successful")
    print()
    
    # Step 2: Create tables
    print("Step 2: Creating database tables...")
    if not create_tables(reset=args.reset):
        sys.exit(1)
    
    # Step 3: Show summary
    print("Step 3: Database summary")
    show_database_info()
    
    # Success
    print_separator()
    print()
    print("🎉 Database initialization complete!")
    print()
    print("Next steps:")
    print("  1. Start the trading system: python main.py")
    print("  2. View database info: python init_db.py --info")
    print("  3. Check schema: python init_db.py --schema")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
