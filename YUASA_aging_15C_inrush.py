import streamlit as st
import numpy as np
import plotly.graph_objects as go

# === Title ===
battery_model = "YUASA NPW45-12"
nominal_capacity_ah = 7.5
st.title(f"Battery Capacity Retention Over Time — {battery_model}")

# === Sidebar Inputs ===
initial_capacity = st.sidebar.slider("Initial Capacity (%)", 50, 100, 95)
input_months = st.sidebar.number_input("Storage Time (Months)", 0, 120, 12)
input_days = st.sidebar.number_input("Additional Days", 0, 31, 0)
input_hours = st.sidebar.number_input("Additional Hours", 0, 23, 0)
min_temp = st.sidebar.slider("Min Temperature (°C)", -20, 25, -15)
max_temp = st.sidebar.slider("Max Temperature (°C)", 25, 60, 45)
temp_step = st.sidebar.slider("Temperature Step (°C)", 1, 10, 5)

# === Constants for model ===
base_temp = 25
base_rate = 0.0342
Q0 = initial_capacity
total_months = input_months + (input_days / 30.42) + (input_hours / 24 / 30.42)
x_months = np.arange(0, total_months + 0.1, 0.1)
x_days = x_months * 30.42
x_hours = x_days * 24
temps = np.arange(min_temp, max_temp + 1, temp_step)
temps_list = [int(t) for t in temps]

# === Color Map ===
color_palette = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
    "#FFA15A", "#19D3F3", "#FF6692", "#B6E880"
]
color_map = {t: color_palette[i % len(color_palette)] for i, t in enumerate(temps_list)}

# === Create Capacity Plot ===
fig = go.Figure()
curves = {}
for T in temps_list:
    k_T = base_rate * 2 ** ((T - base_temp) / 10)
    capacity = Q0 * ((1 - k_T) ** x_months)
    final_capacity = capacity[-1]
    curves[T] = capacity

    fig.add_trace(go.Scatter(
        x=x_months, y=capacity, mode='lines',
        name=f"{T}°C — Final: {final_capacity:.1f}%",
        line=dict(color=color_map[T]),
        hovertemplate='Month: %{x:.2f}<br>Capacity: %{y:.2f}%<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=[x_months[-1]], y=[final_capacity],
        mode='markers', marker=dict(size=8, color=color_map[T]),
        showlegend=False,
        hovertemplate=(f"<b>Temp:</b> {T}°C<br>"
                       f"<b>Month:</b> {x_months[-1]:.2f}<br>"
                       f"<b>Hour:</b> {x_hours[-1]:.0f}<br>"
                       f"<b>Cap:</b> {final_capacity:.2f}%<extra></extra>")
    ))

# === Highlight Area Between Temperatures ===
def get_closest_index(array, value):
    return int((np.abs(array - value)).argmin())

highlight_start_idx = get_closest_index(temps, -5)
highlight_end_idx = get_closest_index(temps, 35)
highlight_start = st.sidebar.selectbox("Highlight Start Temp (°C)", temps_list, index=highlight_start_idx)
highlight_end = st.sidebar.selectbox("Highlight End Temp (°C)", temps_list, index=highlight_end_idx)

if highlight_start != highlight_end:
    lower_T, upper_T = sorted((highlight_start, highlight_end))
    y_lower = curves[lower_T]
    y_upper = curves[upper_T]
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_months, x_months[::-1]]),
        y=np.concatenate([y_upper, y_lower[::-1]]),
        fill='toself', fillcolor='rgba(255, 215, 0, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo='skip', showlegend=False
    ))

fig.update_layout(
    title=f"{battery_model} — Capacity Retention vs. Time & Temperature",
    xaxis_title="Storage Time (Months)",
    yaxis_title="Remaining Capacity (%)",
    hovermode='x unified',
    height=600
)
st.plotly_chart(fig, use_container_width=True)

# === Self-Discharge Estimation ===
st.header("Estimated Self-Discharge Current")
est_temp = st.sidebar.number_input("Temperature for Self-Discharge Estimation (°C)", -20, 60, 25)
k_est = base_rate * 2 ** ((est_temp - base_temp) / 10)
current_a = k_est * nominal_capacity_ah
current_ma = current_a * 1000
rate_percent = k_est * 100

st.markdown(f"""
- 🌡️ **Input temperature**: **{est_temp}°C**  
- 📉 **Self-discharge rate**: **{rate_percent:.2f}% per month**  
- 🔋 **Nominal capacity**: {nominal_capacity_ah} Ah  
- 🔌 **Self-discharge current**: **{current_ma:.0f} mA**
""")

# === Inrush Current and Voltage Drop Estimation ===
st.header("Inrush Current and Voltage Drop Estimation")
nominal_voltage = st.sidebar.number_input("Nominal Battery Voltage (V)", 12, 600, 240)
max_power_kw = st.sidebar.number_input("Maximum Load Power (kW)", 1.0, 50.0, 12.0)
max_power_w = max_power_kw * 1000
inrush_current = max_power_w / nominal_voltage

st.markdown(f"""
- ⚡ **Maximum load power**: {max_power_kw:.1f} kW  
- 🔌 **Nominal voltage**: {nominal_voltage} V  
- 🧮 **Estimated inrush current**: {inrush_current:.1f} A
""")

# === Internal Resistance Over Aging (converted to mΩ) ===
time = np.arange(0, 11)  # Years
R_25_mohm = np.array([1.0, 1.05, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.75, 4.5]) * 13.83  # mΩ

Ea = 5000  # J/mol
R_const = 8.314  # J/mol-K
T_ref = 25
T_15 = 15
R_15_mohm = R_25_mohm * np.exp((Ea / R_const) * ((1 / (T_15 + 273.15)) - (1 / (T_ref + 273.15))))

# Clamp negative voltages
voltage_drop_15 = (R_15_mohm / 1000) * inrush_current
terminal_voltage_15 = nominal_voltage - voltage_drop_15
terminal_voltage_15 = np.clip(terminal_voltage_15, 0, nominal_voltage)

# === Plot Terminal Voltage ===
fig_v = go.Figure()
fig_v.add_trace(go.Scatter(
    x=time,
    y=terminal_voltage_15,
    mode='lines+markers',
    name="Terminal Voltage (15°C Aging)",
    line=dict(color='red'),
    hovertemplate='Year: %{x}<br>Voltage: %{y:.2f} V<extra></extra>'
))
fig_v.update_layout(
    title="Terminal Voltage vs. Aging Time (15°C)",
    xaxis_title="Time (Years)",
    yaxis_title="Terminal Voltage (V)",
    height=400
)
st.plotly_chart(fig_v, use_container_width=True)

# === Optional: Show Resistance Trend ===
fig_r = go.Figure()
fig_r.add_trace(go.Scatter(
    x=time,
    y=R_15_mohm,
    mode='lines+markers',
    name="Internal Resistance @15°C",
    line=dict(color='blue'),
    hovertemplate='Year: %{x}<br>Resistance: %{y:.1f} mΩ<extra></extra>'
))
fig_r.update_layout(
    title="Internal Resistance vs. Aging Time (15°C)",
    xaxis_title="Time (Years)",
    yaxis_title="Internal Resistance (mΩ)",
    height=400
)
st.plotly_chart(fig_r, use_container_width=True)
