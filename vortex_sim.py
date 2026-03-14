import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- 1. 초기화 및 상반기 설정 ---
st.set_page_config(page_title="THE VORTEX", layout="wide")
st.title("🌀 THE VORTEX: 설계와 실행")
st.markdown("맵을 클릭하여 와류를 배치하고, **PLAY**를 눌러 주인공을 Goal로 인도하세요.")

# 세션 상태 초기화
if 'vortices' not in st.session_state:
    st.session_state.vortices = []
if 'temp_pos' not in st.session_state:
    st.session_state.temp_pos = None
if 'playing' not in st.session_state:
    st.session_state.playing = False

# 게임 상수
P_START = np.array([-4.0, 0.0])
Q_TARGET = np.array([4.0, 0.0])
TARGET_RADIUS = 0.3
LIMIT = 5.0

# --- 2. 물리 엔진 함수 ---
def get_velocity_at(x, y, vortices):
    """특정 좌표 (x, y)에서의 합성 유속 u, v를 계산"""
    u, v = 0.0, 0.0
    for vx, vy, vg in vortices:
        dx, dy = x - vx, y - vy
        r2 = dx**2 + dy**2 + 0.1  # Singularity 방지
        u += -(vg / (2 * np.pi)) * (dy / r2)
        v += (vg / (2 * np.pi)) * (dx / r2)
    return u, v

# --- 3. 사이드바 UI 컨트롤 ---
with st.sidebar:
    st.header("🎮 조작 패널")
    
    # (1) 와류 개수 제한 설정
    max_v = st.number_input("최대 와류 개수", 1, 20, 5)
    st.write(f"현재 배치된 와류: {len(st.session_state.vortices)} / {max_v}")
    
    # 와류 배치 UI
    if st.session_state.temp_pos and len(st.session_state.vortices) < max_v:
        st.info(f"선택 지점: ({st.session_state.temp_pos[0]:.1f}, {st.session_state.temp_pos[1]:.1f})")
        v_gamma = st.slider("와류 강도 (Γ)", -30.0, 30.0, 10.0)
        if st.button("✅ 배치 확정"):
            st.session_state.vortices.append([st.session_state.temp_pos[0], st.session_state.temp_pos[1], v_gamma])
            st.session_state.temp_pos = None
            st.rerun()
        if st.button("❌ 취소"):
            st.session_state.temp_pos = None
            st.rerun()
            
    st.divider()
    
    # (2) 게임 실행 버튼
    if not st.session_state.playing:
        if st.button("🚀 PLAY: 흐름 시작", use_container_width=True, type="primary"):
            if not st.session_state.vortices:
                st.warning("와류를 먼저 배치하세요!")
            else:
                st.session_state.playing = True
    
    if st.button("🔄 리셋 (모든 와류 삭제)", use_container_width=True):
        st.session_state.vortices = []
        st.session_state.temp_pos = None
        st.session_state.playing = False
        st.rerun()

# --- 4. 렌더링 함수 (Pure 2D Plotly) ---
def draw_stage(current_pos=None, path_history=None):
    fig = go.Figure()

    # [배경] 투명 클릭 센서 (배경 어디든 클릭 가능하게 함)
    sensor_pts = np.linspace(-LIMIT, LIMIT, 25)
    sx, sy = np.meshgrid(sensor_pts, sensor_pts)
    fig.add_trace(go.Scatter(
        x=sx.flatten(), y=sy.flatten(),
        mode='markers',
        marker=dict(color='rgba(0,0,0,0)', size=10),
        showlegend=False,
        hoverinfo='none'
    ))

    # [1] 벡터 필드 (Flow Arrows) 시각화
    if st.session_state.vortices:
        grid_pts = np.linspace(-LIMIT, LIMIT, 16)
        for gx in grid_pts:
            for gy in grid_pts:
                u, v = get_velocity_at(gx, gy, st.session_state.vortices)
                speed = np.sqrt(u**2 + v**2)
                if speed > 0.1:
                    scale = 0.25
                    # 화살표 그리기 (Annotation 사용)
                    fig.add_annotation(
                        x=gx + (u/speed)*scale, y=gy + (v/speed)*scale,
                        ax=gx, ay=gy, xref="x", yref="y", axref="x", ayref="y",
                        showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=0.8,
                        arrowcolor="rgba(255, 255, 255, 0.2)"
                    )

    # [2] 출발(P)과 도착(Q) 마커
    fig.add_trace(go.Scatter(x=[P_START[0]], y=[P_START[1]], mode='markers',
                             marker=dict(color='#2ECC71', size=15), name="Start"))
    fig.add_trace(go.Scatter(x=[Q_TARGET[0]], y=[Q_TARGET[1]], mode='markers',
                             marker=dict(color='#E74C3C', size=20, symbol='star'), name="Goal"))

    # [3] 배치된 와류들
    for vx, vy, vg in st.session_state.vortices:
        v_color = '#F39C12' if vg > 0 else '#9B59B6'
        fig.add_trace(go.Scatter(x=[vx], y=[vy], mode='markers',
                                 marker=dict(color=v_color, size=12, line=dict(width=2, color='white')),
                                 hovertext=f"Strength: {vg}"))

    # [4] 경로 이력 (Path History)
    if path_history is not None and len(path_history) > 1:
        ph = np.array(path_history)
        fig.add_trace(go.Scatter(x=ph[:,0], y=ph[:,1], mode='lines',
                                 line=dict(color='yellow', width=2, dash='dot')))

    # [5] 플레이어 아이콘 (현재 위치)
    if current_pos is not None:
        fig.add_trace(go.Scatter(x=[current_pos[0]], y=[current_pos[1]], mode='markers',
                                 marker=dict(color='#F1C40F', size=18, symbol='circle',
                                             line=dict(width=3, color='black')), name="Player"))

    # 레이아웃 최적화 (2D 고정)
    fig.update_layout(
        width=800, height=800,
        template="plotly_dark",
        xaxis=dict(range=[-LIMIT-0.5, LIMIT+0.5], fixedrange=True, zeroline=False, showgrid=False),
        yaxis=dict(range=[-LIMIT-0.5, LIMIT+0.5], fixedrange=True, zeroline=False, showgrid=False),
        margin=dict(l=20, r=20, t=20, b=20),
        clickmode='event+select',
        showlegend=False
    )
    return fig

# --- 5. 메인 로직 및 실행 루프 ---
plot_placeholder = st.empty()

if st.session_state.playing:
    # 실행 모드: 입자가 움직임
    curr_pos = P_START.copy()
    path_history = [curr_pos.copy()]
    
    success = False
    for i in range(250): # 최대 프레임 수
        u, v = get_velocity_at(curr_pos[0], curr_pos[1], st.session_state.vortices)
        curr_pos += np.array([u, v]) * 0.1  # 속도 조절(dt)
        path_history.append(curr_pos.copy())
        
        # 화면 업데이트
        fig = draw_stage(current_pos=curr_pos, path_history=path_history)
        plot_placeholder.plotly_chart(fig, use_container_width=False, key=f"play_frame_{i}")
        
        # 승리/패배 판정
        if np.linalg.norm(curr_pos - Q_TARGET) < TARGET_RADIUS:
            success = True
            break
        if np.abs(curr_pos).max() > LIMIT + 0.5:
            st.error("장외 이탈! 와류 배치를 다시 고민해 보세요.")
            break
        time.sleep(0.01) # 애니메이션 속도
    
    if success:
        st.balloons()
        st.success("🎉 축하합니다! 도착 지점에 성공적으로 도달했습니다!")
    
    st.session_state.playing = False # 실행 종료 후 대기 모드로 전환

else:
    # 설계 모드: 클릭 대기
    fig = draw_stage()
    event_data = plot_placeholder.plotly_chart(fig, on_select="rerun", key="design_chart")
    
    if event_data and "selection" in event_data and event_data["selection"]["points"]:
        # 클릭된 좌표 저장
        pt = event_data["selection"]["points"][0]
        st.session_state.temp_pos = (pt['x'], pt['y'])
        st.rerun()
