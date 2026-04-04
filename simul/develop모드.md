Develop 모드 설명

이 문서는 A-S 논문을 확장한 Develop 모드의 설정과 변경점을 설명한다.
프로젝트의 전체 철학은 프로젝트가이드.md에서 다루며, 이 문서에서는 다루지 않는다.
Paper 모드의 원본 설정은 paper모드.md에서 다루며, 이 문서에서는 다루지 않는다.


1. Develop 모드의 목적

A-S 논문의 이론적 프레임워크를 유지하면서 시장조성의 현실적 특성을 반영한다.
Paper 모드에서 확인된 한계를 보완하여 보다 현실적인 시뮬레이션을 수행한다.


2. Paper 모드와의 핵심 차이 요약

가격 데이터는 동일하다.
Paper 모드와 동일하게 GBM으로 생성한 가상 가격을 사용한다.
drift를 포함한 Brownian motion으로 추세가 있는 시장을 모델링한다.

재고 정의는 동일하다.
Paper 모드와 동일하게 계약 수 q를 사용한다.

변동성 파라미터는 동일하다.
Paper 모드와 동일하게 고정 sigma = 2.0을 사용한다.

시간 설정은 동일하다.
Paper 모드와 동일하게 T = 1, dt = 0.005, n_steps = 200을 사용한다.

Develop 모드에서 추가된 기능은 다음과 같다.
다단계 호가(multi-level quoting)가 있다.
Tick size 반올림이 있다.
즉시 체결 조건(delta <= 0)과 mid price 체결이 있다.
방향성 기반 체결 확률 조정(bucket 승수)이 있다.


3. 시뮬레이션 환경 설정

Paper 모드와 동일한 파라미터를 따르며, 추가 파라미터가 있다.

초기 중간가격 S0은 100이다.
시뮬레이션 총 시간 T는 1로 정규화한다.
변동성 sigma는 2이다.
추세 파라미터 drift는 기본값 0이며, 시뮬레이션 시 15로 설정하여 사용한다.
시간 간격 dt는 0.005이다.
총 스텝 수 n_steps는 200이다.
위험 회피 계수 gamma는 0.1이다.
체결 강도 A는 140이다.
체결 강도 감쇠율 k는 1.5이다.
호가 단계 수 n_levels는 3이다.
틱 사이즈 tick_size는 0.05이다.

drift를 일부러 15로 설정하는 이유는 추세가 있는 시장에서 재고가 한쪽 방향으로 쌓이는 문제를 관찰하기 위함이다.
drift = 0이면 재고 관리가 잘 되지만, drift = 15이면 재고 관리의 어려움이 드러난다.


4. 중간가격 동학

Paper 모드와 동일하게 drift가 포함된 Brownian motion을 따른다.
dS = drift * dt + sigma * dW

이산화하면 다음과 같다.
S(t+dt) = S(t) + drift * dt + sigma * sqrt(dt) * Z
여기서 Z는 표준정규분포를 따르는 난수다.


5. Reservation Price와 Spread

Paper 모드와 동일한 수식을 사용한다.

Reservation Price는 다음과 같다.
r = s - q * gamma * sigma^2 * (T - t)

Optimal Spread는 다음과 같다.
spread = gamma * sigma^2 * (T - t) + (2 / gamma) * ln(1 + gamma / k)


6. Tick Size 반올림

실제 거래소에서는 호가가 tick 단위로만 가능하다.
bid는 tick의 배수로 내림(floor)한다.
ask는 tick의 배수로 올림(ceil)한다.

tick_size는 0.05이다.
RP/Spread 변동에 비해 tick size가 과도하지 않은지 검증하였다.
RP 조정량은 q=1, tau=0.5일 때 0.2 (4 ticks)로 tick 반올림 후에도 비대칭이 유지된다.
half-spread는 약 0.65~0.85로 13~17 ticks에 해당하여 tick 반올림 영향이 미미하다.


7. 다단계 호가 (Multi-Level Quoting)

7-1. 개념

Paper 모드에서는 bid 1개, ask 1개로 호가를 제시한다.
Develop 모드에서는 bid와 ask 각각 n_levels(3)개의 호가를 제시한다.
실제 LP가 여러 가격 단계에 호가를 제시하는 현실을 반영한다.

7-2. 호가 배치

최우선 호가(레벨 0)는 RP와 Spread로 결정된 bid, ask 가격이다.
이후 레벨은 tick_size 간격으로 배치한다.

bid_level[0] = bid (최우선)
bid_level[1] = bid - tick_size
bid_level[2] = bid - 2 * tick_size

ask_level[0] = ask (최우선)
ask_level[1] = ask + tick_size
ask_level[2] = ask + 2 * tick_size

7-3. 레벨별 체결 판정

각 레벨에 대해 독립적으로 체결 확률을 계산한다.
레벨이 멀수록 delta가 커지므로 체결 확률이 낮아진다.

7-4. Sweep 보정

현실에서 먼 가격의 호가가 체결되려면 가까운 가격의 호가가 먼저 체결되어야 한다.
레벨 2가 체결되었으면 레벨 1과 레벨 0도 반드시 체결된다.
레벨 1이 체결되었으면 레벨 0도 반드시 체결된다.

7-5. 재고 및 현금 반영

체결된 레벨 수만큼 재고가 변동한다.
스텝당 최대 재고 변동은 n_levels(3)이다.
각 레벨의 체결 가격으로 현금을 계산한다.


8. 체결 확률

8-1. 기본 구조

포아송 프로세스 구조를 유지한다.
lambda(delta) = A * exp(-k * delta)
P(fill) = min(lambda * dt, 1.0)

8-2. 즉시 체결 조건

재고가 많이 쌓이면 호가가 mid price를 역전할 수 있다.
bid >= mid_price 또는 ask <= mid_price인 경우 delta <= 0이 된다.
이 경우 P(fill) = 1.0이다.

체결 가격은 mid price로 처리한다.
현실에서는 crossing quote를 제시하면 시장 가격(mid 근처)에 체결된다.
delta_bid <= 0이면 bid 체결 가격은 mid_price이다.
delta_ask <= 0이면 ask 체결 가격은 mid_price이다.
delta > 0이면 정상적으로 해당 호가 가격으로 체결된다.

8-3. 방향성 기반 체결 확률 조정

t+1 시점의 가격 정보를 활용하여 체결 확률의 현실성을 높인다.
가격이 상승하면 ask 체결 확률이 높아지고, 가격이 하락하면 bid 체결 확률이 높아진다.

가격 변동률 계산은 다음과 같다.
mu_pct = (S_{t+1} - S_t) / S_t * 100

bucket 구조는 다음과 같다.
변동률 절대값이 0.02% 미만이면 승수는 1.0이다.
변동률 절대값이 0.02% 이상 0.05% 미만이면 승수는 1.5이다.
변동률 절대값이 0.05% 이상 0.10% 미만이면 승수는 2.5이다.
변동률 절대값이 0.10% 이상이면 승수는 3.5이다.

승수 적용 규칙은 다음과 같다. 양방향 승수를 적용하여 방향성 체결 흐름을 극대화한다.
mu_pct > 0 (상승)이면 ask 확률에 승수를 곱하고, bid 확률은 승수로 나눈다.
mu_pct < 0 (하락)이면 bid 확률에 승수를 곱하고, ask 확률은 승수로 나눈다.
마지막 step에서는 t+1 가격이 없으므로 승수 1.0을 적용한다.

bucket 경계값과 승수는 KOSPI200 옵션 실제 데이터를 기반으로 설정했다.

8-4. 체결 확률 계산 순서

1. delta <= 0 체크. 해당하면 P(fill) = 1.0 반환.
2. 기본 확률 계산. base_prob = min(A * exp(-k * delta) * dt, 1.0)
3. 마지막 step이면 base_prob 반환.
4. t+1 가격 변동률 계산.
5. bucket에서 승수 결정.
6. 해당 방향이면 min(base_prob * multiplier, 1.0) 반환. 반대 방향이면 max(base_prob / multiplier, 0.0) 반환.


9. P&L 계산

Realized P&L은 체결된 거래에서 발생한 손익이다.
bid 체결 시 현금이 체결 가격만큼 감소한다. 다단계 체결 시 각 레벨의 체결 가격 합이 감소한다.
ask 체결 시 현금이 체결 가격만큼 증가한다. 다단계 체결 시 각 레벨의 체결 가격 합이 증가한다.

Mark-to-Market P&L은 미실현 손익이다.
현재 재고에 현재 중간가격을 곱한 값이다.

Total P&L은 Realized P&L과 Mark-to-Market P&L의 합이다.


10. 구현 위치

develop.ipynb 파일에서 다음 부분을 참조한다.

DevelopConfig 클래스에서 Develop 모드의 파라미터를 정의한다.
n_levels, tick_size, buckets 파라미터가 Paper 모드 대비 추가되었다.

tick_floor 함수에서 bid 가격을 tick 배수로 내림한다.
tick_ceil 함수에서 ask 가격을 tick 배수로 올림한다.
compute_quotes 함수에서 RP와 Spread를 계산한 후 tick 반올림을 적용한다.

compute_fill_probability_develop 함수에서 다음을 수행한다.
즉시 체결 조건(delta <= 0)을 체크한다.
t+1 가격 변동률을 계산한다.
bucket에서 승수를 결정하고 양방향으로 적용한다.

get_fill_multiplier 함수에서 bucket 구조에 따라 승수를 반환한다.

run_develop_simulation 함수에서 Develop 모드 시뮬레이션을 실행한다.
다단계 호가 생성, 레벨별 체결 판정, sweep 보정, 레벨별 체결 가격 결정을 수행한다.
SimulationState에 bid_fill(체결 레벨 수), ask_fill(체결 레벨 수), bid_levels_detail, ask_levels_detail을 기록한다.


11. 향후 논의 예정 사항

논의1. BSM 기반 옵션 이론가 경로 및 Net Delta 재고
현재 GBM으로 주가를 직접 모델링하고 있으나, 주가 GBM 경로에 BSM을 적용하여 옵션 이론가를 경로로 사용하는 방안을 검토한다.
BSM에서 계산되는 이론적 delta를 활용하여 재고를 q 대신 q * delta로 정의하는 방안을 검토한다.

논의2. Look-ahead Bias 수정
현재 t step에서 t step의 mid price를 사용하여 RP를 계산하고 체결을 판정한다.
실제 마켓메이킹에서는 t-1 step의 정보만으로 t step의 호가를 결정해야 한다.
이를 반영하여 1-step lag를 도입하는 방안을 검토한다.


Last Updated: 2026-04-04 (multi-level 호가, tick size 반올림, drift 반영)
