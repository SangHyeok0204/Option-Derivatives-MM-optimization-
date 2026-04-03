Develop 모드 설명

이 문서는 A-S 논문을 옵션 Market Making에 맞게 확장한 Develop 모드의 설정과 변경점을 설명한다.
프로젝트의 전체 철학은 프로젝트가이드.md에서 다루며, 이 문서에서는 다루지 않는다.
Paper 모드의 원본 설정은 paper모드.md에서 다루며, 이 문서에서는 다루지 않는다.


1. Develop 모드의 목적

A-S 논문의 이론적 프레임워크를 유지하면서 옵션 Market Making의 현실적 특성을 반영한다.
KOSPI200 ATM 옵션을 대상으로 실제 데이터 기반 시뮬레이션을 수행한다.


2. Paper 모드와의 핵심 차이 요약

가격 데이터가 다르다.
Paper 모드에서는 GBM으로 생성한 가상 가격을 사용한다.
Develop 모드에서는 실제 KOSPI200 옵션 데이터의 mid price를 사용한다.
mid price = (매도호가1 + 매수호가1) / 2로 계산한다.

재고 정의가 다르다.
Paper 모드에서는 계약 수 q를 사용한다.
Develop 모드에서는 Net Delta를 사용한다. Net Delta는 계약 수에 옵션 델타를 곱한 값이다.
옵션 델타는 실제 데이터에서 가져온다.

변동성 파라미터는 동일하다.
Paper 모드와 Develop 모드 모두 고정 sigma = 2.0을 사용한다.

시간 정규화는 동일하다.
Paper 모드와 Develop 모드 모두 T = 1로 정규화한다.
Develop 모드에서 T는 당일 장 마감을 1로 정규화한 것이다.
dt = 1 / n_steps로 계산하며, n_steps는 데이터 개수에서 결정된다.

추가 기능이 있다.
즉시 체결 조건(delta <= 0)과 mid price 체결이 있다.
방향성 기반 체결 확률 조정(bucket 승수)이 있다.


3. 재고 정의의 변경

3-1. Net Delta 개념

옵션에서는 계약 수가 아닌 델타 노출이 실제 리스크를 결정한다.
시뮬레이션에서는 계약 수(contracts)와 Net Delta를 모두 추적한다.

체결 시 포지션 변화는 다음과 같다.
bid 체결 시: contracts += 1, net_delta += option_delta (매수)
ask 체결 시: contracts -= 1, net_delta -= option_delta (매도)

option_delta는 해당 시점의 실제 데이터에서 가져온 옵션 델타 값이다.
동일한 계약 수라도 시점에 따라 델타가 다르므로 Net Delta도 다르게 누적된다.

예시는 다음과 같다.
t=0에서 1계약 매수 (delta=0.48): contracts=1, net_delta=0.48
t=1에서 1계약 매수 (delta=0.50): contracts=2, net_delta=0.98
t=2에서 1계약 매도 (delta=0.49): contracts=1, net_delta=0.49

3-2. Reservation Price 수식 변경

Paper 모드 수식은 다음과 같다.
r = s - q * gamma * sigma^2 * (T - t)

Develop 모드 수식은 다음과 같다.
r = s - q_delta * gamma * sigma^2 * (T - t)

각 변수의 의미는 다음과 같다.
s는 옵션 mid price이다. 실제 데이터의 (매도호가1 + 매수호가1) / 2이다.
q_delta는 Net Delta이다. 누적된 계약 × 옵션델타 값이다.
sigma는 고정값 2.0이다. Paper 모드와 동일한 값을 사용한다.
(T - t)는 정규화된 잔여 시간이다.

핵심 차이는 q 대신 q_delta를 사용한다는 점이다.
계약 수가 아닌 델타 노출에 비례하여 RP를 조정한다.


4. 변동성 파라미터

4-1. 고정 sigma 사용

Paper 모드와 동일하게 고정 sigma = 2.0을 사용한다.
sigma = 2.0

이 값은 RP 조정량과 스프레드 계산에 사용된다.
실제 옵션의 IV와는 별개로, 모델 내부에서 사용하는 스케일링 파라미터이다.

4-2. 고정 sigma를 사용하는 이유

단위 일관성 문제가 있다.
IV는 연간화된 변동성이다. 예를 들어 IV 50%는 연간 기준이다.
A-S 논문의 sigma는 정규화된 시간 단위(T=1) 기준이다.
IV를 그대로 사용하면 gamma * sigma^2 값이 너무 작아진다.

수치 비교는 다음과 같다.
IV 기반: gamma * sigma^2 = 0.1 * 0.25 = 0.025
고정 sigma: gamma * sigma^2 = 0.1 * 4 = 0.4
16배 차이가 발생한다.

RP 조정량이 tick size(0.05pt)보다 커야 비대칭 호가가 작동한다.
고정 sigma = 2.0을 사용해야 유의미한 RP 조정이 가능하다.

4-3. IV 정보의 활용

IV는 RP/Spread 계산에 직접 사용하지 않는다.
실제 데이터에서 IV를 가져오지만, 모델에서는 고정 sigma를 사용한다.


5. 시간 지평의 변경

5-1. 시간 정규화

논문과 동일하게 시간을 정규화하여 사용한다.
T = 1 (정규화된 시간 지평)
dt = 1 / n_steps (정규화된 시간 간격)

실제 데이터는 1분 간격으로 수집하며, 6시간 동안 n_steps = 360개의 스냅샷이 생성된다.
정규화된 dt = 1/360 = 0.00278이다.

이 방식의 장점은 다음과 같다.
논문의 A, k 파라미터를 그대로 사용할 수 있다.
sigma = 2.0의 의미가 논문과 동일하게 유지된다.
τ = (T-t)/T가 0~1 범위로 정규화되어 수식이 일관성 있게 작동한다.

5-2. 장 마감 기준

원논문의 T는 옵션 만기다.
Develop 모드의 T는 당일 장 마감이다.
실제 LP는 옵션 만기까지 재고를 들고 가지 않고 장중에 정리하기 때문이다.

시간 정규화를 적용하면 다음과 같다.
실제 시간 6시간을 T = 1로 정규화한다.
step = 100이면 τ = (360-100)/360 = 0.722이다.

5-3. Indicator Function

장 막판에 (T - t)가 0에 가까워지면 스프레드가 지나치게 좁아지는 문제가 있다.
이를 해결하기 위해 Indicator Function을 적용한다.

tau_eff = threshold (상수), if time_remaining > threshold
tau_eff = time_remaining, if time_remaining <= threshold

threshold는 정규화된 시간으로 설정한다. 기본값은 1/6 (1시간/6시간)이다.
장 초반과 중반(τ > 1/6)에는 tau_eff = 1/6으로 고정되어 안정적인 호가를 제시한다.
장 막판(τ ≤ 1/6)에는 tau_eff = τ로 전환되어 청산 유도가 강화된다.


6. Spread 계산

6-1. 이론적 스프레드 수식

Develop 모드에서도 Paper 모드와 동일한 이론적 스프레드 수식을 사용한다.

spread = gamma * sigma^2 * tau_eff + (2 / gamma) * ln(1 + gamma / k)

각 변수의 의미는 다음과 같다.
gamma는 위험 회피 계수이다.
sigma는 고정값 2.0이다. Paper 모드와 동일한 값을 사용한다.
tau_eff는 effective time remaining이다. Indicator Function이 적용된 값이다.
k는 체결 강도 감쇠율이다. Develop 모드에서는 k_develop를 사용한다.

첫 번째 항 gamma * sigma^2 * tau_eff는 재고 리스크 보상이다.
두 번째 항 (2 / gamma) * ln(1 + gamma / k)는 체결확률 보정이다.

6-2. Paper 모드와의 차이

Paper 모드와 Develop 모드의 핵심 차이는 Reservation Price에서 재고를 정의하는 방식이다.
Paper 모드에서는 계약 수 q를 사용한다.
Develop 모드에서는 Net Delta를 사용한다.

sigma는 두 모드 모두 고정값 2.0을 사용한다.

6-3. 체결 확률 기본 구조

Develop 모드에서도 포아송 프로세스 구조는 유지한다.
lambda(delta) = A * exp(-k * delta)
P(fill) = lambda * dt

시간 정규화로 인해 논문과 동일한 파라미터를 사용한다.
A = 140 (논문 값)
k = 1.5 (논문 값)
dt = 1/360 = 0.00278 (정규화)

체결확률 계산 예시는 다음과 같다.
delta = 1.0일 때: P = 140 * exp(-1.5) * 0.00278 = 140 * 0.223 * 0.00278 = 8.7%

6-4. 즉시 체결 조건

재고가 많이 쌓이면 호가가 mid price를 역전할 수 있다.
bid >= mid_price 또는 ask <= mid_price인 경우 delta <= 0이 된다.
이 경우 시장가보다 유리한 가격을 제시한 것이므로 즉시 체결된다.

즉시 체결 조건은 다음과 같다.
delta <= 0이면 P(fill) = 1.0이다.

체결 가격은 mid price로 처리한다.
현실에서는 crossing quote를 제시하면 내 호가 가격이 아니라 시장 가격(mid 근처)에 체결된다.
bid > mid인데 내 bid 가격으로 체결되면 손해이고, ask < mid인데 내 ask 가격으로 체결되면 손해이다.
따라서 delta <= 0인 경우 체결 가격을 mid price로 설정하여 현실을 반영한다.

구체적인 처리는 다음과 같다.
delta_bid <= 0이면 bid 체결 가격은 mid_price이다. (bid가 아님)
delta_ask <= 0이면 ask 체결 가격은 mid_price이다. (ask가 아님)
delta > 0이면 정상적으로 해당 호가 가격으로 체결된다.

이는 Paper 모드의 한계를 보완한 것이다.
Paper 모드에서는 delta가 음수여도 확률적 체결을 수행했다.
Develop 모드에서는 현실적으로 즉시 체결 처리하고, 체결 가격도 현실에 맞게 mid price로 처리한다.

6-5. 방향성 기반 체결 확률 조정

t+1 시점의 가격 정보를 활용하여 체결 확률의 현실성을 높인다.
가격이 상승하면 ask 체결 확률이 높아지고, 가격이 하락하면 bid 체결 확률이 높아진다.

가격 변동률 계산은 다음과 같다.
mu_pct = (S_{t+1} - S_t) / S_t * 100

bucket 구조는 다음과 같다.
변동률 절대값이 0.02% 미만이면 승수는 1.0이다. 결과 확률은 약 23%이다.
변동률 절대값이 0.02% 이상 0.05% 미만이면 승수는 1.5이다. 결과 확률은 약 34%이다.
변동률 절대값이 0.05% 이상 0.10% 미만이면 승수는 2.5이다. 결과 확률은 약 57%이다.
변동률 절대값이 0.10% 이상이면 승수는 3.5이다. 결과 확률은 약 80%이다.

승수 적용 규칙은 다음과 같다. 양방향 승수를 적용하여 방향성 체결 흐름을 극대화한다.
mu_pct > 0 (상승)이면 ask 확률에 승수를 곱하고, bid 확률은 승수로 나눈다.
mu_pct < 0 (하락)이면 bid 확률에 승수를 곱하고, ask 확률은 승수로 나눈다.
마지막 step에서는 t+1 가격이 없으므로 승수 1.0을 적용한다.

양방향 승수 적용 시 체결 비율은 다음과 같다.
변동률 0.10% 이상일 때 ask:bid 비율은 약 12배이다. (80% : 6.6%)
이는 시장 현실을 반영한다. 가격 상승 시 매수세 유입으로 ask가 체결되고, 매도자들이 호가를 올려 bid 체결이 줄어든다.

bucket 경계값과 승수는 KOSPI200 옵션 실제 데이터를 기반으로 설정했다.
데이터 분석 결과 10틱 간격 기준 변동률 분포는 다음과 같았다.
66%가 0.02% 이내, 30%가 0.02%~0.05%, 3.7%가 0.05%~0.10%, 0.1%가 0.10% 초과.

6-6. 체결 확률 계산 순서

1. delta <= 0 체크. 해당하면 P(fill) = 1.0 반환.
2. 기본 확률 계산. base_prob = min(A * exp(-k * delta) * dt, 1.0)
3. 마지막 step이면 base_prob 반환.
4. t+1 가격 변동률 계산.
5. bucket에서 승수 결정.
6. 해당 방향이면 min(base_prob * multiplier, 1.0) 반환. 아니면 base_prob 반환.


7. Safety Cap

7-1. 문제 상황

gamma가 크거나 재고가 많이 쌓이면 비정상적 호가가 발생할 수 있다.
Bid가 Mid보다 높거나 Ask가 Mid보다 낮으면 즉시 손실이 확정된다.

7-2. 해결 방법

Safety Cap을 적용하여 호가를 제한한다.
bid_final = min(bid_raw, mid_price - min_distance)
ask_final = max(ask_raw, mid_price + min_distance)

min_distance는 최소 호가 거리이다. 기본값은 0이다.
Paper 모드에서는 적용하지 않는다.

7-3. Skewed Quote

Safety Cap 적용 시 스프레드가 비대칭해질 수 있다.
재고가 롱이면 Ask를 낮추고 싶지만 Mid 아래로는 내릴 수 없다. Ask는 고정되고 Bid만 낮아진다.
재고가 숏이면 Bid를 높이고 싶지만 Mid 위로는 올릴 수 없다. Bid는 고정되고 Ask만 높아진다.

이는 청산 욕구와 의무 호가 제약의 트레이드오프를 반영한다.


8. Tick Size 적용

실제 거래소에서는 호가가 tick 단위로만 가능하다.
bid는 tick의 배수로 내림한다.
ask는 tick의 배수로 올림한다.

tick_size는 설정 가능하다.
apply_tick_size 옵션으로 활성화 여부를 결정한다.


9. 시뮬레이션 실행 순서

9-1. 핵심 원칙

t step의 호가를 설정할 때 t step의 mid price는 아직 모른다.
t-1 step의 정보만 알고 있는 상태에서 t step의 호가를 결정한다.
이를 반영하기 위해 상태 기록 후 새 호가를 설정한다.

9-2. 단일 스텝 실행 순서

_run_step 메서드는 다음 순서로 실행된다.

1. t 시점의 snapshot 가져오기
2. t-1에서 설정한 호가로 t 시점 체결 시뮬레이션
3. 체결 실행 (t-1에서 설정한 호가 가격으로 체결)
4. 헷지 실행 (develop 모드)
5. 상태 기록 (t-1 기반 RP가 기록됨)
6. t 시점의 mid price로 t+1용 새 호가 설정

9-3. 결과

t step에서 기록되는 RP는 t-1 step의 mid price를 기반으로 계산된 값이다.
RP와 mid price 사이에 1 step lag가 발생한다.
이것이 실제 마켓메이킹 환경을 정확히 반영한다.


10. 구현 위치

develop.ipynb 파일에서 다음 부분을 참조한다.

DevelopConfig 클래스에서 buckets 파라미터로 체결 확률 승수를 설정한다.
기본값은 [(0.02, 1.0), (0.05, 1.5), (0.10, 2.5), (inf, 3.5)]이다.

compute_fill_probability_develop 함수에서 다음을 수행한다.
즉시 체결 조건(delta <= 0)을 체크한다.
t+1 가격 변동률을 계산한다.
bucket에서 승수를 결정하고 해당 방향에 적용한다.

get_fill_multiplier 함수에서 bucket 구조에 따라 승수를 반환한다.

run_develop_simulation 함수에서 Develop 모드 시뮬레이션을 실행한다.
SimulationState에 bid_prob, ask_prob, price_change_pct, multiplier를 추가로 기록한다.


11. 향후 개선 예정 사항

(T-t) 문제가 있다.
만기 근처에서 재고 조정 메커니즘이 약해지는 구조적 한계가 있다.
qγσ²(T-t) 항이 T-t → 0일 때 0으로 수렴하여 재고가 많아도 조정력이 약해진다.
향후 이를 개선할 예정이다.


Last Updated: 2026-04-03 (실제 옵션 데이터 기반 시뮬레이션, Net Delta 기반 재고 관리)
