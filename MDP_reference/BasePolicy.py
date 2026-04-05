from copy import copy, deepcopy
import numpy as np
from BaseModel import SmartphoneModel, USER_TYPE


# ===============================
# 하이퍼파라미터
# ===============================

POLICY_TYPE = 'adaptive_theta'  # 정책 선택: 'heuristic' | 'myopic' | 'lookahead_1' | 'adaptive_theta'
POLICY_SEED = 1885           # 정책 전용 난수 시드

# BaseDriverScript.py와 동일한 설정 (AdaptiveThetaPolicy용)
STATE_NAMES = ['e', 'h']
DECISION_NAMES = ['r', 'g', 'c']
INIT_STATE = {'e': 1.0, 'h': 0.3}
HORIZON_T = 18
REWARD_TYPE = 'Cumulative'


# ===============================
# 영역 기반 근시안적 정책 설정
# ===============================

# 기본 임계값 (배터리 및 온도) - __init__에 전달되지 않으면 사용
DEFAULT_THETA_1 = 0.30   # 저배터리 임계값 (theta_1)
DEFAULT_THETA_2 = 0.70   # 고배터리 임계값 (theta_2)
DEFAULT_THETA_H = 0.70   # 고온 임계값 (theta_h)

# 이산 행동: (r, g, c) 모두 [0, 1] 범위
# 최대 절약 → 최대 성능 순서
A1_ULTRA_SAVING    = (0.1, 0.1, 0.0)   # 초절약 모드
A2_THERMAL_CONTROL = (0.3, 0.3, 0.2)   # 발열 제어 모드
A3_BALANCED        = (0.5, 0.5, 0.5)   # 균형 모드
A4_PERFORMANCE     = (0.7, 0.7, 0.7)   # 성능 모드
A5_HIGH_PERF       = (0.9, 0.8, 0.8)   # 고성능 모드
A6_MAX_PERF        = (1.0, 1.0, 1.0)   # 최대 성능 모드

DISCRETE_ACTIONS = [
    A1_ULTRA_SAVING,     # 인덱스 0: 초절약
    A2_THERMAL_CONTROL,  # 인덱스 1: 발열 제어
    A3_BALANCED,         # 인덱스 2: 균형
    A4_PERFORMANCE,      # 인덱스 3: 성능
    A5_HIGH_PERF,        # 인덱스 4: 고성능
    A6_MAX_PERF,         # 인덱스 5: 최대 성능
]


# ===============================
# BasePolicy
# ===============================

class BasePolicy:

    def __init__(self, model, policy_type=None, 
                 theta_1=None, theta_2=None, theta_h=None, **kwargs):
        self.M = model
        self.prng = np.random.RandomState(POLICY_SEED)
        self.policy_type = policy_type if policy_type else POLICY_TYPE
        
        self.theta_1 = theta_1 if theta_1 is not None else DEFAULT_THETA_1
        self.theta_2 = theta_2 if theta_2 is not None else DEFAULT_THETA_2
        self.theta_h = theta_h if theta_h is not None else DEFAULT_THETA_H
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run_policy(self):
        """전체 시뮬레이션 실행"""
        model_copy = copy(self.M)
        model_copy.reset()
        policy_copy = self.__class__(model_copy, **self._get_params())
        for t in range(model_copy.T):
            decision = policy_copy.get_decision()
            model_copy.step(decision)
        return (model_copy.obj, model_copy.history.copy())
    
    def _get_params(self):
        """정책 파라미터 추출 (모델과 난수생성기 제외)"""
        params = {}
        for key, value in self.__dict__.items():
            if key not in ['M', 'prng']:
                params[key] = value
        return params

    def myopic_policy(self, e: float, h: float):

        if e < self.theta_1:
            # 저배터리 영역
            if h < self.theta_h:
                # R1: 저배터리, 저온 → 발열 제어
                return A2_THERMAL_CONTROL
            else:
                # R2: 저배터리, 고온 → 초절약
                return A1_ULTRA_SAVING
        elif e < self.theta_2:
            # 중배터리 영역
            if h < self.theta_h:
                # R3: 중배터리, 저온 → 균형
                return A3_BALANCED
            else:
                # R4: 중배터리, 고온 → 발열 제어
                return A2_THERMAL_CONTROL
        else:
            # 고배터리 영역
            if h < self.theta_h:
                # R5: 고배터리, 저온 → 최대 성능
                return A6_MAX_PERF
            else:
                # R6: 고배터리, 고온 → 성능
                return A4_PERFORMANCE

    def heuristic_policy(self, e_t: float, h_t: float):
        """휴리스틱 정책 (하위 호환성을 위해 myopic_policy 호출)"""
        r_t, g_t, c_t = self.myopic_policy(e_t, h_t)
        return self.M.build_decision({"r": r_t, "g": g_t, "c": c_t})

    def lookahead_policy_1(self):
        """3단계 내다보기 정책 (myopic 연속 적용)
        
        Q = R0 + gamma * R1 + gamma^2 * R2
        
        Q값이 가장 높은 행동 선택
        """
        current_model = self.M
        gamma = current_model.gamma
        
        best_action = None
        best_Q = -np.inf
        
        for candidate_action in DISCRETE_ACTIONS:
            # 시뮬레이션용 모델 딥카피
            sim_model = deepcopy(current_model)
            
            # 단계 0: 후보 행동 적용
            r0, g0, c0 = candidate_action
            decision_0 = sim_model.build_decision({"r": r0, "g": g0, "c": c0})
            sim_model.step(decision_0)
            
            # R0 획득 (히스토리 마지막 항목)
            R0 = sim_model.history[-1]['reward']
            e1, h1 = sim_model.state.e, sim_model.state.h
            
            # t+1: (e1, h1) 기반 myopic 정책 적용
            r1, g1, c1 = self.myopic_policy(e1, h1)
            decision_1 = sim_model.build_decision({"r": r1, "g": g1, "c": c1})
            sim_model.step(decision_1)
            
            # t+1 시점 보상 획득
            R1 = sim_model.history[-1]['reward']
            e2, h2 = sim_model.state.e, sim_model.state.h
            
            # t+2: (e2, h2) 기반 myopic 정책 적용
            r2, g2, c2 = self.myopic_policy(e2, h2)
            decision_2 = sim_model.build_decision({"r": r2, "g": g2, "c": c2})
            sim_model.step(decision_2)
            
            # t+2 시점 보상 획득
            R2 = sim_model.history[-1]['reward']
            
            # Q값 계산
            Q = R0 + gamma * R1 + (gamma ** 2) * R2
            
            if Q > best_Q:
                best_Q = Q
                best_action = candidate_action
        
        r_t, g_t, c_t = best_action
        return self.M.build_decision({"r": r_t, "g": g_t, "c": c_t})

    def get_decision(self):

        e_t, h_t = self.M.state.e, self.M.state.h
        
        if self.policy_type in ['heuristic', 'myopic']:
            return self.heuristic_policy(e_t, h_t)
        elif self.policy_type == 'lookahead_1':
            return self.lookahead_policy_1()
        else:
            raise ValueError(f"Unknown policy_type: {self.policy_type}")


# ===============================
# AdaptiveThetaPolicy
# ===============================

class AdaptiveThetaPolicy:
    """Episode 종료 후 Gradient Ascent로 θ를 학습하는 정책"""
    
    def __init__(self, model, policy_type='myopic',
                 theta_1=None, theta_2=None, theta_h=None,
                 num_mc=20, max_iters=20, c_step=0.5, eps_grad=1e-2,
                 learn_seed_base=5000, user_type=None):
        
        self.M = model
        self.policy_type = policy_type
        self.user_type = user_type or USER_TYPE
        
        # θ 초기화
        self.theta_1 = theta_1 if theta_1 is not None else DEFAULT_THETA_1
        self.theta_2 = theta_2 if theta_2 is not None else DEFAULT_THETA_2
        self.theta_h = theta_h if theta_h is not None else DEFAULT_THETA_H
        
        # 학습 하이퍼파라미터
        self.num_mc = num_mc
        self.max_iters = max_iters
        self.c_step = c_step
        self.eps_grad = eps_grad
        self.learn_seed_base = learn_seed_base
        
        # 학습 기록
        self.theta_history = []
        self.J_history = []
        self.best_theta = None
        self.best_J = -float('inf')
    
    def _create_model_and_policy(self, theta, seed):
        """주어진 θ와 시드로 새로운 model/policy 생성"""
        model = SmartphoneModel(
            state_names=STATE_NAMES,
            x_names=DECISION_NAMES,
            s_0=INIT_STATE,
            T=HORIZON_T,
            reward_type=REWARD_TYPE,
            seed=seed,
            user_type=self.user_type,
        )
        policy = BasePolicy(
            model,
            policy_type=self.policy_type,
            theta_1=theta[0],
            theta_2=theta[1],
            theta_h=theta[2],
        )
        return model, policy
    
    def _evaluate_J(self, theta, seed_base):
        """Monte-Carlo로 J(θ) 평가"""
        J_values = []
        for i in range(self.num_mc):
            seed = seed_base + i
            _, policy = self._create_model_and_policy(theta, seed)
            total_return, _ = policy.run_policy()
            J_values.append(total_return)
        return sum(J_values) / len(J_values)
    
    def _clip_theta(self, theta):
        """θ를 [0,1] 범위로 클립하고 θ₁ < θ₂ 유지"""
        t1, t2, th = theta
        t1 = np.clip(t1, 0.0, 1.0)
        t2 = np.clip(t2, 0.0, 1.0)
        th = np.clip(th, 0.0, 1.0)
        
        # θ₁ < θ₂ 유지
        if t1 >= t2:
            mid = (t1 + t2) / 2
            t1 = mid - 0.01
            t2 = mid + 0.01
            t1 = np.clip(t1, 0.0, 0.98)
            t2 = np.clip(t2, 0.02, 1.0)
        
        return (t1, t2, th)
    
    def _estimate_gradient(self, theta, k):
        """Finite Difference로 gradient 추정"""
        seed_base = self.learn_seed_base + k * self.num_mc * 10
        
        J_theta = self._evaluate_J(theta, seed_base)
        grad = [0.0, 0.0, 0.0]
        
        for i in range(3):
            # θ + ε * e_i
            theta_plus = list(theta)
            theta_plus[i] += self.eps_grad
            theta_plus = self._clip_theta(tuple(theta_plus))
            
            J_plus = self._evaluate_J(theta_plus, seed_base)
            
            # ∂J/∂θ_i ≈ (J(θ + ε e_i) − J(θ)) / ε
            grad[i] = (J_plus - J_theta) / self.eps_grad
        
        return grad, J_theta
    
    def learn_theta(self, verbose=True):
        """Gradient Ascent로 θ 학습"""
        theta = (self.theta_1, self.theta_2, self.theta_h)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"AdaptiveThetaPolicy 학습 시작")
            print(f"{'='*60}")
            print(f"Policy Type: {self.policy_type}")
            print(f"Initial θ: ({theta[0]:.3f}, {theta[1]:.3f}, {theta[2]:.3f})")
            print(f"MC episodes: {self.num_mc}, Max iters: {self.max_iters}")
            print(f"c_step: {self.c_step}, eps_grad: {self.eps_grad}")
            print(f"{'='*60}\n")
        
        self.theta_history = [theta]
        
        for k in range(1, self.max_iters + 1):
            # Step size (harmonic)
            alpha_k = self.c_step / k
            
            # Gradient 추정
            grad, J_theta = self._estimate_gradient(theta, k)
            
            self.J_history.append(J_theta)
            
            # Best 갱신
            if J_theta > self.best_J:
                self.best_J = J_theta
                self.best_theta = theta
            
            if verbose:
                print(f"[Iter {k:3d}] θ=({theta[0]:.3f}, {theta[1]:.3f}, {theta[2]:.3f}) | "
                      f"J(θ)={J_theta:.4f} | α={alpha_k:.4f} | "
                      f"∇J=({grad[0]:.3f}, {grad[1]:.3f}, {grad[2]:.3f})")
            
            # Gradient Ascent Update
            theta_new = (
                theta[0] + alpha_k * grad[0],
                theta[1] + alpha_k * grad[1],
                theta[2] + alpha_k * grad[2],
            )
            theta = self._clip_theta(theta_new)
            self.theta_history.append(theta)
        
        # 최종 θ 적용
        self.theta_1, self.theta_2, self.theta_h = self.best_theta
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"학습 완료!")
            print(f"{'='*60}")
            print(f"Best θ: ({self.best_theta[0]:.3f}, {self.best_theta[1]:.3f}, {self.best_theta[2]:.3f})")
            print(f"Best J(θ): {self.best_J:.4f}")
            print(f"{'='*60}\n")
        
        return self.best_theta, self.best_J
    
    def run_policy(self):
        """학습된 θ로 한 episode 실행"""
        theta = (self.theta_1, self.theta_2, self.theta_h)
        _, policy = self._create_model_and_policy(theta, seed=42)
        return policy.run_policy()
    
    def get_learned_policy(self, seed=42):
        """학습된 θ로 BasePolicy 반환"""
        theta = (self.theta_1, self.theta_2, self.theta_h)
        _, policy = self._create_model_and_policy(theta, seed)
        return policy
