import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- 1. 기본 설정 ---
st.set_page_config(page_title="THE VORTEX: Designer", layout="wide")
st.title("🌀 THE VORTEX: Path Designer")
st.markdown("와류를 배치하여 주인공(●)을 도착지점(★)으로 인도하세요!")

# --- 2. 게임 데이터 초기화 ---
if 'vortices' not in st.session_state:
    st.session_state.vortices = []  # [[x, y, gamma], ...]

# --- 3. 사이드바: 조작 및 설정 ---
with st.sidebar:
    st.header("🛠️ Level Editor")
    
    # 출발(P) 및 도착(Q) 설정
    p_start = np.array([-4.0, 0.0])
    q_target = np.array([4.0, 0.0])
    target_radius = 0.3
    
    st.subheader("Add Vortex")
    v_x = st.number_input("Vortex X", -5.0, 5.0, 0.0)
    v_y = st.number_input("Vortex Y", -5.0, 5.0, 0.0)
    v_g = st.slider("Strength (Γ)", -20.0, 20.0, 5.0)
    
    if st.button("Add Vortex"):
        st.session_state.vortices.append([v_x, v_y, v_g])
    
    if st.button("Clear All"):
        st.session_state.vortices = []
        st.rerun()

# --- 4. 물리 연산 엔진 (고정 와류 모델) ---
def compute_trajectory(p_start, vortices, dt=0.05, max_steps=1000):
    path = [p_start.copy()]
    curr_p = p_start.copy()
    
    for _ in range(max_steps):
        u, v = 0.0, 0.0
        # 중첩의 원리: 각 고정 와류에 의한 속도 합산
        for vx, vy, vg in vortices:
            dx = curr_p[0] - vx
            dy = curr_p[1] - vy
            r2 = dx**2 + dy**2 + 0.01 # Singularity 절단
            
            u += -(vg / (2 * np.pi)) * (dy / r2)
            v += (vg / (2 * np.pi)) * (dx / r2)
        
        curr_p += np.array([u, v]) * dt
        path.append(curr_p.copy())
        
        # 경계를 벗어나거나 목표 도달 시 중단
        if np.linalg.norm(curr_p - q_target) < target_radius:
            return np.array(path), True
        if np.abs(curr_p[0]) > 6 or np.abs(curr_p[1]) > 6:
            break
            
    return np.array(path), False

# --- 5. 시각화 및 렌더링 ---
path, win = compute_trajectory(p_start, st.session_state.vortices)

fig, ax = plt.subplots(figsize=(8, 8), facecolor='#111111')
ax.set_facecolor('#111111')

# 1. 출발지(P)와 도착지(Q) 그리기
ax.plot(p_start[0], p_start[1], 'go', markersize=10, label="Start (P)")
ax.plot(q_target[0], q_target[1], 'r*', markersize=15, label="Goal (Q)")
circle = plt.Circle(q_target, target_radius, color='red', fill=False, linestyle='--')
ax.add_patch(circle)

# 2. 와류 시각화
for vx, vy, vg in st.session_state.vortices:
    color = '#FF4B4B' if vg > 0 else '#1C83E1'
    ax.plot(vx, vy, 'o', color=color, markersize=8)
    # 방향 표시용 화살표 (단순화)
    ax.annotate("", xy=(vx, vy+0.2), xytext=(vx, vy-0.2),
                arrowprops=dict(arrowstyle="->", color=color, lw=2))

# 3. 경로(Trajectory) 그리기
if len(path) > 1:
    ax.plot(path[:, 0], path[:, 1], color='cyan', lw=2, alpha=0.8)
    # 화살표로 진행 방향 표시
    mid = len(path) // 2
    ax.annotate("", xy=path[mid+1], xytext=path[mid],
                arrowprops=dict(arrowstyle="->", color='cyan', lw=2))

# 4. 그래프 디테일
ax.set_xlim(-6, 6)
ax.set_ylim(-6, 6)
ax.set_aspect('equal')
ax.grid(color='#333333', linestyle='--', alpha=0.5)
ax.legend()

st.pyplot(fig)

# 결과 메시지
if win:
    st.success("🎉 목표 지점에 도달했습니다! 성공!")
else:
    st.warning("경로를 설계하여 Q(별표)까지 도달시키세요.")
