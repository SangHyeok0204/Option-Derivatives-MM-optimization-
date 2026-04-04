Paper 모드 설명

이 문서는 Avellaneda-Stoikov 논문을 그대로 재현한 Paper 모드의 설정과 수식을 설명한다.
프로젝트의 전체 철학은 프로젝트가이드.md에서 다루며, 이 문서에서는 다루지 않는다.
Develop 모드의 확장 내용은 develop모드.md에서 다루며, 이 문서에서는 다루지 않는다.


1. Paper 모드의 목적

논문의 설정과 수식을 그대로 구현하여, 원논문이 제시한 조건에서의 결과를 재현한다.
이를 통해 논문의 이론적 결과를 검증하고, Develop 모드와의 비교 기준점을 확보한다.


2. 시뮬레이션 환경 설정

논문에서 제시한 기본 파라미터를 따른다.

초기 중간가격 S0은 100이다.
시뮬레이션 총 시간 T는 1로 정규화한다.
변동성 sigma는 2이다.
추세 파라미터 drift는 기본값 0이며, 시뮬레이션 시 15로 설정하여 사용한다.
시간 간격 dt는 0.005이다.
총 스텝 수 n_steps는 200이다.
위험 회피 계수 gamma는 0.1이다.
체결 강도 A는 140이다.
체결 강도 감쇠율 k는 1.5이다.


3. 중간가격 동학

중간가격은 drift가 포함된 Brownian motion을 따른다.
dS = drift * dt + sigma * dW

원논문에서는 drift = 0인 순수 Brownian motion을 가정한다.
본 시뮬레이션에서는 추세가 있는 시장에서의 재고 리스크를 보여주기 위해 drift를 추가하였다.
drift가 양수이면 가격이 상승 추세를 가지며, 이로 인해 한쪽 방향으로 재고가 쌓이는 문제를 관찰할 수 있다.

이산화하면 다음과 같다.
S(t+dt) = S(t) + drift * dt + sigma * sqrt(dt) * Z
여기서 Z는 표준정규분포를 따르는 난수다.

구현에서는 np.random.randn을 사용하여 난수를 생성하고, drift * dt + sigma * sqrt(dt) * Z로 증분을 계산한 후 누적합으로 경로를 생성한다.


4. Reservation Price

논문 식 (29)에 따른 Reservation Price 계산이다.

r = s - q * gamma * sigma^2 * (T - t)

각 변수의 의미는 다음과 같다.
s는 현재 중간가격이다.
q는 현재 재고(계약 수)이다. 양수이면 롱, 음수이면 숏이다.
gamma는 위험 회피 계수이다.
sigma는 변동성이다.
(T - t)는 잔여 시간이다.

해석하면 다음과 같다.
재고가 양수(롱)이면 기준가격을 중간가격보다 낮게 설정한다. 매도를 유도하여 재고를 줄이려는 것이다.
재고가 음수(숏)이면 기준가격을 중간가격보다 높게 설정한다. 매수를 유도하여 재고를 늘리려는 것이다.

gamma * sigma^2 * (T - t) 부분이 재고 1단위당 기준가격 조정 폭이다.
gamma가 클수록 재고에 민감하게 반응한다.
sigma가 클수록 변동성 리스크가 크므로 더 크게 조정한다.
잔여 시간이 길수록 리스크 노출 기간이 길으므로 더 크게 조정한다.


5. Optimal Spread

논문 식 (30)에 따른 최적 스프레드 계산이다.

spread = gamma * sigma^2 * (T - t) + (2 / gamma) * ln(1 + gamma / k)

첫 번째 항 gamma * sigma^2 * (T - t)는 재고 리스크 보상이다.
변동성과 잔여 시간에 비례하여 스프레드를 넓힌다.

두 번째 항 (2 / gamma) * ln(1 + gamma / k)는 체결확률 보정이다.
체결 강도 감쇠율 k를 반영한다.
gamma가 작을수록 이 항이 커진다.

최종 호가는 다음과 같이 배치한다.
bid = r - spread / 2
ask = r + spread / 2

여기서 r은 Reservation Price다.


6. 체결 확률

논문 식 (12)에 따른 포아송 프로세스 기반 체결 확률 계산이다.

체결 강도 lambda는 다음과 같다.
lambda(delta) = A * exp(-k * delta)

delta는 호가와 중간가격 사이의 거리다.
bid의 경우 delta_bid = mid_price - bid_price이다.
ask의 경우 delta_ask = ask_price - mid_price이다.

체결 확률은 다음과 같다.
P(fill) = lambda(delta) * dt

호가가 중간가격에 가까울수록(delta가 작을수록) 체결 강도가 높아지고, 체결 확률이 높아진다.
A는 기본 체결 강도를 결정한다.
k는 호가 거리에 따른 체결 강도 감소 속도를 결정한다.


7. 재고 관리

Paper 모드에서 재고는 계약 수로 정의한다.
옵션 델타는 1로 고정한다. 기초자산을 직접 거래하는 상황을 가정하기 때문이다.

체결 시 재고 변화는 다음과 같다.
bid 체결 시 재고가 1 증가한다. 매수이므로 롱 포지션이 늘어난다.
ask 체결 시 재고가 1 감소한다. 매도이므로 롱 포지션이 줄어든다.


8. P&L 계산

Realized P&L은 체결된 거래에서 발생한 손익이다.
bid 체결 시 현금이 bid_price만큼 감소한다.
ask 체결 시 현금이 ask_price만큼 증가한다.

Mark-to-Market P&L은 미실현 손익이다.
현재 재고에 현재 중간가격을 곱한 값이다.

Total P&L은 Realized P&L과 Mark-to-Market P&L의 합이다.


9. 구현 위치

paper.ipynb 파일에서 다음 부분을 참조한다.

PaperConfig 클래스에서 Paper 모드의 파라미터를 정의한다.
S0, T, sigma, drift, dt, n_steps, gamma, A, k, q0 파라미터가 사용된다.

generate_mid_price_path 함수에서 drift가 포함된 Brownian motion 경로를 생성한다.

compute_reservation_price 함수에서 논문 식 (29)의 Reservation Price를 계산한다.
compute_optimal_spread 함수에서 논문 식 (30)의 최적 스프레드를 계산한다.
compute_fill_probability 함수에서 논문 식 (12)의 체결 확률을 계산한다.
run_simulation 함수에서 단일 시뮬레이션을 실행한다.
run_symmetric_simulation 함수에서 대칭 호가 전략 시뮬레이션을 실행한다.


10. Paper 모드의 한계

Paper 모드는 다음을 가정한다.
기초자산을 직접 거래한다. 델타가 항상 1이다.
변동성이 고정되어 있다.
T는 옵션 만기까지의 시간이다.
gamma는 상수다.

이러한 가정은 옵션 Market Making의 현실과 맞지 않는다.
이를 보완한 것이 Develop 모드이며, 상세 내용은 develop모드.md에서 다룬다.


Last Updated: 2026-03-30
