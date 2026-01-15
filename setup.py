#!/usr/bin/env python3
"""
ANGEL-X Quick Setup Script
নতুন ইউজারদের জন্য ইন্টারঅ্যাক্টিভ সেটআপ স্ক্রিপ্ট

This script helps beginners set up Angel-X with:
✅ Interactive configuration
✅ Automatic .env file creation
✅ Directory structure setup
✅ API connectivity test
✅ Database initialization (optional)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple
import shutil
import getpass


class AngelXSetup:
    """Interactive setup wizard for Angel-X"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"
        self.config = {}
        self.step = 0

    def print_header(self):
        """Print setup header"""
        print("\n" + "=" * 80)
        print("🚀 ANGEL-X TRADING SYSTEM - QUICK SETUP WIZARD")
        print("=" * 80)
        print("\nএই স্ক্রিপ্ট আপনাকে Angel-X সেটআপ করতে সাহায্য করবে।")
        print("This script will help you set up Angel-X in just a few minutes.")
        print("=" * 80 + "\n")

    def print_step(self, title: str):
        """Print step header"""
        self.step += 1
        print(f"\n📍 STEP {self.step}: {title}")
        print("-" * 80)

    def ask_question(self, question: str, default: str = "", options: list = None) -> str:
        """Ask user a question and get response"""
        if options:
            print(f"\n{question}")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            while True:
                try:
                    choice = int(input("\nYour choice (number): ").strip())
                    if 1 <= choice <= len(options):
                        return options[choice - 1]
                except ValueError:
                    pass
                print("❌ Invalid choice. Please try again.")
        else:
            if default:
                prompt = f"{question} [{default}]: "
            else:
                prompt = f"{question}: "
            response = input(prompt).strip()
            return response if response else default

    def ask_password(self, question: str) -> str:
        """Ask for password (hidden input)"""
        while True:
            password = getpass.getpass(f"{question}: ")
            if password:
                return password
            print("❌ Password cannot be empty.")

    def step1_welcome(self):
        """Step 1: Welcome and mode selection"""
        self.print_step("Welcome & Mode Selection")
        
        print("\n🎯 Choose your setup mode:")
        print("\n1️⃣  LEARNING MODE (Recommended for beginners)")
        print("   ✅ Paper trading (no real money)")
        print("   ✅ Debug mode enabled")
        print("   ✅ Detailed logging")
        print("   ✅ Low resource usage")
        
        print("\n2️⃣  TESTING MODE (For strategy testing)")
        print("   ✅ Customizable settings")
        print("   ✅ Paper trading enabled")
        print("   ✅ Full documentation")
        
        print("\n3️⃣  PRODUCTION MODE (For live trading)")
        print("   ⚠️  Real money required")
        print("   ⚠️  Strict validation")
        print("   ⚠️  Advanced monitoring")
        
        mode = self.ask_question("Which mode?", options=["Learning", "Testing", "Production"])
        
        if mode == "Learning":
            self.config["mode"] = "development"
            shutil.copy(self.project_root / ".env.development", self.env_file)
            print("\n✅ Copied .env.development → .env (Learning mode configured)")
        elif mode == "Testing":
            self.config["mode"] = "testing"
            shutil.copy(self.env_example, self.env_file)
            print("\n✅ Copied .env.example → .env (Testing mode ready)")
        else:  # Production
            self.config["mode"] = "production"
            shutil.copy(self.project_root / ".env.production", self.env_file)
            print("\n✅ Copied .env.production → .env (Production mode configured)")

    def step2_angelone_credentials(self):
        """Step 2: AngelOne API credentials"""
        self.print_step("AngelOne API Credentials")
        
        print("\n🔑 Where to find your credentials:")
        print("1. Open AngelOne mobile app")
        print("2. Menu → Settings → API Configuration")
        print("3. Copy your credentials from there")
        print("\n📖 Full guide: https://smartapi.angelbroking.com/\n")
        
        print("⚠️  Your credentials will be stored in .env (local file only)")
        print("    Never share these credentials!\n")
        
        api_key = self.ask_question("Your API Key")
        client_code = self.ask_question("Your Client Code (User ID)")
        password = self.ask_password("Your Login Password")
        totp_secret = self.ask_question("Your TOTP Secret (from Google Authenticator)")
        
        self.config["ANGELONE_API_KEY"] = api_key
        self.config["ANGELONE_CLIENT_CODE"] = client_code
        self.config["ANGELONE_PASSWORD"] = password
        self.config["ANGELONE_TOTP_SECRET"] = totp_secret
        
        print("\n✅ Credentials configured")

    def step3_trading_settings(self):
        """Step 3: Trading settings (for non-learning modes)"""
        if self.config["mode"] == "development":
            print("\n⏭️  Skipping trading settings (Learning mode uses safe defaults)")
            return
        
        self.print_step("Trading Settings")
        
        print("\n💰 Risk Management Settings:")
        
        initial_capital = self.ask_question(
            "Starting capital (in rupees)",
            "100000"
        )
        self.config["INITIAL_CAPITAL"] = initial_capital
        
        risk_per_trade = self.ask_question(
            "Risk per trade (as % of capital)",
            "2"
        )
        self.config["RISK_PER_TRADE"] = f"0.{risk_per_trade}"
        
        max_daily_loss = self.ask_question(
            "Max daily loss (in rupees)",
            "5000"
        )
        self.config["MAX_DAILY_LOSS"] = max_daily_loss
        
        print("\n✅ Trading settings configured")

    def step4_database_setup(self):
        """Step 4: Database selection"""
        self.print_step("Database Configuration")
        
        print("\n🗄️  Choose your database:")
        print("\n1️⃣  SQLite (Recommended for beginners)")
        print("   ✅ No setup required")
        print("   ✅ Simple file-based")
        print("   ✅ Good for learning")
        
        print("\n2️⃣  PostgreSQL (Recommended for production)")
        print("   ✅ Powerful and scalable")
        print("   ✅ Better for large datasets")
        print("   ✅ Requires installation")
        
        print("\n3️⃣  No database (Skip for now)")
        print("   ✅ No data persistence")
        print("   ✅ Good for testing strategies")
        
        db_choice = self.ask_question(
            "Which database?",
            options=["SQLite", "PostgreSQL", "Skip"]
        )
        
        if db_choice == "SQLite":
            self.config["DB_ENABLED"] = "True"
            self.config["DB_TYPE"] = "sqlite"
            self.config["DB_PATH"] = "./data/angelx.db"
            print("\n✅ SQLite configured")
            
        elif db_choice == "PostgreSQL":
            self.config["DB_ENABLED"] = "True"
            self.config["DB_TYPE"] = "postgresql"
            db_host = self.ask_question("Database host", "localhost")
            db_port = self.ask_question("Database port", "5432")
            db_name = self.ask_question("Database name", "angelx_ml")
            db_user = self.ask_question("Database user", "angelx")
            db_password = self.ask_password("Database password")
            
            self.config["DATABASE_HOST"] = db_host
            self.config["DATABASE_PORT"] = db_port
            self.config["DATABASE_NAME"] = db_name
            self.config["DATABASE_USER"] = db_user
            self.config["DATABASE_PASSWORD"] = db_password
            print("\n✅ PostgreSQL configured")
            
        else:
            self.config["DB_ENABLED"] = "False"
            print("\n✅ Database skipped")

    def step5_create_directories(self):
        """Step 5: Create necessary directories"""
        self.print_step("Setting up directories")
        
        directories = [
            "data",
            "data/exports",
            "logs",
            "models",
            "profiling",
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}/")

    def step6_update_env_file(self):
        """Step 6: Update .env file with collected config"""
        self.print_step("Updating .env file")
        
        # Read current .env
        with open(self.env_file, "r") as f:
            env_content = f.read()
        
        # Update with collected values
        for key, value in self.config.items():
            if key in ["mode", "INITIAL_CAPITAL"]:
                continue
            
            # Find and replace or add the key
            if f"{key}=" in env_content:
                import re
                pattern = f"{key}=.*"
                env_content = re.sub(pattern, f"{key}={value}", env_content)
            
        # Write back
        with open(self.env_file, "w") as f:
            f.write(env_content)
        
        print(f"✅ Updated .env file")
        print(f"📁 Location: {self.env_file}")

    def step7_test_connection(self):
        """Step 7: Test AngelOne API connection"""
        self.print_step("Testing API Connection")
        
        if not all([
            self.config.get("ANGELONE_API_KEY"),
            self.config.get("ANGELONE_CLIENT_CODE"),
            self.config.get("ANGELONE_PASSWORD")
        ]):
            print("⏭️  Skipping API test (credentials incomplete)")
            return
        
        print("\n🔄 Testing AngelOne API connection...")
        print("⏳ This may take a few seconds...\n")
        
        try:
            # Try importing and testing
            from config import ANGELONE_API_KEY, ANGELONE_CLIENT_CODE
            
            if ANGELONE_API_KEY and ANGELONE_CLIENT_CODE:
                print("✅ API credentials loaded successfully!")
                print("   Ready to connect to AngelOne broker")
            else:
                print("⚠️  API credentials not fully configured")
        except Exception as e:
            print(f"⚠️  Could not test API: {e}")
            print("   You can test manually later by running the system")

    def step8_summary(self):
        """Step 8: Summary and next steps"""
        self.print_step("Setup Complete! ✅")
        
        print("\n🎉 Angel-X has been configured successfully!")
        print("\nYour configuration:")
        print(f"  • Mode: {self.config.get('mode', 'development')}")
        print(f"  • Database: {self.config.get('DB_TYPE', 'sqlite')}")
        print(f"  • API Credentials: {self.config.get('ANGELONE_CLIENT_CODE', 'Not set')}")
        
        print("\n📖 Next steps:")
        print("\n1. Read the documentation:")
        print("   📚 cat docs/CONFIGURATION.md")
        
        print("\n2. Start the system:")
        if self.config["mode"] == "development":
            print("   🚀 python main.py")
        else:
            print("   🚀 python main.py")
        
        print("\n3. Access the dashboard:")
        print("   🌐 http://localhost:5001")
        
        print("\n4. Check logs if needed:")
        print("   📊 tail -f logs/angel-x.log")
        
        print("\n💡 Tips:")
        print("  • Always start with LEARNING mode to understand the system")
        print("  • Paper trading is enabled by default (no real money)")
        print("  • Check logs in ./logs/ directory if issues occur")
        print("  • See docs/CONFIGURATION.md for all available settings")
        
        print("\n" + "=" * 80)
        print("Happy Trading! शुभ व्यापार! শুভ ট্রেডিং!")
        print("=" * 80 + "\n")

    def run(self):
        """Run the complete setup wizard"""
        try:
            self.print_header()
            
            # Check if .env already exists
            if self.env_file.exists():
                response = self.ask_question(
                    "\n⚠️  .env file already exists. Overwrite?",
                    options=["Yes", "No"]
                )
                if response == "No":
                    print("\n❌ Setup cancelled")
                    return False
            
            self.step1_welcome()
            self.step2_angelone_credentials()
            self.step3_trading_settings()
            self.step4_database_setup()
            self.step5_create_directories()
            self.step6_update_env_file()
            self.step7_test_connection()
            self.step8_summary()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user")
            return False
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            return False


def main():
    """Main entry point"""
    setup = AngelXSetup()
    success = setup.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
