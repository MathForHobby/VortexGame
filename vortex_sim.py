import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- 1. 초기화 및 설정 ---
st.set_page_config(page_title="THE VORTEX: Play Mode", layout="wide")
st.title("🌀 THE VORTEX: 설계와 실행")

if 'vortices' not in st.session_state:
    st.session_state.vortices = []
if 'temp_pos' not in st.session_state:
    st.session_state.temp_pos = None
if 'playing' not in st.session_state:
    st.session_state.playing = False

P_START = np.array([-4.0, 0.0])
Q_TARGET = np.array([4.0, 0.0])

# --- 2. 사이드바 조작 ---
with st.sidebar:
    st.header("🎮 Game Control")
    # (1) 와류 개수 제한 설정
    max_vortices = st.number_input("최대 배치 가능 와류 수", 1, 10, 3)
    current_count = len(st.session_state.vortices)
    st.write(f"현재 배치: {current_count} / {max_vortices}")

    if st.session_state.temp_pos and current_count < max_vortices:
        st.info(f"선택 좌표: ({st.session_state.temp_pos[0]:.1f}, {st.session_state.temp_pos[1]:.1f})")
        v_gamma = st.slider("와류 강도(Γ)", -20.0, 20.0, 5.0)
        if st.button("와류 배치 확정"):
            st.session_state.vortices.append([st.session_state.temp_pos[0], st.session_state.temp_pos[1], v_gamma])
            st.session_state.temp_pos = None
            st.rerun()
    
    if st.button("전체 초기화"):
        st.session_state.vortices = []
        st.session_state.temp_pos = None
        st.session_state.playing = False
        st.rerun()

    st.divider()
    # (2) 실행 버튼
    if st.button("🚀 PLAY: Flow 시작!", use_container_width=True):
        st.session_state.playing = True

# --- 3. 물리 및 벡터 필드 연산 ---
def get_velocity_at(x, y, vortices):
    u, v = 0.0, 0.0
    for vx, vy, vg in vortices:
        dx, dy = x - vx, y - vy
        r2 = dx**2 + dy**2 + 0.1 # Singularity 방지
        u += -(vg / (2 * np.pi)) * (dy / r2)
        v += (vg / (2 * np.pi)) * (dx / r2)
    return u, v

# (3) 필드 전체 화살표(Vector Field) 생성
grid_pts = np.linspace(-5, 5, 20)
X, Y = np.meshgrid(grid_pts, grid_pts)
U = np.zeros_like(X)
V = np.zeros_like(Y)

for i in range(len(grid_pts)):
    for j in range(len(grid_pts)):
        u, v = get_velocity_at(X[i,j], Y[i,j], st.session_state.vortices)
        speed = np.sqrt(u**2 + v**2)
        if speed > 0: # 화살표 정규화 (크기 고정, 방향만 표시)
            U[i,j] = u / (speed + 0.1)
            V[i,j] = v / (speed + 0.1)

# --- 4. 렌더링 함수 ---
def draw_stage(current_pos=None):
    fig = go.Figure()

    # 벡터 필드 그리기 (화살표)
    if st.session_state.vortices:
        fig.add_trace(go.Cone(
            x=X.flatten(), y=Y.flatten(), z=np.zeros_like(X.flatten()),
            u=U.flatten(), v=V.flatten(), w=np.zeros_like(X.flatten()),
            sizemode="absolute", sizeref=0.3, showscale=False, 
            colorscale=[[0, 'gray'], [1, 'gray']], opacity=0.3, name="Flow"
        ))

    # 클릭 센서용 그리드
    sensor_pts = np.linspace(-5, 5, 25)
    sx, sy = np.meshgrid(sensor_pts, sensor_pts)
    fig.add_trace(go.Scatter(x=sx.flatten(), y=sy.flatten(), mode='markers', 
                             marker=dict(color='rgba(0,0,0,0)', size=5), showlegend=False))

    # P(출발)와 Q(도착)
    fig.add_trace(go.Scatter(x=[P_START[0]], y=[P_START[1]], mode='markers', marker=dict(color='green', size=15), name="Start"))
    fig.add_trace(go.Scatter(x=[Q_TARGET[0]], y=[Q_TARGET[1]], mode='markers', marker=dict(color='red', size=20, symbol='star'), name="Goal"))

    # 와류들
    for vx, vy, vg in st.session_state.vortices:
        fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers', marker=dict(color='orange', size=12, line=dict(width=2, color='white')), showlegend=False))

    # (2) 플레이어 아이콘 움직임
    if current_pos is not None:
        fig.add_trace(go.Scatter(x=[current_pos[0]], y=[current_pos[1]], mode='markers', 
                                 marker=dict(color='yellow', size=18, symbol='circle', line=dict(width=3, color='black')), name="Player"))

    fig.update_layout(width=800, height=800, template="plotly_dark", 
                      xaxis=dict(range=[-5, 5], fixedrange=True), yaxis=dict(range=[-5, 5], fixedrange=True))
    return fig

# --- 5. 게임 실행 루프 ---
plot_placeholder = st.empty()

if st.session_state.playing:
    curr_pos = P_START.copy()
    path_history = [curr_pos.copy()]
    
    for _ in range(200): # 최대 200프레임 애니메이션
        u, v = get_velocity_at(curr_pos[0], curr_pos[1], st.session_state.vortices)
        curr_pos += np.array([u, v]) * 0.1
        path_history.append(curr_pos.copy())
        
        # 화면 업데이트
        fig = draw_stage(current_pos=curr_pos)
        # 경로선 추가
        h = np.array(path_history)
        fig.add_trace(go.Scatter(x=h[:,0], y=h[:,1], mode='lines', line=dict(color='yellow', width=1, dash='dot')))
        plot_placeholder.plotly_chart(fig, use_container_width=False, key=f"play_{_}")
        
        # 도착 판정
        if np.linalg.norm(curr_pos - Q_TARGET) < 0.3:
            st.balloons()
            st.success("도착 성공!")
            st.session_state.playing = False
            break
        if np.abs(curr_pos).max() > 5:
            st.error("장외 이탈! 다시 설계하세요.")
            st.session_state.playing = False
            break
        time.sleep(0.01)
else:
    # 대기 상태 (설계 모드)
    fig = draw_stage()
    event_data = plot_placeholder.plotly_chart(fig, on_select="rerun", key="setup_chart")
    if event_data and "selection" in event_data and event_data["selection"]["points"]:
        st.session_state.temp_pos = (event_data["selection"]["points"][0]['x'], event_data["selection"]["points"][0]['y'])
        st.rerun()
