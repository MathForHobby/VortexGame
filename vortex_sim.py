import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# --- 1. 환경 설정 ---
st.set_page_config(page_title="THE VORTEX: Lite", layout="wide")
st.title("🌀 THE VORTEX: Prototype")
st.sidebar.header("Physics Settings")

# --- 2. 하이퍼파라미터 (사이드바) ---
n_particles = st.sidebar.slider("입자 수", 100, 2000, 500)
dt = st.sidebar.slider("시간 간격 (dt)", 0.01, 0.1, 0.05)
gamma = st.sidebar.slider("와류 강도 (Γ)", 1.0, 10.0, 5.0)
vortex_dist = st.sidebar.slider("와류 간격 (d)", 0.5, 4.0, 1.0)

# --- 3. 초기 상태 설정 (Session State) ---
if 'particles' not in st.session_state:
    # 초기 잉크 배치 (중앙에 뭉쳐 있는 형태)
    st.session_state.particles = np.random.normal(0, 0.5, (n_particles, 2))
    st.session_state.running = False

# --- 4. 와류 물리 엔진 (수학적 핵심) ---
def get_velocity(pos, vortices):
    """
    각 입자 위치(pos)에서 모든 와류(vortices)에 의한 유도 속도 계산
    vortices: [[x, y, gamma], ...]
    """
    u_total = np.zeros_like(pos)
    for vx, vy, vg in vortices:
        dx = pos[:, 0] - vx
        dy = pos[:, 1] - vy
        r2 = dx**2 + dy**2 + 1e-6  # Singularity 방지
        
        # 2D Point Vortex Velocity Formula
        # u = -gamma/(2*pi) * dy/r^2
        # v =  gamma/(2*pi) * dx/r^2
        u_total[:, 0] += -(vg / (2 * np.pi)) * (dy / r2)
        u_total[:, 1] += (vg / (2 * np.pi)) * (dx / r2)
    return u_total

# --- 5. 애니메이션 루프 ---
col1, col2 = st.columns([3, 1])

with col2:
    if st.button("Simulation Start/Stop"):
        st.session_state.running = not st.session_state.running
    if st.button("Reset"):
        st.session_state.particles = np.random.normal(0, 0.5, (n_particles, 2))
        st.rerun()

# 와류 위치 설정 (Dipole 구조)
vortices = [
    [-vortex_dist/2, 0, gamma],   # 왼쪽 와류 (반시계)
    [vortex_dist/2, 0, -gamma]    # 오른쪽 와류 (시계)
]

with col1:
    placeholder = st.empty()

    # 시뮬레이션 실행
    while st.session_state.running:
        # 1. 속도 계산 및 위치 업데이트 (Euler Integration)
        vel = get_velocity(st.session_state.particles, vortices)
        st.session_state.particles += vel * dt
        
        # 2. 시각화 (Matplotlib)
        fig, ax = plt.subplots(figsize=(8, 8), facecolor='black')
        ax.scatter(st.session_state.particles[:, 0], st.session_state.particles[:, 1], 
                   s=1, c='cyan', alpha=0.6)
        
        # 와류 위치 표시
        for vx, vy, vg in vortices:
            color = 'red' if vg > 0 else 'blue'
            ax.plot(vx, vy, 'o', color=color, markersize=10)
        
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        ax.set_axis_off()
        
        placeholder.pyplot(fig)
        plt.close(fig)
        time.sleep(0.01) # 프레임 속도 조절
