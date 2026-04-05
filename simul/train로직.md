Train 모드 설명

이 문서는 train.ipynb의 설계 논리와 구현 구조를 설명한다.
프로젝트의 전체 철학은 프로젝트가이드.md에서 다루며, 이 문서에서는 다루지 않는다.
Develop 모드의 기반 로직은 develop모드.md에서 다루며, 이 문서에서는 다루지 않는다.


1. Train 모드의 목적

Develop 모드에서 확인된 두 가지 문제를 해결하기 위해 RL 기반으로 동적 변동성 파라미터를 학습한다.

첫째, sigma^2 * (T-t) 구조의 한계이다. sigma가 상수이고 (T-t)가 0으로 수렴하면서 장 마감 직전에 재고 관리 능력이 소멸한다.
둘째, 고정 sigma로는 시장 변동성의 동적 변화를 반영하지 못한다.

학습된 파라미터는 optimize.ipynb에서 실제 데이터로 검증한다.


2. 핵심 수식 변경

2-1. 기존 A-S 수식

RP = s - q_delta * gamma * sigma^2 * (T - t)
spread = gamma * sigma^2 * (T - t) + (2 / gamma) * ln(1 + gamma / k)

sigma^2 * (T - t) 항은 A-S의 최적 제어 해에서 sigma가 상수일 때 도출된다.
이 항의 의미는 t 시점부터 T 시점까지 남은 총 분산이다.
sigma가 상수이면 남은 총 분산은 sigma^2 * (T - t)로 닫힌다.

2-2. 변경된 수식

RP = s - q_delta * gamma * sigma_new^2
spread = gamma * sigma_new^2 + (2 / gamma) * ln(1 + gamma / k)

sigma_new^2는 GARCH(1,1)가 산출하는 조건부 분산이다.
(T - t) 항을 제거하고 sigma_new^2로 대체한다.

2-3. (T - t) 제거의 정당성

sigma^2 * (T - t)는 sigma가 상수일 때만 성립한다.
sigma가 동적이면 남은 총 분산은 E[integral_t^T sigma_s^2 ds]이며 닫힌 해가 없다.
따라서 RL로 최적 sigma_new^2를 결정하는 구조로 전환한다.

경제학적 해석도 변경된다.
기존은 만기까지 남은 총 리스크를 고려한 최적 호가(finite horizon 최적화)이다.
변경 후는 현재 변동성 상태에 반응하는 적응적 호가(myopic 최적화)이다.
장중 MM의 시간지평은 하루이며 장 마감 직전에도 가격 변동은 지속되므로
현재 시장의 변동성 상태가 리스크를 결정한다는 가정이 더 현실적이다.


3. GARCH(1,1) 변동성 모델

3-1. 수식

sigma_t^2 = (1 - alpha_t - beta_t) * V_L + alpha_t * r_{t-1}^2 + beta_t * sigma_{t-1}^2

각 항의 의미는 다음과 같다.
(1 - alpha_t - beta_t) * V_L은 장기평균 분산으로의 회귀 항이다.
alpha_t * r_{t-1}^2은 직전 충격 반영 항이다. alpha가 클수록 직전 가격 변동에 민감하게 반응한다.
beta_t * sigma_{t-1}^2은 직전 분산의 관성 항이다. beta가 클수록 이전 변동성을 유지한다.

3-2. 파라미터 설정

V_L은 장기평균 분산이며 4.0으로 설정한다.
develop 모드에서 sigma^2 * (T-t)가 t=0일 때 4.0이므로, (T-t) 제거 후에도 동등한 조정력을 유지하기 위해 이 값을 사용한다.

alpha_t + beta_t = 0.97로 고정한다.
alpha_t는 0.03(최소)에서 0.15(최대) 범위에서 연속적으로 변한다.
beta_t = 0.97 - alpha_t이다.

alpha_t가 최소(0.03)이면 sigma^2는 V_L 근처에서 안정적으로 유지된다.
alpha_t가 최대(0.15)이면 sigma^2가 직전 충격에 강하게 반응하여 빠르게 변동한다.

r_{t-1}은 주가의 절대 변화량(S_t - S_{t-1})이다.
퍼센트 수익률이 아닌 절대 변화량을 사용하는 이유는 V_L = 4.0과 스케일을 맞추기 위함이다.
sigma_stock = 10, dt = 0.005일 때 1 step 절대 변화량은 약 0.71이며, r^2 약 0.50은 V_L(4.0) 대비 의미 있는 크기이다.

3-3. 학습용 가격 경로 생성

학습 환경에서 주가 경로 생성 시 sigma_stock = 10.0을 사용한다.
이는 develop 모드와 동일한 주가 변동성이다.
GARCH의 sigma_t^2는 RP/spread 수식에만 사용하고 주가 경로 생성에는 사용하지 않는다.
두 변동성의 역할이 분리된다.

sigma_stock은 주가가 실제로 얼마나 움직이는가를 결정한다.
sigma_t^2(GARCH)는 시장조성자가 인식하는 리스크 수준을 결정한다.

경로 생성 절차는 다음과 같다.
1단계. S_t = S_{t-1} + drift * dt + sigma_stock * sqrt(dt) * Z_t로 주가를 생성한다.
2단계. 주가를 BSM에 입력하여 옵션 이론가와 델타를 도출한다.
3단계. 시뮬레이션 중 매 step에서 GARCH 수식으로 sigma_t^2를 업데이트한다.


4. 동적 alpha 결정: sigmoid 연속 정책

4-1. 이산 threshold 정책의 한계

초기 설계에서는 score를 구간별로 나누어 3개 regime 중 하나를 선택하는 이산 정책을 사용하였다.
이 방식의 문제는 theta를 미세하게 변경해도 대부분의 step에서 regime이 바뀌지 않아 reward(J)가 변하지 않고, gradient가 0이 되어 학습이 진행되지 않는 것이었다.

4-2. sigmoid 연속 정책

이산 threshold 대신 sigmoid 함수를 사용하여 alpha_t를 연속적으로 결정한다.

alpha_t = ALPHA_MIN + (ALPHA_MAX - ALPHA_MIN) * sigmoid((score - theta_3) / theta_4)
beta_t = 0.97 - alpha_t

ALPHA_MIN = 0.03이다.
ALPHA_MAX = 0.15이다.

theta_3은 sigmoid의 중심점이다. score가 이 값일 때 alpha가 (ALPHA_MIN + ALPHA_MAX) / 2 = 0.09가 된다.
theta_4는 sigmoid의 전환 폭이다. 값이 클수록 완만한 전환, 작을수록 급격한 전환이 이루어진다.

이 구조에서 theta를 미세하게 변경하면 모든 step에서 alpha_t가 연속적으로 미세하게 변한다.
따라서 J가 항상 반응하고 gradient가 존재하여 학습이 정상 작동한다.

4-3. score 설계

score는 현재 시장 상태를 하나의 숫자로 요약하여 alpha_t 결정에 사용한다.
score가 높을수록 alpha_t가 높아지고, sigma^2가 충격에 더 민감하게 반응한다.

score에 들어가는 feature는 alpha의 역할과 일치해야 한다.
alpha는 GARCH 수식에서 직전 충격(r^2)에 대한 반응도를 결정한다.
따라서 score는 시장의 변동성 상태나 불안정성을 반영하는 feature로 구성해야 한다.

score에 부적합한 feature는 다음과 같다.

|net_delta|(재고 크기)는 부적합하다.
재고가 클 때 alpha를 올리면 sigma^2가 커지고 spread가 넓어져 체결이 줄어든다.
그런데 RP 수식은 재고가 클 때 bid/ask를 비대칭으로 밀어서 재고 해소 체결을 유도한다.
alpha 상승에 의한 spread 확대가 RP의 재고 해소 메커니즘을 방해한다.
gradient ascent 실험에서도 net_delta의 가중치(theta_1)가 일관되게 하한으로 수렴하여 이를 확인하였다.

|직전수익률| 단독 사용도 주의가 필요하다.
직전수익률이 크면 alpha를 올리고, alpha가 곱해지는 r^2 자체도 크므로 이중 증폭이 발생한다.
과도한 sigma^2 급등으로 이어질 수 있다.

score에 적합한 feature 후보는 다음과 같다.

후보 1. sigma^2_{t-1} / V_L (현재 변동성의 장기 대비 수준)
sigma^2가 V_L보다 높으면 시장이 불안정한 상태이므로 alpha를 올려 더 민감하게 추적한다.
sigma^2가 V_L 근처이면 안정적이므로 alpha를 낮춰 관성을 유지한다.
RP와 충돌하지 않는다.

후보 2. 최근 N step 수익률의 분산 (realized volatility)
단일 수익률이 아닌 최근 구간의 변동성을 사용하므로 이중 증폭 문제가 완화된다.

후보 3. |r_{t-1}| / sqrt(sigma^2_{t-1}) (정규화된 충격 크기)
현재 변동성 수준 대비 충격이 얼마나 큰지를 측정한다.
이 값이 크면 예상을 벗어난 충격이므로 alpha를 올려 빠르게 반영한다.

이 중 어떤 feature를 사용할지, 또는 여러 feature를 조합할지는 실험을 통해 결정한다.


5. 학습 대상과 구조

5-1. 학습 대상 (theta)

theta는 4개이다.
theta_1은 score에서 feature 1의 가중치이다.
theta_2는 score에서 feature 2의 가중치이다. (feature가 1개이면 사용하지 않는다.)
theta_3은 sigmoid의 중심점이다.
theta_4는 sigmoid의 전환 폭이다.

alpha_t와 beta_t의 범위(ALPHA_MIN, ALPHA_MAX)는 고정이며 학습 대상이 아니다.

5-2. 학습 방식: finite difference gradient ascent

MDP reference의 AdaptiveThetaPolicy 패턴을 따른다.

학습의 목표는 reward J(theta)를 최대화하는 theta를 찾는 것이다.
J(theta)는 주어진 theta로 정책을 구성하고 여러 시뮬레이션을 실행하여 평균 reward를 계산한 값이다.

구체적 절차는 다음과 같다.

1단계. 현재 theta의 성적을 측정한다.
theta로 MMPolicy를 구성한다.
num_mc개(50개)의 서로 다른 시장 경로에서 시뮬레이션을 실행한다.
각 경로마다 GARCH로 주가를 생성하고, BSM으로 옵션가를 도출하고, 200 step 동안 매 step policy로 alpha_t를 결정하고, 체결과 재고를 시뮬레이션한다.
50개 episode의 reward 평균이 J(theta)이다.

2단계. theta를 하나씩 살짝 바꿔서 gradient를 추정한다.
theta_i를 eps_i만큼 올린 상태에서 같은 50개 경로(같은 seed)로 J를 다시 측정한다.
eps_i는 theta_i 크기에 비례한다(상대적 perturbation). eps_i = eps_frac * max(|theta_i|, 0.5)이다.
gradient_i = (J(theta_i + eps_i) - J(theta)) / eps_i이다.
4개 theta에 대해 반복하므로 총 5회의 J 평가(기본 1회 + perturbation 4회)가 필요하다.

3단계. gradient 방향으로 theta를 업데이트한다.
theta_i += lr_k * gradient_i * scale_i이다.
lr_k는 harmonic rule을 따른다. lr_k = c_lr / k이다. k는 iteration 번호이다.
scale_i는 theta_i 크기에 비례한다. scale_i = max(|theta_i|, 0.5)이다.
상대적 업데이트를 통해 theta 크기가 다른 파라미터 간 업데이트 균형을 맞춘다.

4단계. clip을 적용한다.
각 theta가 허용 범위를 벗어나지 않도록 clip한다.

5단계. 100회 반복한다.
매 iteration마다 best theta를 기록하고, 학습 종료 후 best theta를 반환한다.

5-3. 상대적 perturbation과 업데이트를 사용하는 이유

고정 eps(예: 0.05)를 모든 theta에 동일하게 적용하면 theta 크기에 따라 gradient 스케일이 달라진다.
theta_i = 0.1인데 eps = 0.05이면 50% 변동이 되어 gradient가 폭발한다.
theta_i = 10.0인데 eps = 0.05이면 0.5% 변동이 되어 gradient가 미미하다.
상대적 eps를 사용하면 모든 theta가 자기 크기의 동일 비율만큼 변동하여 gradient 스케일이 균일해진다.
업데이트 시에도 theta 크기에 비례하여 이동량을 조절한다.

5-4. Reward 함수

J = 최종 P&L - lambda_inv * max_t(|inventory_t|)

최종 P&L은 cash + inventory * 최종 옵션가이다.
lambda_inv는 재고 벌점 강도이며 0.5로 설정한다.
max_t(|inventory_t|)는 시뮬레이션 중 재고 절대값의 최대치이다.
재고가 크게 쌓이는 경로에 벌점을 부여하여 재고 관리를 유도한다.

5-5. drift 설정

drift는 사용자가 코드에서 수동으로 설정한다.
특정 drift에서 최적 theta가 얼마인지를 확인하는 구조이다.
여러 drift 값에 대해 각각 학습을 실행하여 비교한다.
이를 통해 추세 강도에 따라 최적 변동성 전략이 어떻게 달라지는지 정량적으로 확인할 수 있다.


6. Develop 모드에서 계승하는 요소

BSM으로 옵션 이론가와 델타를 도출하는 구조를 계승한다.
재고 정의는 Net Delta(inventory * delta_t)를 사용한다.
체결 로직은 다단계 호가, bucket 승수, 1-step lag, sweep 보정을 모두 유지한다.
tick size 반올림을 유지한다.
P&L 계산 방식을 유지한다.


7. 파일 간 관계

develop.ipynb는 문제를 보여준다. A-S 확장 시 추세장에서 재고 관리가 실패함을 확인한다.
train.ipynb는 문제를 해결한다. RL로 동적 변동성 파라미터를 학습한다.
optimize.ipynb는 해결을 검증한다. 실제 데이터에서 학습된 정책의 성능을 확인한다.


8. 구현 위치

train.ipynb에서 다음 부분을 참조한다.

TrainConfig 클래스에서 A-S 파라미터, GARCH 파라미터, RL 파라미터를 정의한다.
GarchPathGenerator 클래스에서 sigma_stock 기반 주가 경로를 생성한다.
MMEnvironment 클래스에서 MDP 환경(state, transition, reward)을 정의하며 step_continuous 메서드에서 alpha_t, beta_t를 직접 받아 GARCH를 업데이트한다.
MMPolicy 클래스에서 sigmoid 기반 연속 정책으로 alpha_t를 결정한다.
AdaptiveRLPolicy 클래스에서 상대적 eps gradient ascent로 theta를 학습한다.


Last Updated: 2026-04-06 (sigmoid 연속 정책 전환, score feature 재설계 논의, 상대적 eps/업데이트, r_t 스케일 수정)
