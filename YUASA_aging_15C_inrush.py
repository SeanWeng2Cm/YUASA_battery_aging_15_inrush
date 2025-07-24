import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Title and model
battery_model = "YUASA NPW45-12"
st.title(f"Battery Resistance and Inrush Estimation — {battery_model}")

# Internal resistance data at 25°C
time_years = np.array([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5])
R_25 = np.array([1.0, 1.05, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.75, 4.5])  # Ohms

# Arrhenius parameters
Ea = 0.5 * 1.60218e-19 * 6.022e23  # J/mol
Rg = 8.314  # J/mol·K
T_ref = 298  # 25°C in K
T_actual_C = st.sidebar.slider("Temperature (°C)", -10, 40, 15)
T_actual_K = T_actual_C + 273.15

# Correction factor and adjusted resistance
factor = np.exp((Ea / Rg) * (1 / T_actual_K - 1 / T_ref))
R_T = R_25 * factor

# Plot resistance curves
fig = go.Figure()
fig.add_trace(go.Scatter(x=time_years, y=R_25, mode='lines+markers', name='25°C', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=time_years, y=R_T, mode='lines+markers', name=f'{T_actual_C}°C', line=dict(color='red')))

fig.update_layout(
    title='Internal Resistance vs. Time',
    xaxis_title='Time (Years)',
    yaxis_title='Internal Resistance (Ω)',
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

# Inrush Estimation Section
st.header("Inrush Current & Voltage Estimation")

V_OC = st.sidebar.number_input("Battery Open-Circuit Voltage (V)", value=12.0)
R_load = st.sidebar.number_input("Load Resistance (Ω)", value=1.0)
selected_year = st.sidebar.slider("Select Aging Year", 0.0, 5.0, step=0.1)

# Interpolate resistance
R_internal = np.interp(selected_year, time_years, R_T)
I_inrush = V_OC / (R_internal + R_load)
V_inrush = I_inrush * R_load

st.markdown(f"""
- 📆 **Selected Aging Year**: {selected_year:.1f} years  
- 🌡️ **Temperature**: {T_actual_C}°C  
- 🔌 **Internal Resistance**: {R_internal:.4f} Ω  
- ⚡ **Inrush Current**: {I_inrush:.2f} A  
- 🔋 **Inrush Voltage (across load)**: {V_inrush:.2f} V  
""")
