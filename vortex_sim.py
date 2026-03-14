import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- 1. 초기화 및 설정 ---
st.set_page_config(page_title="THE VORTEX", layout="wide")
st.title("🌀 THE VORTEX: 설계와 실행")
st.markdown("맵을 클릭하여 와류를 배치하세요. **PLAY**를 누르면 시뮬레이션이 시작됩니다.")

if 'vortices' not in st.session_state:
    st.session_state.vortices = []
if 'temp_pos' not in st.session_state:
    st.session_state.temp_pos = None
if 'playing' not in st.session_state:
    st.session_state.playing = False

P_START = np.array([-4.0, 0.0])
Q_TARGET = np.array([4.0, 0.0])
TARGET_RADIUS = 0.3
LIMIT = 5.0

# --- 2. 물리 엔진 ---
def get_velocity_at(x, y, vortices):
    u, v = 0.0, 0.0
    for vx, vy, vg in vortices:
        dx, dy = x - vx, y - vy
        r2 = dx**2 + dy**2 + 0.1
        u += -(vg / (2 * np.pi)) * (dy / r2)
        v += (vg / (2 * np.pi)) * (dx / r2)
    return u, v

# --- 3. 사이드바 UI ---
with st.sidebar:
    st.header("🎮 조작 패널")
    max_v = st.number_input("최대 와류 개수", 1, 20, 5)
    st.write(f"현재 배치: {len(st.session_state.vortices)} / {max_v}")
    
    if st.session_state.temp_pos and len(st.session_state.vortices) < max_v:
        st.markdown(f"#### 📍 선택된 위치: `{st.session_state.temp_pos[0]:.1f}, {st.session_state.temp_pos[1]:.1f}`")
        v_gamma = st.slider("와류 강도 (Γ)", -30.0, 30.0, 10.0)
        
        col1, col2 = st.columns(2)
        if col1.button("✅ 확정", use_container_width=True):
            st.session_state.vortices.append([st.session_state.temp_pos[0], st.session_state.temp_pos[1], v_gamma])
            st.session_state.temp_pos = None
            st.rerun()
        if col2.button("❌ 취소", use_container_width=True):
            st.session_state.temp_pos = None
            st.rerun()
            
    st.divider()
    if not st.session_state.playing:
        if st.button("🚀 PLAY: 흐름 시작", use_container_width=True, type="primary"):
            if not st.session_state.vortices:
                st.warning("와류를 먼저 배치하세요!")
            else:
                st.session_state.playing = True
    
    if st.button("🔄 리셋 (초기화)", use_container_width=True):
        st.session_state.vortices = []
        st.session_state.temp_pos = None
        st.session_state.playing = False
        st.rerun()

# --- 4. 렌더링 함수 (버그 수정됨) ---
def draw_stage(current_pos=None, path_history=None):
    fig = go.Figure()

    # 공통 설정: 선택 시 다른 요소가 사라지지 않게 강제 설정
    no_hide = dict(marker=dict(opacity=1), line=dict(opacity=1))

    # [배경 센서]
    sensor_pts = np.linspace(-LIMIT, LIMIT, 21)
    sx, sy = np.meshgrid(sensor_pts, sensor_pts)
    fig.add_trace(go.Scatter(
        x=sx.flatten(), y=sy.flatten(), mode='markers',
        marker=dict(color='rgba(0,0,0,0)', size=10),
        showlegend=False, hoverinfo='none',
        unselected=dict(marker=dict(opacity=0)) # 센서는 평소에 안 보임
    ))

    # [1] 벡터 필드 (Flow)
    if st.session_state.vortices:
        grid_pts = np.linspace(-LIMIT, LIMIT, 15)
        for gx in grid_pts:
            for gy in grid_pts:
                u, v = get_velocity_at(gx, gy, st.session_state.vortices)
                speed = np.sqrt(u**2 + v**2)
                if speed > 0.1:
                    scale = 0.25
                    fig.add_annotation(
                        x=gx + (u/speed)*scale, y=gy + (v/speed)*scale,
                        ax=gx, ay=gy, xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=0.8,
                        arrowcolor="rgba(255, 255, 255, 0.15)"
                    )

    # [2] 출발/도착 지점 (unselected 설정 추가로 사라짐 방지)
    fig.add_trace(go.Scatter(x=[P_START[0]], y=[P_START[1]], mode='markers',
                             marker=dict(color='#2ECC71', size=15), name="Start",
                             unselected=dict(marker=dict(opacity=1))))
    fig.add_trace(go.Scatter(x=[Q_TARGET[0]], y=[Q_TARGET[1]], mode='markers',
                             marker=dict(color='#E74C3C', size=20, symbol='star'), name="Goal",
                             unselected=dict(marker=dict(opacity=1))))

    # [3] 배치된 와류들
    for vx, vy, vg in st.session_state.vortices:
        v_color = '#F39C12' if vg > 0 else '#9B59B6'
        fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers',
                                 marker=dict(color=v_color, size=12, line=dict(width=2, color='white')),
                                 unselected=dict(marker=dict(opacity=1))))

    # [4] 클릭한 지점 미리보기 (Ghost Vortex)
    if st.session_state.temp_pos:
        tx, ty = st.session_state.temp_pos
        fig.add_trace(go.Scatter(x=[tx], y=[ty], mode='markers',
                                 marker=dict(color='white', size=15, symbol='x-thin', line=dict(width=2)),
                                 name="Click Point"))

    # [5] 경로 및 플레이어
    if path_history is not None:
        ph = np.array(path_history)
        fig.add_trace(go.Scatter(x=ph[:,0], y=ph[:,1], mode='lines',
                                 line=dict(color='yellow', width=2, dash='dot'),
                                 unselected=dict(line=dict(opacity=1))))

    if current_pos is not None:
        fig.add_trace(go.Scatter(x=[current_pos[0]], y=[current_pos[1]], mode='markers',
                                 marker=dict(color='#F1C40F', size=18, symbol='circle',
                                             line=dict(width=3, color='black')),
                                 unselected=dict(marker=dict(opacity=1))))

    fig.update_layout(
        width=800, height=800, template="plotly_dark",
        xaxis=dict(range=[-LIMIT-0.2, LIMIT+0.2], fixedrange=True, zeroline=False, showgrid=False),
        yaxis=dict(range=[-LIMIT-0.2, LIMIT+0.2], fixedrange=True, zeroline=False, showgrid=False),
        margin=dict(l=10, r=10, t=10, b=10),
        clickmode='event+select', showlegend=False
    )
    return fig

# --- 5. 루프 ---
plot_placeholder = st.empty()

if st.session_state.playing:
    curr_pos = P_START.copy()
    path_history = [curr_pos.copy()]
    success = False
    for i in range(300):
        u, v = get_velocity_at(curr_pos[0], curr_pos[1], st.session_state.vortices)
        curr_pos += np.array([u, v]) * 0.1
        path_history.append(curr_pos.copy())
        fig = draw_stage(current_pos=curr_pos, path_history=path_history)
        plot_placeholder.plotly_chart(fig, use_container_width=False, key=f"play_{i}")
        if np.linalg.norm(curr_pos - Q_TARGET) < TARGET_RADIUS:
            success = True
            break
        if np.abs(curr_pos).max() > LIMIT + 0.5:
            st.error("장외 이탈!")
            break
        time.sleep(0.01)
    if success:
        st.balloons()
        st.success("🎉 목표 도달!")
    st.session_state.playing = False
else:
    fig = draw_stage()
    event_data = plot_placeholder.plotly_chart(fig, on_select="rerun", key="design_chart")
    if event_data and "selection" in event_data and event_data["selection"]["points"]:
        pt = event_data["selection"]["points"][0]
        st.session_state.temp_pos = (pt['x'], pt['y'])
        st.rerun()
