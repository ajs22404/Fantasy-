from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from fantasy_gm.data import load_live, load_snapshot, live_credentials_available
from fantasy_gm.engine import (
    add_drop_moves,
    daily_note,
    explain_start,
    lineup_changes,
    optimize_lineup,
    player_score,
    trade_ideas,
)

st.set_page_config(page_title="Baja Blast Fantasy GM", page_icon="🌊", layout="wide")

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; max-width: 1450px;}
[data-testid="stMetricValue"] {font-size: 1.45rem;}
.gm-card {border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:14px; margin-bottom:10px;}
.small-muted {opacity:.72; font-size:.88rem;}
.good {color:#22c55e; font-weight:700;}
.warn {color:#f59e0b; font-weight:700;}
.bad {color:#ef4444; font-weight:700;}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=180)
def get_data(use_live: bool):
    if use_live:
        return load_live()
    data = load_snapshot()
    data["source"] = "saved ESPN snapshot from this project"
    return data


st.title("🌊 Baja Blast Fantasy GM")
st.caption("Real-data MVP: full roster, start/sit logic, add/drop scan, trade scan, and explainable recommendations.")

with st.sidebar:
    st.header("Data")
    has_creds = live_credentials_available()
    use_live = st.toggle("Use live ESPN league", value=has_creds, disabled=not has_creds)
    if has_creds:
        st.success("Private ESPN credentials found locally.")
    else:
        st.info("Running in snapshot mode. Add ESPN_S2 + ESPN_SWID to .env to enable live refresh.")
    if st.button("Refresh now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption("Your ESPN cookies stay in your local .env file. Never commit .env to GitHub.")

try:
    data = get_data(use_live)
except Exception as exc:
    st.error(f"Live ESPN refresh failed: {exc}")
    st.info("Falling back to the saved snapshot so the app still works.")
    data = get_data(False)
    use_live = False

league = data["league"]
roster = data["roster"]
free_agents = data.get("free_agents", [])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Team", league.get("team_name", "Baja Blast"))
c2.metric("NFL/Fantasy Week", league.get("week", "—"))
c3.metric("Waiver Priority", league.get("waiver_rank", "—"))
c4.metric("Data Source", "LIVE ESPN" if use_live else "SNAPSHOT")

st.subheader("Today's GM Note")
notes = daily_note(data)
cols = st.columns(len(notes)) if len(notes) <= 4 else st.columns(4)
for i, note in enumerate(notes):
    with cols[i % len(cols)]:
        st.markdown(f'<div class="gm-card">{note}</div>', unsafe_allow_html=True)

starters, bench = optimize_lineup(roster)
changes = lineup_changes(roster)

left, right = st.columns([1.35, 0.65], gap="large")

with left:
    st.subheader("Full Team")
    starter_names = {p["name"] for p in starters}
    rows = []
    for p in starters + bench:
        advice = "START" if p["name"] in starter_names else "BENCH"
        if str(p.get("injury_status", "ACTIVE")).upper() in {"OUT", "IR", "DOUBTFUL"}:
            advice = "INJURY"
        rows.append({
            "Slot": p.get("recommended_slot", "BE") if advice == "START" else "BENCH",
            "Player": p["name"],
            "Pos": p["position"],
            "NFL": p.get("team", ""),
            "Proj": round(float(p.get("projection", 0) or 0), 1),
            "GM": player_score(p),
            "Status": p.get("injury_status", "ACTIVE"),
            "Advice": advice,
        })
    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Proj": st.column_config.NumberColumn(format="%.1f"),
            "GM": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
        },
    )
    st.caption("GM score is transparent MVP logic, not a claim of perfect prediction. ESPN weekly projection is the largest input.")

    st.subheader("Why this start/sit?")
    if changes:
        labels = [f"{x['start']['name']} over {x['bench']['name']}" for x in changes]
        picked = st.selectbox("Decision", labels)
        ch = changes[labels.index(picked)]
        exp = explain_start(ch["start"], ch["bench"])
        st.markdown(f"### Start **{exp['winner']}** over **{exp['loser']}**")
        st.progress(exp["confidence"] / 100, text=f"Confidence: {exp['confidence']}%")
        for factor in exp["factors"]:
            st.write("•", factor)
        st.caption("Sources used in this MVP: " + " · ".join(exp["sources"]))
    else:
        # Still allow manual comparison of any two skill players.
        skill = [p for p in roster if p["position"] in {"QB", "RB", "WR", "TE"}]
        names = [p["name"] for p in skill]
        a, b = st.columns(2)
        with a:
            first = st.selectbox("Player A", names, index=0)
        with b:
            second = st.selectbox("Player B", names, index=min(1, len(names)-1))
        if first != second:
            pa = next(p for p in skill if p["name"] == first)
            pb = next(p for p in skill if p["name"] == second)
            winner, loser = (pa, pb) if player_score(pa) >= player_score(pb) else (pb, pa)
            exp = explain_start(winner, loser)
            st.markdown(f"### Model lean: **{winner['name']}**")
            st.progress(exp["confidence"] / 100, text=f"Confidence: {exp['confidence']}%")
            for factor in exp["factors"]:
                st.write("•", factor)

with right:
    st.subheader("Add / Drop")
    moves = add_drop_moves(roster, free_agents, 8)
    if moves:
        for m in moves:
            with st.container(border=True):
                st.markdown(f"**ADD {m['add']['name']}** → drop **{m['drop']['name']}**")
                st.write(m["why"])
                st.caption(f"GM-score edge: {m['edge']:+.1f} · projection edge: {m['projection_edge']:+.1f}")
    else:
        st.info("No add/drop currently clears the MVP upgrade threshold. In snapshot mode, waiver projections may be missing; live ESPN mode fixes that.")

    st.subheader("Trade Board")
    opponent_rosters = data.get("opponent_rosters", {})
    ideas = trade_ideas(roster, opponent_rosters)
    if ideas:
        for idea in ideas:
            with st.expander(idea["opponent"]):
                if idea.get("give"):
                    st.write(f"**Explore:** {idea['give']['name']} → {idea['get']['name']}")
                    st.write(idea["reason"])
                    st.caption(f"Model value gap (receive - give): {idea['value_gap']:+.1f}")
                else:
                    st.write(idea["status"])
                    st.caption(idea["reason"])
    else:
        for opp in data.get("opponents", []):
            with st.expander(opp):
                st.write("Live ESPN mode will read this opponent's roster and generate a roster-based trade fit.")

st.divider()
st.subheader("How real is this version?")
st.write(
    "The interface and recommendation engine are working now. In **live ESPN mode**, roster changes, opponent rosters, "
    "free agents/waivers, ESPN projections, ownership percentages and ESPN injury statuses refresh from your private league. "
    "The next data layer will add independent usage/news sources (targets, routes, snap share, practice reports and market data) "
    "so the written explanation is not dependent on ESPN alone."
)
st.caption(f"Current source: {data.get('source', 'unknown')}.")
