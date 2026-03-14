import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 초기화 ---
st.set_page_config(page_title="THE VORTEX: Click Fix", layout="wide")
st.title("🌀 THE VORTEX: Designer Mode")

if 'vortices' not in st.session_state:
    st.session_state.vortices = []
if 'temp_pos' not in st.session_state:
    st.session_state.temp_pos = None

P_START = np.array([-4.0, 0.0])
Q_TARGET = np.array([4.0, 0.0])

# --- 2. 투명 클릭 센서 그리드 생성 ---
# -5부터 5까지 0.2 간격으로 점을 생성 (촘촘할수록 클릭이 정확해짐)
grid_range = np.arange(-5, 5.2, 0.2)
grid_x, grid_y = np.meshgrid(grid_range, grid_range)
grid_x = grid_x.flatten()
grid_y = grid_y.flatten()

# --- 3. 물리 연산 ---
def get_path(vortices):
    path = [P_START]
    curr = P_START.copy()
    dt = 0.05
    for _ in range(500):
        u, v = 0.0, 0.0
        for vx, vy, vg in vortices:
            dx, dy = curr[0] - vx, curr[1] - vy
            r2 = dx**2 + dy**2 + 0.01
            u += -(vg / (2 * np.pi)) * (dy / r2)
            v += (vg / (2 * np.pi)) * (dx / r2)
        curr += np.array([u, v]) * dt
        path.append(curr.copy())
        if np.linalg.norm(curr - Q_TARGET) < 0.3 or np.abs(curr).max() > 6:
            break
    return np.array(path)

# --- 4. Plotly 차트 구성 ---
fig = go.Figure()

# [중요] 투명 클릭 센서 (가장 아래에 깔아줌)
fig.add_trace(go.Scatter(
    x=grid_x, y=grid_y,
    mode='markers',
    marker=dict(color='rgba(0,0,0,0)', size=5), # 완전히 투명
    hoverinfo='none',
    showlegend=False,
    name="sensor"
))

# 경로와 목표지점들 (위 레이어)
path_data = get_path(st.session_state.vortices)
fig.add_trace(go.Scatter(x=path_data[:,0], y=path_data[:,1], mode='lines', line=dict(color='cyan', width=2), name="Path"))
fig.add_trace(go.Scatter(x=[P_START[0]], y=[P_START[1]], mode='markers', marker=dict(color='green', size=12), name="Start"))
fig.add_trace(go.Scatter(x=[Q_TARGET[0]], y=[Q_TARGET[1]], mode='markers', marker=dict(color='red', size=15, symbol='star'), name="Goal"))

# 배치된 와류들
for vx, vy, vg in st.session_state.vortices:
    color = 'red' if vg > 0 else 'blue'
    fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers', marker=dict(color=color, size=10), showlegend=False))

fig.update_layout(
    width=700, height=700,
    xaxis=dict(range=[-5, 5], fixedrange=True, gridcolor='#333'),
    yaxis=dict(range=[-5, 5], fixedrange=True, gridcolor='#333'),
    template="plotly_dark",
    clickmode='event+select'
)

# 이벤트 감지
event_data = st.plotly_chart(fig, on_select="rerun", key="vortex_chart")

# 클릭 시 좌표 획득
if event_data and "selection" in event_data and event_data["selection"]["points"]:
    # 센서나 점을 클릭했을 때의 좌표
    point = event_data["selection"]["points"][0]
    st.session_state.temp_pos = (point['x'], point['y'])

# --- 5. UI ---
if st.session_state.temp_pos:
    st.sidebar.markdown(f"### 📍 선택된 위치: `{st.session_state.temp_pos[0]:.1f}, {st.session_state.temp_pos[1]:.1f}`")
    v_gamma = st.sidebar.slider("와류 강도(Γ)", -20.0, 20.0, 5.0)
    
    if st.sidebar.button("와류 배치 확정"):
        st.session_state.vortices.append([st.session_state.temp_pos[0], st.session_state.temp_pos[1], v_gamma])
        st.session_state.temp_pos = None
        st.rerun()
    if st.sidebar.button("취소"):
        st.session_state.temp_pos = None
        st.rerun()

if st.sidebar.button("리셋"):
    st.session_state.vortices = []
    st.session_state.temp_pos = None
    st.rerun()
