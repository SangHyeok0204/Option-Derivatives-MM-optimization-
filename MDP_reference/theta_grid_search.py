"""
Theta Grid Search - myopic 정책의 최적 임계값 탐색
"""

from copy import copy
import numpy as np
from BaseModel import SmartphoneModel, USER_TYPE, GAMMA, USER_PARAMS
from BasePolicy import BasePolicy, POLICY_TYPE


# Grid 정의
THETA1_GRID = [0.20, 0.30, 0.40]
THETA2_GRID = [0.60, 0.70, 0.80]
THETAH_GRID = [0.45, 0.55, 0.65]

# BaseDriverScript.py와 동일한 설정
STATE_NAMES = ['e', 'h']
DECISION_NAMES = ['r', 'g', 'c']
INIT_STATE = {'e': 1.0, 'h': 0.3}
T = 18
REWARD_TYPE = 'Cumulative'


def create_model_and_policy(theta, policy_type=None, user_type=None, seed=None):
    """theta와 시드로 model/policy 생성"""
    theta_1, theta_2, theta_h = theta
    
    model = SmartphoneModel(
        state_names=STATE_NAMES,
        x_names=DECISION_NAMES,
        s_0=INIT_STATE,
        T=T,
        reward_type=REWARD_TYPE,
        seed=seed if seed is not None else 42,
        user_type=user_type or USER_TYPE,
    )
    
    policy = BasePolicy(
        model,
        policy_type=policy_type or POLICY_TYPE,
        theta_1=theta_1,
        theta_2=theta_2,
        theta_h=theta_h,
    )
    
    return model, policy


def evaluate_theta(theta, policy_type=None, user_type=None, 
                   num_trials=50, seed_base=1000):
    """Monte Carlo로 J(theta) 평가"""
    J_values = []
    
    for trial_index in range(num_trials):
        seed = seed_base + trial_index
        model, policy = create_model_and_policy(
            theta, 
            policy_type=policy_type, 
            user_type=user_type, 
            seed=seed
        )
        total_return, history = policy.run_policy()
        J_values.append(total_return)
    
    avg_return = sum(J_values) / len(J_values)
    return avg_return, J_values


def grid_search_theta(policy_type=None, user_type=None, 
                      num_trials=50, seed_base=1000, verbose=True):
    """Grid search로 최적 theta 탐색"""
    results = []
    best_theta = None
    best_value = -float("inf")
    
    # 전체 조합 수
    total_combinations = 0
    for theta_1 in THETA1_GRID:
        for theta_2 in THETA2_GRID:
            if theta_1 < theta_2:
                total_combinations += len(THETAH_GRID)
    
    current = 0
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Grid Search 시작")
        print(f"{'='*60}")
        print(f"Policy: {policy_type or POLICY_TYPE}")
        print(f"User Type: {user_type or USER_TYPE}")
        print(f"Trials per theta: {num_trials}")
        print(f"Total combinations: {total_combinations}")
        print(f"{'='*60}\n")
    
    for theta_1 in THETA1_GRID:
        for theta_2 in THETA2_GRID:
            if theta_1 >= theta_2:
                continue
            
            for theta_h in THETAH_GRID:
                theta = (theta_1, theta_2, theta_h)
                current += 1
                
                if verbose:
                    print(f"[{current}/{total_combinations}] "
                          f"θ = ({theta_1:.2f}, {theta_2:.2f}, {theta_h:.2f}) ... ", 
                          end="", flush=True)
                
                avg_return, _ = evaluate_theta(
                    theta,
                    policy_type=policy_type,
                    user_type=user_type,
                    num_trials=num_trials,
                    seed_base=seed_base
                )
                
                result = {"theta": theta, "J": avg_return}
                results.append(result)
                
                if verbose:
                    print(f"J(θ) = {avg_return:.4f}")
                
                if avg_return > best_value:
                    best_value = avg_return
                    best_theta = theta
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Grid Search 완료!")
        print(f"{'='*60}")
    
    return best_theta, results


def print_results_table(results, best_theta):
    """결과 테이블 출력"""
    print(f"\n{'='*70}")
    print(f"{'θ_1':>8} | {'θ_2':>8} | {'θ_h':>8} | {'J(θ)':>12} | {'Best':>6}")
    print(f"{'-'*70}")
    
    sorted_results = sorted(results, key=lambda x: x["J"], reverse=True)
    
    for r in sorted_results:
        theta = r["theta"]
        is_best = "  ★" if theta == best_theta else ""
        print(f"{theta[0]:>8.2f} | {theta[1]:>8.2f} | {theta[2]:>8.2f} | "
              f"{r['J']:>12.4f} |{is_best}")
    
    print(f"{'='*70}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Theta Grid Search for MDP Policy")
    parser.add_argument("--policy", type=str, default=None)
    parser.add_argument("--user", type=str, default=None)
    parser.add_argument("--trials", type=int, default=50)
    parser.add_argument("--seed", type=int, default=1000)
    args = parser.parse_args()
    
    best_theta, results = grid_search_theta(
        policy_type=args.policy,
        user_type=args.user,
        num_trials=args.trials,
        seed_base=args.seed,
        verbose=True
    )
    
    print_results_table(results, best_theta)
    
    print(f"\n★ Best theta: ({best_theta[0]:.2f}, {best_theta[1]:.2f}, {best_theta[2]:.2f})")
    print(f"★ Best J(θ):  {max(r['J'] for r in results):.4f}")
    
    # Sensitivity Analysis
    print(f"\n{'='*60}")
    print("Sensitivity Analysis")
    print(f"{'='*60}")
    
    for t1 in THETA1_GRID:
        subset = [r for r in results if r["theta"][0] == t1]
        if subset:
            avg = np.mean([r["J"] for r in subset])
            print(f"  θ_1 = {t1:.2f}: avg J = {avg:.4f}")
    
    
    for t2 in THETA2_GRID:
        subset = [r for r in results if r["theta"][1] == t2]
        if subset:
            avg = np.mean([r["J"] for r in subset])
            print(f"  θ_2 = {t2:.2f}: avg J = {avg:.4f}")
    
    
    for th in THETAH_GRID:
        subset = [r for r in results if r["theta"][2] == th]
        if subset:
            avg = np.mean([r["J"] for r in subset])
            print(f"  θ_h = {th:.2f}: avg J = {avg:.4f}")
