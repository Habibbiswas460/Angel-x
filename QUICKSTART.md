# ANGEL-X QUICKSTART GUIDE
# দ্রুত শুরু করার গাইড

## ⚡ 5 মিনিটে শুরু করুন | Get started in 5 minutes

### পদ্ধতি ১: ইন্টারঅ্যাক্টিভ সেটআপ (সবচেয়ে সহজ) | Interactive Setup (Easiest)

```bash
# একটি কমান্ড চালান | Just run:
python setup.py

# এরপর প্রশ্নের উত্তর দিন | Answer the questions:
# ✅ Choose your mode (Learning/Testing/Production)
# ✅ Enter AngelOne credentials
# ✅ Select database type
# ✅ Done! System is ready
```

### পদ্ধতি २: ম্যানুয়াল সেটআপ | Manual Setup

```bash
# Step 1: কপি করুন | Copy template
cp .env.example .env

# Step 2: এডিট করুন | Edit configuration
nano .env

# Step 3: আপনার credentials যোগ করুন | Add your credentials:
# ANGELONE_API_KEY=YOUR_KEY
# ANGELONE_CLIENT_CODE=YOUR_CODE
# ANGELONE_PASSWORD=YOUR_PASSWORD
# ANGELONE_TOTP_SECRET=YOUR_TOTP

# Step 4: সংরক্ষণ করুন | Save and exit (Ctrl+X in nano, then Y)
```

---

## ✅ কনফিগারেশন যাচাই করুন | Validate Configuration

```bash
# সব সেটিংস চেক করুন | Check all settings
python validate_config.py

# এটি যাচাই করবে:
# ✅ .env ফাইল আছে কি
# ✅ AngelOne credentials সম্পূর্ণ কি
# ✅ পোর্ট available আছে কি
# ✅ ডাটাবেস কানেক্ট হয় কি
# ✅ সব প্যাকেজ installed আছে কি
```

---

## 🚀 সিস্টেম চালান | Start the System

### Learning Mode (শিক্ষার জন্য - নিরাপদ)
```bash
# সবচেয়ে নিরাপদ | Safest option
cp .env.development .env
python main.py

# ব্রাউজার এ যান | Open browser:
# http://localhost:5001
```

### Testing Mode (পরীক্ষার জন্য - কাস্টমাইজেবল)
```bash
# আপনার সেটিংস দিয়ে | With your settings
python setup.py
python main.py
```

### Production Mode (লাইভ ট্রেডিং - সাবধানি!)
```bash
# ⚠️ শুধুমাত্র অভিজ্ঞরা | Experts only
cp .env.production .env
nano .env  # যোগ করুন: আপনার credentials
python main.py
```

---

## 📊 ড্যাশবোর্ড অ্যাক্সেস করুন | Access Dashboard

```
http://localhost:5001
```

ড্যাশবোর্ডে দেখবেন:
- Real-time market data
- Trading performance
- Account statistics
- System health
- Live charts and analytics

---

## 📚 ডেটাবেস সেটআপ (অপশনাল) | Database Setup (Optional)

### SQLite (Recommended for beginners)
```bash
# কোন সেটআপ লাগবে না | No setup needed
# স্বয়ংক্রিয়ভাবে তৈরি হবে | Auto-created
python main.py
# ডেটা সংরক্ষিত হবে: ./data/angelx.db
```

### PostgreSQL (Recommended for production)
```bash
# ইনস্টল করুন | Install PostgreSQL
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# Python package
pip install psycopg2-binary

# সেটআপ স্ক্রিপ্ট চালান | Run setup
python setup.py
# Select "PostgreSQL" option
```

---

## 🔍 সমস্যা সমাধান | Troubleshooting

### "সংযোগ ব্যর্থ" | "Connection failed"
```bash
# চেক করুন: AngelOne credentials সঠিক কি
grep ANGELONE .env

# চেক করুন: ইন্টারনেট আছে কি
ping 8.8.8.8

# চেক করুন: AngelOne সার্ভার চলছে কি
# Browser: https://smartapi.angelbroking.com/
```

### "পোর্ট ইতিমধ্যে ব্যবহৃত" | "Port already in use"
```bash
# কোনটি ব্যবহার করছে দেখুন
lsof -i :5001

# বা অন্য পোর্ট ব্যবহার করুন
DASHBOARD_PORT=5002 python main.py
```

### "ডাটাবেস এরর" | "Database error"
```bash
# SQLite এ সুইচ করুন | Switch to SQLite
DB_TYPE=sqlite python main.py

# অথবা ডাটাবেস বন্ধ করুন | Or disable database
DB_ENABLED=False python main.py
```

---

## 📖 পূর্ণ ডকুমেন্টেশন | Full Documentation

- **সম্পূর্ণ কনফিগারেশন গাইড**: `docs/CONFIGURATION.md`
- **API ডকুমেন্টেশন**: `docs/API.md`
- **ট্রেডিং গাইড**: `docs/TRADING.md`
- **ইনস্টলেশন**: `INSTALLATION.md`

---

## 💡 টিপস | Tips

✅ **শিক্ষানবিসদের জন্য:**
- সবসময় Learning mode দিয়ে শুরু করুন
- Paper trading enabled রাখুন
- Dashboard ব্যবহার করে সব বুঝুন
- একবার comfortable হলে Testing mode ব্যবহার করুন

✅ **ট্রেডারদের জন্য:**
- Risk management সেটিংস যত্নসহকারে করুন
- Daily loss limit সেট করুন
- Position size limit করুন
- প্রথমে কম capital দিয়ে শুরু করুন

✅ **সবার জন্য:**
- লগ ফাইল নিয়মিত চেক করুন: `./logs/`
- কনফিগারেশন validate করুন: `python validate_config.py`
- ডেটাবেস ব্যাকআপ নিন: `./data/`

---

## 🚨 গুরুত্বপূর্ণ নিরাপত্তা | Security Important

⚠️ **কখনো করবেন না | Never do:**
- ❌ .env ফাইল GitHub এ আপলোড করবেন না
- ❌ API key কাউকে দেবেন না
- ❌ Password শেয়ার করবেন না
- ❌ Production credentials development মেশিনে রাখবেন না

✅ **সবসময় করুন | Always do:**
- ✅ .env ফাইল .gitignore এ আছে কি চেক করুন
- ✅ Strong password ব্যবহার করুন
- ✅ নিয়মিত credentials rotate করুন
- ✅ লগ ফাইল পরিষ্কার রাখুন

---

## 📞 সাহায্য | Help

প্রশ্ন থাকলে:
1. `docs/CONFIGURATION.md` পড়ুন
2. `python validate_config.py` চালান
3. লগ ফাইল দেখুন: `tail -f logs/angel-x.log`
4. GitHub issues: https://github.com/Angel-x/issues

---

## এখন শুরু করুন! | Start Now!

```bash
python setup.py
```

Happy Trading! শুভ ট্রেডিং! 🚀
