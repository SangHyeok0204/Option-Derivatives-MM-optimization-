"""스마트폰 MDP 실험 스크립트"""

import numpy as np
import matplotlib.pyplot as plt
from BaseModel import SmartphoneModel, GAMMA, USER_TYPE, USER_PARAMS
from BasePolicy import BasePolicy, AdaptiveThetaPolicy, POLICY_TYPE


def main():
    # 상태: e(배터리), h(온도) / 행동: r(주사율), g(GPU), c(화면밝기)
    state_names = ['e', 'h']
    decision_names = ['r', 'g', 'c']
    init_state = {'e': 1.0, 'h': 0.3}  # 배터리 100%, 온도 30%로 시작
    T = 18                              # 하루를 18스텝으로 나눔
    trial_size = 100                    # MC 시뮬레이션 횟수
    reward_type = 'Cumulative'          # 누적 할인 보상 사용

    params = USER_PARAMS[USER_TYPE]
    print(f"\n실험 설정: T={T}, trials={trial_size}, user={USER_TYPE}, policy={POLICY_TYPE}")
    print(f"분포: b~N({params['b_mean']},{params['b_std']}), x~U({params['x_min']},{params['x_max']}), p_wifi={params['p_wifi']}")

    model = SmartphoneModel(state_names, decision_names, init_state, T, reward_type, seed=42)
    
    if POLICY_TYPE == 'adaptive_theta':
        # θ를 gradient ascent로 학습하는 정책
        adaptive_policy = AdaptiveThetaPolicy(
            model,
            policy_type='myopic',   # 내부에서 쓸 정책 (myopic or lookahead_1)
            theta_1=0.40,           # 저배터리 임계값 초기값
            theta_2=0.70,           # 고배터리 임계값 초기값
            theta_h=0.45,           # 고온 임계값 초기값
            num_mc=20,              # J(θ) 평가할 때 MC 횟수
            max_iters=20,           # gradient ascent 반복 횟수
            c_step=0.005,           # step size α_k = c/k
            eps_grad=1e-2,          # finite difference용 ε
            learn_seed_base=5000,
            user_type=USER_TYPE,
        )
        adaptive_policy.learn_theta(verbose=True)
        policy = adaptive_policy.get_learned_policy(seed=42)
        print(f"학습된 θ: ({adaptive_policy.theta_1:.3f}, {adaptive_policy.theta_2:.3f}, {adaptive_policy.theta_h:.3f})")
    else:
        policy = BasePolicy(model)  # myopic, lookahead_1 등

    # MC 시뮬레이션 돌림
    returns, final_batteries, final_heats = [], [], []
    best_reward, best_history, best_iteration = -np.inf, None, 0

    for trial in range(trial_size):
        total_reward, history = policy.run_policy()  # 한 episode 실행
        returns.append(total_reward)
        if history:
            final_batteries.append(history[-1]['state'].e)  # 마지막 배터리
            final_heats.append(history[-1]['state'].h)      # 마지막 온도
        if total_reward > best_reward:
            best_reward, best_history, best_iteration = total_reward, history, trial + 1
        print(f" iteration: {trial+1}: 보상={total_reward:.2f}")

    # 결과 출력
    returns = np.array(returns)
    print(f"\n결과 ({USER_TYPE}): 평균={np.mean(returns):.2f}, std={np.std(returns):.2f}")
    print(f"최종 배터리: {np.mean(final_batteries)*100:.1f}%, 온도: {np.mean(final_heats)*100:.1f}%")
    print(f"최고 보상 iteration: {best_iteration}, 보상={best_reward:.2f}")

    # 최고 episode의 행동 경로 출력
    print(f"\n[Best Iteration {best_iteration}] Decision Trajectory:")
    print(f"{'t':>3} | {'e':>6} | {'h':>6} | {'r':>3} | {'g'} | {'c':>5} | {'reward':>7}")
    print("-" * 50)
    for rec in best_history:
        s, d = rec['state'], rec['decision']
        print(f"{rec['t']:3} | {s.e*100:5.1f}% | {s.h*100:5.1f}% | {d.r:3} | {d.g} | {d.c:.3f} | {rec['reward']:7.3f}")

    # 플롯 1: iteration별 누적 보상
    iterations = np.arange(1, trial_size + 1)
    plt.figure(figsize=(10, 6))
    plt.plot(iterations, returns, marker='o', markersize=4, linewidth=1, color='steelblue', alpha=0.8)
    plt.axhline(y=np.mean(returns), color='red', linestyle='--', linewidth=2, label=f'평균: {np.mean(returns):.2f}')
    plt.axhline(y=best_reward, color='green', linestyle='--', linewidth=2, label=f'최고: {best_reward:.2f} (iter {best_iteration})')
    plt.xlabel('Iteration', fontsize=12)
    plt.ylabel('Cumulative Reward', fontsize=12)
    plt.title(f'Cumulative Reward per Iteration\n(Policy: {POLICY_TYPE}, User: {USER_TYPE}, T={T})', fontsize=14)
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    # 플롯 2: 최고 episode의 시점별 보상 경로
    t_values = [rec['t'] for rec in best_history]
    reward_values = [rec['reward'] for rec in best_history]
    plt.figure(figsize=(10, 6))
    plt.plot(t_values, reward_values, marker='s', markersize=6, linewidth=2, color='darkorange', alpha=0.9)
    plt.xlabel('t', fontsize=12)
    plt.ylabel('Reward', fontsize=12)
    plt.title(f'Reward Trajectory of Best Iteration (iter {best_iteration})\nCumulative Reward: {best_reward:.2f}', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(t_values)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
