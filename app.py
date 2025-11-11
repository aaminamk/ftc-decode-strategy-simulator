# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from strategy import compute_strategy, default_field_layout, euclid

st.set_page_config(page_title="FTC DECODE Strategy Simulator", layout="wide")

st.title("🤖 FTC DECODE — Strategy Simulator")

# ---- left: parameters ----
with st.sidebar:
    st.header("Match & Robot Parameters")
    match_time = st.number_input("Match time (s)", min_value=30, max_value=300, value=150, step=10)
    auton_time = st.number_input("Autonomous time (s)", min_value=5, max_value=60, value=30, step=5)
    robot_speed = st.number_input("Robot speed (units/s)", min_value=10.0, max_value=1000.0, value=150.0, step=10.0)
    pickup_time = st.number_input("Pickup time (s) per artifact", min_value=0.5, max_value=20.0, value=3.0, step=0.5)
    points_per_artifact = st.number_input("Base points per artifact", min_value=1, max_value=50, value=5, step=1)
    decode_bonus = st.number_input("Decode zone bonus (points)", min_value=0, max_value=50, value=3, step=1)
    auton_multiplier = st.number_input("Autonomous points multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)

    st.markdown("---")
    st.header("Field / Artifacts")
    preset = default_field_layout()
    use_preset = st.checkbox("Use default field layout (recommended)", value=True)
    if use_preset:
        start = preset["start"]
        artifacts = preset["artifacts"]
        decode_zone = preset["decode_zone"]
    else:
        st.write("Manual artifact input (comma-separated pairs e.g. 200,80 ; 300,200)")
        start_x = st.number_input("Start X", value=50)
        start_y = st.number_input("Start Y", value=200)
        start = (start_x, start_y)
        art_input = st.text_area("Artifact positions", value="200,80;250,160;300,240")
        artifacts = []
        for p in art_input.split(";"):
            p = p.strip()
            if not p:
                continue
            try:
                x, y = map(float, p.split(","))
                artifacts.append((x, y))
            except:
                st.warning(f"Could not parse: {p}")
        dz_center_x = st.number_input("Decode center X", value=470)
        dz_center_y = st.number_input("Decode center Y", value=160)
        dz_radius = st.number_input("Decode radius", value=70)
        decode_zone = ((dz_center_x, dz_center_y), dz_radius)

    st.markdown("---")
    if st.button("Run strategy simulation"):
        run_sim = True
    else:
        run_sim = False

# ---- main area: run & visualize ----
if run_sim:
    params = {
        "robot_speed": robot_speed,
        "pickup_time": pickup_time,
        "match_time": match_time,
        "auton_time": auton_time,
        "points_per_artifact": points_per_artifact,
        "decode_zone": decode_zone,
        "decode_bonus": decode_bonus,
        "auton_multiplier": auton_multiplier
    }

    result = compute_strategy(start, artifacts, params)

    st.subheader("🔎 Strategy summary")
    st.metric("Expected score", f"{result['expected_score']:.1f} pts")
    st.write(f"Used time: {result['used_time']:.1f} s / {match_time} s")
    st.write(f"Remaining artifacts not reached: {result['remaining_artifacts']}")

    # visited table
    visited = result["visited"]
    if visited:
        tbl = []
        for i, v in enumerate(visited, 1):
            tbl.append({
                "Order": i,
                "X": v["pos"][0],
                "Y": v["pos"][1],
                "Travel time (s)": round(v["travel_time"], 2),
                "Pickup time (s)": v["pickup_time"],
                "Time at pickup (s)": round(v["time_at_pickup"], 2),
                "In auton": v["in_auton"],
                "Points gained": round(v["gained"], 2)
            })
        df = pd.DataFrame(tbl)
        st.table(df)

    # ---- Visualization: plot field, artifacts, path ----
    st.subheader("🗺 Field visualization")
    fig = go.Figure()
    # field bounds
    WIDTH, HEIGHT = 600, 400

    # artifacts
    xs = [p[0] for p in artifacts]
    ys = [p[1] for p in artifacts]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text",
                             marker=dict(size=12), text=[f"A{i+1}" for i in range(len(artifacts))],
                             textposition="top center", name="Artifacts"))

    # start point
    fig.add_trace(go.Scatter(x=[start[0]], y=[start[1]], mode="markers+text",
                             marker=dict(size=14, color="green"), text=["Start"],
                             textposition="bottom center", name="Start"))

    # decode zone circle
    dz_center, dz_radius = decode_zone
    theta = np.linspace(0, 2*np.pi, 80)
    circ_x = dz_center[0] + dz_radius * np.cos(theta)
    circ_y = dz_center[1] + dz_radius * np.sin(theta)
    fig.add_trace(go.Scatter(x=circ_x, y=circ_y, mode="lines", fill="toself",
                             opacity=0.15, name="Decode zone"))

    # path line
    path_x = []
    path_y = []
    cur = start
    for v in visited:
        path_x.append(cur[0]); path_y.append(cur[1])
        path_x.append(v["pos"][0]); path_y.append(v["pos"][1])
        cur = v["pos"]

    if path_x:
        fig.add_trace(go.Scatter(x=path_x, y=path_y, mode="lines+markers",
                                 line=dict(width=3), name="Planned path"))

    fig.update_layout(
        width=900, height=600,
        xaxis=dict(range=[0, WIDTH], title="Field X"),
        yaxis=dict(range=[0, HEIGHT], title="Field Y", autorange="reversed"),
        showlegend=True, title="Field map (units arbitrary)"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Notes and suggestions
    st.markdown("---")
    st.subheader("Coach tips (automatically generated)")
    tips = []
    if result["remaining_artifacts"] > 0:
        tips.append("- Consider increasing robot speed, or prioritizing artifacts inside the decode zone during auton.")
    if autonom_multiplier > 1.2 and auton_time > 10:
        tips.append("- Focus on quick pickups during autonomous to exploit the multiplier.")
    if decode_bonus > 0:
        tips.append("- Decode zone grants bonus: plan path to include those artifacts early if close.")
    if not tips:
        tips.append("- Strategy looks balanced for current parameters.")

    for t in tips:
        st.write(t)

else:
    st.info("Configure parameters in the sidebar and press **Run strategy simulation**.")
