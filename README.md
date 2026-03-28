# 🏆 Tournament Betting Market

A live odds betting platform for your friend group — built with FastAPI + WebSockets.

---

## Features
- User accounts with fake point balances (1,000 pts to start)
- Admin creates head-to-head matchups with starting odds
- Odds auto-adjust as bets come in (market model + vig)
- Admin can override odds at any time
- Live updates via WebSocket — odds move in real time for everyone
- Settle matchups and payouts are automatic
- Bet history per user
- Leaderboard

---

## Local Setup (VS Code)

### 1. Create & activate a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server
```bash
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

### 4. First user = Admin
The **first account registered** becomes the admin. Register yourself first, then share the URL with friends.

---

## Deploy to Railway (free public URL)

1. Push this folder to a GitHub repo
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select your repo — Railway auto-detects Python and starts the app
4. Add an environment variable: `SECRET_KEY` = any long random string
5. Your app gets a public URL like `https://your-app.up.railway.app`

That's it — share the URL with friends!

---

## Admin Guide

Log in as admin → click **⚙️ Admin** tab.

- **Create Matchup**: set player names, sport, and starting odds
- **Set Odds**: manually override odds at any time (pushes live to all users)
- **Settle**: click the winner → payouts credited automatically

## How Odds Work

Odds start at whatever the admin sets. When bets come in, the engine:
1. Calculates proportion of money on each side
2. Converts to decimal odds with a 5% house vig
3. Broadcasts the new odds live to all connected users

Odds are clamped between **1.05x** (heavy favorite) and **20.0x** (massive underdog).
