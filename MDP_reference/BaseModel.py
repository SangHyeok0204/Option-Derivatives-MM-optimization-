"""
스마트폰 배터리/발열 관리 MDP 모델

Reward 구조:
- U_user: 사용자 효용 (b_t, x_t, n_t의 선형 조합)
- U_system: 시스템 효용 (r_t, g_t, c_t에 대한 (1-exp) 곱)
- 페널티: 에너지 사용, 발열, 심리적 불안

모든 action (r_t, g_t, c_t)은 [0, 1] 범위로 정규화됨
"""

from collections import namedtuple
import numpy as np


# ===============================
# 하이퍼파라미터 
# ===============================

USER_TYPE = 'Heavy' #이거 Heavy, Light , Mid 중 선택하면서 plot 비교하시면 됩니당. 실행은 DriverScript.py 에서 하면됨.

USER_PARAMS = {  # 사용자 유형별 외생변수 분포
    'Light': {'b_mean': 0.70, 'b_std': 0.07, 'x_min': 0.0, 'x_max': 0.4, 'p_wifi': 0.9},
    'Mid':   {'b_mean': 0.55, 'b_std': 0.10, 'x_min': 0.2, 'x_max': 0.8, 'p_wifi': 0.6},
    'Heavy': {'b_mean': 0.80, 'b_std': 0.10, 'x_min': 0.6, 'x_max': 1.0, 'p_wifi': 0.3},
}

# 배터리 전이 계수 (λ) - actions are now in [0,1]
LAMBDA_PARAMS = dict(
    lambda1=0.005,   # 밝기(b) 영향
    lambda2=0.02,    # 앱 사용량(x) 영향
    lambda3=0.015,   # 네트워크(n) 영향
    lambda4=0.03,    # 주사율(r) 영향
    lambda5=0.03,    # GPU(g) 영향
    lambda6=0.05,    # 화면밝기(c) 영향
)

# 온도 전이 계수 (φ)
PHI_PARAMS = dict(
    phi1=0.003,   # 밝기(b) 영향
    phi2=0.02,    # 앱 사용량(x) 영향
    phi3=0.01,    # 네트워크(n) 영향
    phi4=0.02,    # 주사율(r) 영향
    phi5=0.05,    # GPU(g) 영향
    phi6=0.03,    # 화면밝기(c) 영향
    phi7=0.5,     # 쿨링 계수 배율
)

DELTA_COOLING = 0.1  # 쿨링 계수
SIGMA_E = 0.01       # 배터리 노이즈
SIGMA_H = 0.01       # 온도 노이즈

# User utility weights (U_user = w_b*b + w_x*x + w_n*n)
W_B = 1.0   # 밝기 가중치
W_X = 0.5   # 앱 사용량 가중치
W_N = 0.3   # 네트워크 가중치

# System utility curvature params (U_system = prod of (1 - exp(-k*action)))
K1 = 3.0    # 주사율 곡률
K2 = 3.0    # GPU 곡률
K3 = 3.0    # 화면밝기 곡률

# Penalty weights
LAMBDA_E = 1.0   # 에너지 사용 페널티 가중치
LAMBDA_H = 0.5   # 발열 페널티 가중치
LAMBDA_B = 0.3   # 심리적 불안 페널티 가중치
KAPPA = 5.0      # 심리적 불안 곡률

GAMMA = 0.99     # 할인율


# ===============================
# SmartphoneModel
# ===============================

class SmartphoneModel:

    def __init__(self, state_names, x_names, s_0, T, reward_type='Cumulative', 
                 seed=42, user_type=None):
        self.prng = np.random.RandomState(seed)
        self.seed = seed
        self.T = T
        self.t = 0
        self.reward_type = reward_type
        self.obj = 0.0
        self.state_names = state_names
        self.x_names = x_names
        self.State = namedtuple('State', state_names)
        self.Decision = namedtuple('Decision', x_names)
        self.init_state = s_0
        self.state = self.build_state(s_0)
        self.history = []

        # Discount factor
        self.gamma = GAMMA
        
        # Transition parameters
        self.lambda_params = LAMBDA_PARAMS
        self.phi_params = PHI_PARAMS
        self.delta = DELTA_COOLING
        self.sigma_e = SIGMA_E
        self.sigma_h = SIGMA_H
        
        # User utility weights: U_user = w_b*b + w_x*x + w_n*n
        self.w_b = W_B
        self.w_x = W_X
        self.w_n = W_N
        
        # System utility curvature: U_system = (1-exp(-k1*r)) * (1-exp(-k2*g)) * (1-exp(-k3*c))
        self.k1 = K1
        self.k2 = K2
        self.k3 = K3
        
        # Penalty weights
        self.lambda_E = LAMBDA_E  # Energy use penalty
        self.lambda_H = LAMBDA_H  # Heat penalty
        self.lambda_B = LAMBDA_B  # Battery anxiety penalty
        self.kappa = KAPPA        # Battery anxiety curvature
        
        # User parameters
        self.user_params = USER_PARAMS
        self.user_type = user_type if user_type else USER_TYPE

    def build_state(self, info):
        return self.State(*[info[k] for k in self.state_names])

    def build_decision(self, info):
        return self.Decision(*[info[k] for k in self.x_names])

    def step(self, decision):
        """한 스텝 진행"""
        self.t += 1
        exog_info = self.exog_info_fn(decision)
        reward = self.objective_fn(decision, exog_info)
        
        if self.reward_type == 'Cumulative':
            self.obj += reward
        else:
            if self.t == self.T:
                self.obj = reward
        
        self.history.append({
            't': self.t, 
            'state': self.state, 
            'decision': decision,
            'exog_info': exog_info, 
            'reward': reward
        })
        
        transition_info = self.transition_fn(decision, exog_info)
        self.state = self.build_state(transition_info)

    def reset(self):
        """모델 초기화"""
        self.t = 0
        self.obj = 0.0
        self.state = self.build_state(self.init_state)
        self.history = []

    def exog_info_fn(self, decision):
        """외생변수 샘플링: W_t = (b_t, x_t, n_t), all in [0, 1]"""
        params = self.user_params[self.user_type]
        
        # b_t: 사용자 밝기 선호 (0~1)
        b_t = np.clip(self.prng.normal(params['b_mean'], params['b_std']), 0.0, 1.0)
        
        # x_t: 앱 사용량 (0~1, uniform)
        x_t = self.prng.uniform(params['x_min'], params['x_max'])
        
        # n_t: 네트워크 타입 (0=WiFi, 1=Cellular)
        n_t = self.prng.choice([0.0, 1.0], p=[params['p_wifi'], 1.0 - params['p_wifi']])
        
        return {"b": float(b_t), "x": float(x_t), "n": float(n_t)}

    def cooling_fn(self, h_t):
        """Cooling(h_t) = δ * h_t"""
        return self.delta * h_t

    def transition_fn(self, decision, exog_info):
        """상태 전이: S_t → S_{t+1}
        
        Actions (r_t, g_t, c_t) are in [0, 1].
        """
        e_t, h_t = self.state.e, self.state.h
        b_t, x_t, n_t = exog_info["b"], exog_info["x"], exog_info["n"]
        r_t, g_t, c_t = decision.r, decision.g, decision.c
        
        # 배터리 전이: e_{t+1} = e_t - Δe + noise
        lam = self.lambda_params
        delta_e = (lam["lambda1"] * b_t + 
                   lam["lambda2"] * x_t + 
                   lam["lambda3"] * n_t +
                   lam["lambda4"] * r_t + 
                   lam["lambda5"] * g_t + 
                   lam["lambda6"] * c_t)
        epsilon_e = self.prng.normal(0, self.sigma_e)
        e_next = np.clip(e_t - delta_e + epsilon_e, 0.0, 1.0)
        
        # 온도 전이: h_{t+1} = h_t + Δh - cooling + noise
        phi = self.phi_params
        delta_h = (phi["phi1"] * b_t + 
                   phi["phi2"] * x_t + 
                   phi["phi3"] * n_t +
                   phi["phi4"] * r_t + 
                   phi["phi5"] * g_t + 
                   phi["phi6"] * c_t)
        cooling = phi["phi7"] * self.cooling_fn(h_t)
        epsilon_h = self.prng.normal(0, self.sigma_h)
        h_next = np.clip(h_t + delta_h - cooling + epsilon_h, 0.0, 1.0)

        return {"e": float(e_next), "h": float(h_next)}

    def objective_fn(self, decision, exog_info):
  
        e_t, h_t = self.state.e, self.state.h
        
        # 배터리가 0이면 reward 0
        if e_t <= 0:
            return 0.0
        
        b_t, x_t, n_t = exog_info["b"], exog_info["x"], exog_info["n"]
        r_t, g_t, c_t = decision.r, decision.g, decision.c
        
        # User utility: linear combination
        U_user = self.w_b * b_t + self.w_x * x_t + self.w_n * n_t
        
        # System utility: product of (1 - exp(-k * action))
        # r_t, g_t, c_t are in [0, 1]
        term_r = 1.0 - np.exp(-self.k1 * r_t)
        term_g = 1.0 - np.exp(-self.k2 * g_t)
        term_c = 1.0 - np.exp(-self.k3 * c_t)
        U_system = term_r * term_g * term_c
        
        # Calculate next state for energy penalty
        next_state = self.transition_fn(decision, exog_info)
        e_tp1 = next_state["e"]
        
        # Penalties
        E_use = self.lambda_E * (e_t - e_tp1)           # Energy use penalty
        H_pen = self.lambda_H * (h_t ** 2)              # Heat penalty
        B_psy = self.lambda_B * np.exp(-self.kappa * e_t)  # Battery anxiety penalty
        
        # Instant reward
        instant_reward = U_user * U_system - (E_use + H_pen + B_psy)
        
        # Apply discount factor
        return (self.gamma ** self.t) * instant_reward
