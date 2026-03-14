import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- 1. 초기화 및 설정 ---
st.set_page_config(page_title="THE VORTEX: Stages", layout="wide")
st.title("🌀 THE VORTEX: 경로 설계")

if 'vortices' not in st.session_state:
    st.session_state.vortices = []
if 'temp_pos' not in st.session_state:
    st.session_state.temp_pos = None
if 'playing' not in st.session_state:
    st.session_state.playing = False
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = 1

P_START = np.array([-4.0, 0.0])
Q_TARGET = np.array([4.0, 0.0])
TARGET_RADIUS = 0.3
LIMIT = 5.0

OBSTACLE_RECT = {'x': [-1.0, 1.0], 'y': [-1.5, 1.5]}

# --- 2. 물리 및 판정 함수 ---
def get_velocity_at(x, y, vortices):
    u, v = 0.0, 0.0
    for vx, vy, vg in vortices:
        dx, dy = x - vx, y - vy
        r2 = dx**2 + dy**2 + 0.1
        u += -(vg / (2 * np.pi)) * (dy / r2)
        v += (vg / (2 * np.pi)) * (dx / r2)
    return u, v

def check_collision(pos):
    if st.session_state.current_stage == 2:
        if OBSTACLE_RECT['x'][0] <= pos[0] <= OBSTACLE_RECT['x'][1] and \
           OBSTACLE_RECT['y'][0] <= pos[1] <= OBSTACLE_RECT['y'][1]:
            return "OBSTACLE"
    if np.abs(pos).max() > LIMIT + 0.2:
        return "WALL"
    return None

# --- 3. 사이드바 UI ---
with st.sidebar:
    st.header("🎮 레벨 디자인")
    stage = st.radio("스테이지 선택", [1, 2], index=st.session_state.current_stage-1)
    if stage != st.session_state.current_stage:
        st.session_state.current_stage = stage
        st.session_state.vortices = []
        st.session_state.playing = False
        st.rerun()
    
    st.divider()
    max_v = st.number_input("최대 와류 개수", 1, 10, 5)
    st.write(f"현재 와류: {len(st.session_state.vortices)} / {max_v}")
    
    if st.session_state.temp_pos and len(st.session_state.vortices) < max_v:
        st.markdown(f"#### 📍 위치: `{st.session_state.temp_pos[0]:.1f}, {st.session_state.temp_pos[1]:.1f}`")
        v_gamma = st.slider("강도 (Γ)", -30.0, 30.0, 10.0)
        col1, col2 = st.columns(2)
        if col1.button("✅ 배치"):
            st.session_state.vortices.append([st.session_state.temp_pos[0], st.session_state.temp_pos[1], v_gamma])
            st.session_state.temp_pos = None
            st.rerun()
        if col2.button("❌ 취소"):
            st.session_state.temp_pos = None
            st.rerun()
            
    st.divider()
    if not st.session_state.playing:
        if st.button("🚀 PLAY", use_container_width=True, type="primary"):
            st.session_state.playing = True
    
    if st.button("🔄 리셋", use_container_width=True):
        st.session_state.vortices = []
        st.session_state.temp_pos = None
        st.session_state.playing = False
        st.rerun()

# --- 4. 렌더링 함수 ---
def draw_stage(current_pos=None, path_history=None, crash=False):
    fig = go.Figure()
    bg_color = "#E0F2F7"
    
    # [1] 벡터 필드
    if st.session_state.vortices:
        arrows_x, arrows_y = [], []
        grid_pts = np.linspace(-LIMIT, LIMIT, 16)
        scale = 0.2
        for gx in grid_pts:
            for gy in grid_pts:
                u, v = get_velocity_at(gx, gy, st.session_state.vortices)
                speed = np.sqrt(u**2 + v**2)
                if speed > 0.05:
                    arrows_x.extend([gx, gx + (u/speed)*scale, None])
                    arrows_y.extend([gy, gy + (v/speed)*scale, None])
        fig.add_trace(go.Scatter(x=arrows_x, y=arrows_y, mode='lines',
                                 line=dict(color='rgba(0, 100, 200, 0.15)', width=1),
                                 hoverinfo='none', showlegend=False))

    if st.session_state.current_stage == 2:
        fig.add_shape(type="rect",
                      x0=OBSTACLE_RECT['x'][0], y0=OBSTACLE_RECT['y'][0],
                      x1=OBSTACLE_RECT['x'][1], y1=OBSTACLE_RECT['y'][1],
                      line=dict(color="RoyalBlue"), fillcolor="LightSlateGray", opacity=0.8)

    # [클릭 센서 정밀도 수정] 21개 -> 101개로 대폭 증가 (0.1 단위 정밀도)
    sensor_pts = np.linspace(-LIMIT, LIMIT, 101)
    sx, sy = np.meshgrid(sensor_pts, sensor_pts)
    fig.add_trace(go.Scatter(x=sx.flatten(), y=sy.flatten(), mode='markers',
                             marker=dict(color='rgba(0,0,0,0)', size=6), showlegend=False))

    # [2] 출발/도착
    fig.add_trace(go.Scatter(x=[P_START[0]], y=[P_START[1]], mode='markers',
                             marker=dict(color='#27AE60', size=15), name="Start",
                             unselected=dict(marker=dict(opacity=1))))
    fig.add_trace(go.Scatter(x=[Q_TARGET[0]], y=[Q_TARGET[1]], mode='markers',
                             marker=dict(color='#C0392B', size=22, symbol='star'), name="Goal",
                             unselected=dict(marker=dict(opacity=1))))

    # [3] 배치된 와류들
    for vx, vy, vg in st.session_state.vortices:
        v_color = '#E67E22' if vg > 0 else '#8E44AD'
        fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers',
                                 marker=dict(color=v_color, size=14, line=dict(width=2, color='white')),
                                 unselected=dict(marker=dict(opacity=1))))

    if st.session_state.temp_pos:
        fig.add_trace(go.Scatter(x=[st.session_state.temp_pos[0]], y=[st.session_state.temp_pos[1]],
                                 mode='markers', marker=dict(color='gray', size=15, symbol='x'),
                                 unselected=dict(marker=dict(opacity=1))))

    if path_history is not None:
        ph = np.array(path_history)
        fig.add_trace(go.Scatter(x=ph[:,0], y=ph[:,1], mode='lines',
                                 line=dict(color='#F1C40F', width=3, dash='dot')))

    if current_pos is not None:
        if crash:
            fig.add_trace(go.Scatter(x=[current_pos[0]], y=[current_pos[1]], mode='markers+text',
                                     marker=dict(color='orange', size=50, symbol='hexagram', 
                                                 line=dict(width=2, color='red')),
                                     text="<b>POW!</b>", textposition="top center",
                                     textfont=dict(size=20, color="red")))
        else:
            fig.add_trace(go.Scatter(x=[current_pos[0]], y=[current_pos[1]], mode='markers',
                                     marker=dict(color='#F1C40F', size=20, symbol='circle',
                                                 line=dict(width=3, color='black')),
                                     unselected=dict(marker=dict(opacity=1))))

    fig.update_layout(
        width=800, height=800, plot_bgcolor=bg_color, paper_bgcolor=bg_color,
        xaxis=dict(range=[-LIMIT-0.2, LIMIT+0.2], fixedrange=True, zeroline=False, showgrid=False),
        yaxis=dict(range=[-LIMIT-0.2, LIMIT+0.2], fixedrange=True, zeroline=False, showgrid=False),
        margin=dict(l=10, r=10, t=10, b=10), clickmode='event+select', showlegend=False
    )
    return fig

# --- 5. 루프 ---
plot_placeholder = st.empty()

if st.session_state.playing:
    curr_pos = P_START.copy()
    path_history = [curr_pos.copy()]
    status = None
    for i in range(300):
        u, v = get_velocity_at(curr_pos[0], curr_pos[1], st.session_state.vortices)
        curr_pos += np.array([u, v]) * 0.1
        path_history.append(curr_pos.copy())
        status = check_collision(curr_pos)
        fig = draw_stage(current_pos=curr_pos, path_history=path_history, crash=(status is not None))
        plot_placeholder.plotly_chart(fig, use_container_width=False, key=f"play_{i}")
        if status: break
        if np.linalg.norm(curr_pos - Q_TARGET) < TARGET_RADIUS:
            status = "SUCCESS"
            break
        time.sleep(0.01)
    if status == "SUCCESS":
        st.balloons(); st.success("🎉 스테이지 클리어!")
    elif status == "OBSTACLE":
        st.error("💥 장애물 충돌! (POW!)")
    elif status == "WALL":
        st.warning("🌊 장외 이탈!")
    st.session_state.playing = False
else:
    fig = draw_stage()
    event_data = plot_placeholder.plotly_chart(fig, on_select="rerun", key="design_chart")
    if event_data and "selection" in event_data and event_data["selection"]["points"]:
        st.session_state.temp_pos = (event_data["selection"]["points"][0]['x'], event_data["selection"]["points"][0]['y'])
        st.rerun()
