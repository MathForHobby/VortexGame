import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 1. 초기화 ---
st.set_page_config(page_title="THE VORTEX: Click & Play", layout="wide")
st.title("🌀 THE VORTEX: Designer Mode")

if 'vortices' not in st.session_state:
    st.session_state.vortices = []
if 'temp_pos' not in st.session_state:
    st.session_state.temp_pos = None

# 고정된 P(출발)와 Q(도착)
P_START = np.array([-4.0, 0.0])
Q_TARGET = np.array([4.0, 0.0])

# --- 2. 물리 연산 (Trajectory) ---
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

# --- 3. Plotly 인터랙티브 맵 ---
fig = go.Figure()

# 경로 그리기
path_data = get_path(st.session_state.vortices)
fig.add_trace(go.Scatter(x=path_data[:,0], y=path_data[:,1], mode='lines', line=dict(color='cyan', width=2), name="Path"))

# P와 Q 표시
fig.add_trace(go.Scatter(x=[P_START[0]], y=[P_START[1]], mode='markers', marker=dict(color='green', size=12), name="Start"))
fig.add_trace(go.Scatter(x=[Q_TARGET[0]], y=[Q_TARGET[1]], mode='markers', marker=dict(color='red', size=15, symbol='star'), name="Goal"))

# 배치된 와류들
for vx, vy, vg in st.session_state.vortices:
    color = 'red' if vg > 0 else 'blue'
    fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers', marker=dict(color=color, size=10), showlegend=False))

# 차트 설정
fig.update_layout(
    width=700, height=700,
    xaxis=dict(range=[-6, 6], fixedrange=True),
    yaxis=dict(range=[-6, 6], fixedrange=True),
    template="plotly_dark",
    clickmode='event+select'
)

# 클릭 이벤트 감지 (Streamlit 1.35+ 기준 on_select 기능 활용)
event_data = st.plotly_chart(fig, on_select="rerun", key="vortex_chart")

# 클릭 시 임시 좌표 저장
if event_data and "selection" in event_data and event_data["selection"]["points"]:
    point = event_data["selection"]["points"][0]
    st.session_state.temp_pos = (point['x'], point['y'])

# --- 4. 동적 슬라이더 UI (클릭했을 때만 나타남) ---
if st.session_state.temp_pos:
    st.sidebar.success(f"선택된 좌표: ({st.session_state.temp_pos[0]:.2f}, {st.session_state.temp_pos[1]:.2f})")
    v_gamma = st.sidebar.slider("와류 강도 결정 (Γ)", -20.0, 20.0, 5.0, key="gamma_slider")
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("와류 배치 확정"):
        st.session_state.vortices.append([st.session_state.temp_pos[0], st.session_state.temp_pos[1], v_gamma])
        st.session_state.temp_pos = None
        st.rerun()
    if col2.button("취소"):
        st.session_state.temp_pos = None
        st.rerun()

if st.sidebar.button("전체 초기화"):
    st.session_state.vortices = []
    st.session_state.temp_pos = None
    st.rerun()
