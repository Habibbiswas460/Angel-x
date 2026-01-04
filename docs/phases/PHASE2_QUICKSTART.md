# 🚀 PHASE 2 QUICKSTART - Real AngelOne Trading

**Goal:** Move from simulated trading to real Angel One broker connectivity  
**Time:** 15 minutes  
**Risk:** None (demo account testing first)

---

## ✅ PREREQUISITES

- [ ] Angel One account (live or demo)
- [ ] Python 3.10+ installed
- [ ] VS Code with Python extension

---

## 🔧 STEP 1: GET CREDENTIALS

### From Angel One Website

1. Log in to Angel One trading dashboard
2. Go to **Settings → Mobile App PIN Setup**
3. Note down:
   - **API Key** (SmartAPI app credentials)
   - **Client Code** (your trading account number)
   - **Password** (your trading account password)
4. Go to **2FA Settings → TOTP Secret**
   - Get the secret from Google Authenticator
   - OR generate new secret if needed

### Example

```bash
API_KEY=6VKVgLJy
CLIENT_CODE=H51550060
PASSWORD=8855
TOTP_SECRET=5LDV7BZGWOAL4GBALQ6HI4KZLE
```

---

## 🔐 STEP 2: CONFIGURE ENVIRONMENT

### Edit `.env` File

```bash
# Create or edit .env in project root
nano .env
```

### Add Phase 2 Variables

```bash
# Real Angel One credentials
ANGELONE_API_KEY=your_api_key_here
ANGELONE_CLIENT_CODE=your_client_code_here
ANGELONE_PASSWORD=your_password_here
ANGELONE_TOTP_SECRET=your_totp_secret_here

# Mode (START WITH PAPER FOR TESTING)
PAPER_TRADING=true              # Set to false for real trading

# Data source
DATA_SOURCE=broker

# Logging
LOG_LEVEL=DEBUG
```

### Save File

```bash
# Ctrl+X, Y, Enter to save in nano
```

---

## 📦 STEP 3: INSTALL PHASE 2 DEPENDENCIES

```bash
# Install SmartAPI SDK and TOTP library
cd /home/lora/git_clone_projects/OA
pip install -r requirements.txt
```

**Verify Installation:**

```bash
python -c "import smartapi; import pyotp; print('✓ Installed')"
```

---

## 🧪 STEP 4: TEST IN PAPER TRADING MODE

**Important:** Always test in paper mode first!

### Run Validation Script

```bash
# Test with real credentials but simulated orders
cd /home/lora/git_clone_projects/OA
PYTHONPATH=. python scripts/phase2_validation.py
```

**Expected Output:**

```
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 2 VALIDATION - SIMULATED MODE                            ║
╚══════════════════════════════════════════════════════════════════╝

✓ AUTHENTICATION: SUCCESS
✓ MARKET DATA: LTP fetched
✓ ORDER PLACEMENT: Simulated
✓ All tests passed in paper mode
```

---

## 🔄 STEP 5: SWITCH TO LIVE TESTING

### Update `.env`

```bash
# Before:
PAPER_TRADING=true

# After:
PAPER_TRADING=false
```

### Run Validation Again

```bash
PYTHONPATH=. python scripts/phase2_validation.py
```

**Expected Output:**

```
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 2 VALIDATION - REAL BROKER CONNECTED ✅                  ║
╚══════════════════════════════════════════════════════════════════╝

✓ AUTHENTICATION: SUCCESS (Real credentials used)
✓ MARKET DATA: Real LTP from Angel One
✓ ORDER PLACEMENT: Orders placed on broker
✓ All tests passed - REAL TRADING ACTIVE
```

---

## 📊 STEP 6: RUN STRATEGY

### Start Strategy in Demo Mode

```bash
# This uses real market data + real orders (demo account)
PYTHONPATH=. python main.py --demo --small-position
```

### Monitor Logs

```bash
# In another terminal
tail -f logs/trading.log
```

### Check Orders

1. Log in to Angel One website
2. Go to **Orders** section
3. See orders placed by your Python script

---

## 🛑 STEP 7: SAFETY CHECKS

### Before Going Live

- [ ] Test with 1 lot only (smallest position)
- [ ] Monitor for 5-10 minutes
- [ ] Check order fills on broker website
- [ ] Verify P&L calculations
- [ ] Test cancel/exit functionality
- [ ] Check logs for errors

### Kill Switch (Stop Trading)

```bash
# If something goes wrong, run:
PYTHONPATH=. python scripts/kill_all_orders.py

# Or manually cancel on Angel One website
```

---

## 🐛 COMMON ISSUES

### Issue: "SmartAPI SDK not installed"

**Solution:**
```bash
pip install smartapi>=1.3.0
```

### Issue: "TOTP invalid"

**Solution:**
1. Check that Google Authenticator app has correct time
2. Get fresh TOTP secret from Angel One website
3. Try PAPER_TRADING=true first

### Issue: "Credentials not found"

**Solution:**
```bash
# Check .env file exists and has variables
cat .env | grep ANGELONE

# Ensure it's in project root:
ls -la .env
```

### Issue: "Connection timeout"

**Solution:**
1. Check internet connection
2. Check Angel One server status
3. Try again in 30 seconds (auto-retry works)

---

## 📈 STEP 8: SCALE UP

### Once Confident with Demo

1. Switch to **live account credentials** in `.env`
2. Update `max_position_size=100000` (1 lakh rupees)
3. Start with **1-2 contracts** only
4. Monitor carefully
5. Gradually increase position size

### Live Account Safety

```bash
# In .env, add:
MAX_POSITION_SIZE=100000          # 1 lakh rupees max
MAX_ORDERS_PER_HOUR=10            # Rate limit
STOP_LOSS_PERCENT=5               # Auto-close if down 5%
```

---

## ✅ VALIDATION CHECKLIST

- [ ] .env file created with credentials
- [ ] Dependencies installed (smartapi, pyotp)
- [ ] Phase 2 validation passes in PAPER_TRADING=true
- [ ] Phase 2 validation passes in PAPER_TRADING=false
- [ ] Real orders placed and cancelled successfully
- [ ] Logs show real broker connectivity
- [ ] Strategy runs with real market data
- [ ] Position sizing correct
- [ ] Kill switch tested
- [ ] Ready for live trading

---

## 📞 NEXT STEPS

### If Validation Passes
1. Run full strategy: `python main.py --demo`
2. Monitor for 1 hour
3. Check P&L calculations
4. Verify order fills

### If Validation Fails
1. Check error logs: `tail logs/trading.log`
2. Verify credentials in .env
3. Test manually: `python scripts/test_credentials.py`
4. Contact Angel One support if API issue

---

## 🎯 SUCCESS CRITERIA

✅ Phase 2 is complete when:

- Real credentials accepted by Angel One API
- SmartAPI SDK successfully authenticates
- Market data fetched from live broker
- Orders placed and filled on broker
- All logs show real broker connectivity
- Strategy runs with real market data
- P&L tracking works correctly

---

**Ready to trade! Start with Step 1 above.**

*Questions? Check [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) for detailed documentation.*
