# ftc-decode-strategy-simulator
# FTC DECODE — Strategy Simulator

A simple strategy simulator for the FIRST Tech Challenge DECODE season.
This app helps teams estimate how many artifacts a robot can collect
and suggests a greedy path with scoring (autonomous multiplier and decode zone bonus included).

## Features
- Input match and robot parameters (speed, pickup time, autonomous time)
- Visual field with artifacts and decode zone
- Greedy path planning (nearest-first) with expected points calculation
- Interactive visualization (Plotly) and coach tips

## How to run locally
1. Clone the repo
2. Create and activate Python env
```bash
pip install -r requirements.txt
streamlit run app.py
