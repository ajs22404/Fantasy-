# Baja Blast Fantasy GM

A personal ESPN fantasy-football dashboard for the **Baja Blast** team.

## What works in this MVP

- Full roster + bench on one screen
- Recommended weekly lineup
- Explainable start/sit comparisons
- Add/drop scan against current ESPN free agents/waivers
- Injury-status awareness
- Daily GM summary
- Opponent-by-opponent trade scan when live league data is connected
- 3-minute caching + manual refresh

The recommendation math is deliberately transparent. It is an MVP, not a finished prediction model. ESPN's weekly projection is currently the largest signal; ownership, recent output, season projection and injury status are secondary signals.

## 1. Run it

Use Python 3.10+.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

It opens at `http://localhost:8501`.

## 2. Connect the private ESPN league

Your league is private, so ESPN requires two browser cookie values: `espn_s2` and `SWID` for authenticated league reads. The `espn-api` project supports private leagues using these values.

**Do not send these cookie values to anyone and do not commit them to GitHub.** Treat them like account credentials.

1. Copy `.env.example` to `.env`.
2. Sign into ESPN in your own browser.
3. Open browser developer tools → Application/Storage → Cookies → ESPN.
4. Copy the values for `espn_s2` and `SWID` into your local `.env` file.
5. Restart Streamlit.

Example:

```env
ESPN_LEAGUE_ID=438460368
ESPN_SEASON=2026
ESPN_TEAM_ID=3
ESPN_TEAM_NAME=Baja Blast
ESPN_S2=your_private_cookie_here
ESPN_SWID={your-private-swid-here}
```

`.env` is already included in `.gitignore`.

## 3. Data behavior

Without private ESPN cookies, the app runs against the saved roster snapshot supplied during development. With the cookies configured locally, it uses the live ESPN league for:

- Baja Blast roster
- all seven opponent rosters
- current free agents and waiver players
- weekly player projections
- roster/started percentages when available
- injury status
- waiver priority

## 4. Next upgrades

The next stage should add independent sources for:

- targets and target share
- carries / touches
- snap share
- route participation
- red-zone usage
- official practice and injury reports
- game environment / betting market data
- rest-of-season value

Those signals will feed separate **Start**, **Waiver**, **Drop**, and **Trade** scores instead of one general MVP score.

## Security

Never put `ESPN_S2`, `ESPN_SWID`, passwords, or browser cookies in source code, screenshots, commits, or chat messages.
