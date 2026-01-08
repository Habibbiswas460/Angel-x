# Telegram Alert Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create Telegram Bot
1. Open Telegram app
2. Search for `@BotFather`
3. Send `/newbot` command
4. Enter bot name: `Angel-X Trading Bot`
5. Enter username: `angelx_yourname_bot` (must end with 'bot')
6. Copy the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID
1. Search for `@userinfobot` in Telegram
2. Send `/start` command
3. Copy your **Chat ID** (a number like: `123456789`)

### Step 3: Test the Bot
1. Search for your bot username in Telegram
2. Send `/start` to your bot
3. Bot should respond (if not, wait a minute)

### Step 4: Add to .env File
Open `.env` file and add these lines:

```bash
# Telegram Alerts Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ALERTS_ENABLED=true
```

Replace with your actual token and chat ID!

### Step 5: Test Alerts
```bash
PYTHONPATH=. .venv/bin/python scripts/test_alerts.py
```

You should receive 10 test notifications in Telegram! 📱

---

## Alert Types

Angel-X sends alerts for:

✅ **Entry Signals**
- When strategy finds a trading opportunity
- Includes strike, price, Greeks

📈 **Trade Executed**
- Confirmation when order is filled
- Shows quantity, price, total value

🎯 **Target Achieved**
- When profit target is hit
- Shows entry/exit price, profit amount

🛑 **Stop Loss Hit**
- When stop loss triggers
- Shows entry/exit price, loss amount

📊 **Position Updates**
- Periodic position summaries
- Shows open positions, PnL

⚠️ **Risk Alerts**
- Daily loss limit approaching
- Greeks threshold breaches
- Cooldown period activated

📈 **Daily Summary**
- End-of-day performance
- Win rate, total PnL, trade count

🔧 **System Events**
- Connection status
- Data feed health
- Strategy state changes

---

## Notification Settings

### Silent Notifications
Some alerts (position updates, system events) are sent silently to avoid constant pings.

### Customize in Code
Edit `src/utils/alert_system.py` to:
- Change alert formats
- Add/remove alert types
- Modify notification frequency

---

## Troubleshooting

**Bot not responding?**
- Make sure you sent `/start` to your bot
- Wait 1-2 minutes after creating bot
- Check bot token is correct

**Not receiving alerts?**
- Verify chat ID is correct (number only, no quotes)
- Check `.env` file has correct values
- Test with: `scripts/test_alerts.py`

**Too many alerts?**
- Set `TELEGRAM_ALERTS_ENABLED=false` in `.env`
- Or comment out unwanted alert types in strategy code

---

## Example .env Configuration

```bash
# === Telegram Configuration ===
TELEGRAM_BOT_TOKEN=6789012345:AAHGxYz-ABCdefghIJKLmnopQRSTuvwXYZ
TELEGRAM_CHAT_ID=987654321
TELEGRAM_ALERTS_ENABLED=true
```

---

## Security Notes

⚠️ **Keep your bot token secret!**
- Never commit `.env` to git
- Don't share bot token publicly
- Regenerate token if compromised (via @BotFather)

🔒 **Chat ID privacy:**
- Only you can send messages to your chat ID
- Bot can only send to authorized chat IDs

---

## Advanced: Group Alerts

To send alerts to a Telegram group:

1. Create a Telegram group
2. Add your bot to the group
3. Send a message to the group
4. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Find the group's chat ID (negative number like `-123456789`)
6. Use group chat ID in `.env`

---

## Sample Telegram Alert

```
🎯 ENTRY SIGNAL
26200 CE @ ₹125.50

📊 Details:
  • Strike: 26200
  • Type: CE
  • Bias: BULLISH
  • Entry Price: ₹125.50
  • Delta: 0.472
  • Gamma: 0.00181
  • IV: 16.0%

🕐 2026-01-06 14:35:22
```

---

## Next Steps

After Telegram is working:
1. Integrate alerts into strategy (Phase 1 ongoing)
2. Add WhatsApp alerts (future)
3. Email alerts for daily summaries (future)
4. SMS alerts for critical events (future)

✅ Enjoy real-time trading notifications!
