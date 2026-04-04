Develop 모드 설명

이 문서는 A-S 논문을 옵션 Market Making에 맞게 확장한 Develop 모드의 설정과 변경점을 설명한다.
프로젝트의 전체 철학은 프로젝트가이드.md에서 다루며, 이 문서에서는 다루지 않는다.
Paper 모드의 원본 설정은 paper모드.md에서 다루며, 이 문서에서는 다루지 않는다.


1. Develop 모드의 목적

A-S 논문의 이론적 프레임워크를 유지하면서 옵션 Market Making의 현실적 특성을 반영한다.
원논문은 주가를 직접 거래하는 상황을 가정하지만, Develop 모드에서는 주가 GBM 경로로부터 BSM 옵션 이론가를 도출하여 옵션 MM을 시뮬레이션한다.


2. Paper 모드와의 핵심 차이 요약

가격 데이터가 다르다.
Paper 모드에서는 GBM으로 생성한 가상 주가를 직접 mid price로 사용한다.
Develop 모드에서는 주가 GBM 경로를 BSM에 입력하여 옵션 이론가를 mid price로 사용한다.

재고 정의가 다르다.
Paper 모드에서는 계약 수 q를 사용한다.
Develop 모드에서는 Net Delta (q * delta_t)를 사용한다. delta_t는 매 step의 BSM 델타이다.

추가 기능이 있다.
다단계 호가(multi-level quoting)가 있다.
Tick size 반올림이 있다.
즉시 체결 조건(delta <= 0)과 mid price 체결이 있다.
방향성 기반 체결 확률 조정(주가 변동률 기준 bucket 승수)이 있다.


3. 시뮬레이션 환경 설정

3-1. A-S 모델 파라미터

시뮬레이션 총 시간 T는 1로 정규화한다.
변동성 sigma는 2이다. A-S 모델 내부의 스케일링 파라미터이다.
시간 간격 dt는 0.005이다.
총 스텝 수 n_steps는 200이다.
위험 회피 계수 gamma는 0.1이다.
체결 강도 A는 140이다.
체결 강도 감쇠율 k는 1.5이다.

3-2. 주가 GBM 파라미터

초기 주가 S_stock_0은 800이다. KOSPI200 지수를 상정한다.
주가 drift는 기본값 0이며, % 단위이다. 15로 설정하면 시뮬레이션 동안 +15% 상승을 의미한다.
주가 변동성 sigma_stock은 10이다. 일간 변동폭 약 1.25% 수준이다.

drift를 일부러 양수로 설정하는 이유는 추세가 있는 시장에서 재고가 한쪽 방향으로 쌓이는 문제를 관찰하기 위함이다.

3-3. BSM 파라미터

행사가 K는 800이다. ATM을 가정하여 S_stock_0과 동일하게 설정한다.
무위험이자율 r은 0.03이다.
옵션 잔존만기 T_option은 0.082이다. 약 30일에 해당한다.
BSM 변동성 sigma_bsm은 0.5이다. 연간 50%를 의미한다.

T_option은 시뮬레이션 중 고정한다. 장중 하루 동안의 변화는 무시 가능한 수준이다.

3-4. Develop 확장 파라미터

호가 단계 수 n_levels는 3이다.
틱 사이즈 tick_size는 0.05이다.


4. 가격 경로 생성

4-1. 주가 GBM 경로

주가는 drift가 포함된 Brownian motion을 따른다.
drift는 % 단위이므로 절대값으로 변환한다. drift_abs = S_stock_0 * drift / 100
S(t+dt) = S(t) + drift_abs * dt + sigma_stock * sqrt(dt) * Z
여기서 Z는 표준정규분포를 따르는 난수다.

4-2. BSM 옵션 이론가

매 step의 주가 S_t를 BSM 공식에 입력하여 콜옵션 이론가와 델타를 계산한다.

콜옵션 가격은 다음과 같다.
C = S * N(d1) - K * exp(-r * T_option) * N(d2)
d1 = (ln(S/K) + (r + sigma_bsm^2/2) * T_option) / (sigma_bsm * sqrt(T_option))
d2 = d1 - sigma_bsm * sqrt(T_option)
여기서 N은 표준정규분포의 누적분포함수이다.

콜옵션 델타는 N(d1)이다.

초기 조건(S=800, K=800, T_option=0.082, sigma_bsm=0.5)에서 옵션 이론가는 약 47pt, 델타는 약 0.54이다.


5. 재고 정의: Net Delta

5-1. 개념

옵션에서는 계약 수가 아닌 델타 노출이 실제 리스크를 결정한다.
Net Delta는 계약 수에 해당 시점의 BSM 델타를 곱한 값이다.
net_delta = inventory * delta_t

delta_t는 매 step마다 BSM에서 계산되므로, 거래 없이도 net_delta가 변동한다.
이것이 옵션 MM의 핵심 특성인 Dynamic Delta 리스크이다.

5-2. Reservation Price 수식

r = s - net_delta * gamma * sigma^2 * (T - t)

각 변수의 의미는 다음과 같다.
s는 옵션 이론가(mid price)이다.
net_delta는 inventory * delta_t이다.
sigma는 A-S 모델의 고정값 2.0이다.
(T - t)는 정규화된 잔여 시간이다.

Paper 모드 대비 ATM delta가 약 0.5이므로 RP 조정력이 약 절반으로 줄어든다.
이는 옵션 1계약이 주식 1주보다 방향성 리스크가 작다는 현실을 반영한다.


6. Spread 계산

Paper 모드와 동일한 이론적 스프레드 수식을 사용한다.
spread = gamma * sigma^2 * (T - t) + (2 / gamma) * ln(1 + gamma / k)


7. Tick Size 반올림

실제 거래소에서는 호가가 tick 단위로만 가능하다.
bid는 tick의 배수로 내림(floor)한다.
ask는 tick의 배수로 올림(ceil)한다.

tick_size는 0.05이다. KOSPI200 옵션의 실제 tick size와 동일하다.


8. 다단계 호가 (Multi-Level Quoting)

8-1. 호가 배치

bid와 ask 각각 n_levels(3)개의 호가를 제시한다.
최우선 호가(레벨 0)는 RP와 Spread에 tick 반올림을 적용한 가격이다.
이후 레벨은 tick_size 간격으로 배치한다.

bid_level[i] = bid - i * tick_size (i = 0, 1, 2)
ask_level[i] = ask + i * tick_size (i = 0, 1, 2)

8-2. Sweep 보정

먼 레벨이 체결되면 가까운 레벨도 반드시 체결된다.
레벨 2 체결 시 레벨 1과 레벨 0도 체결된다.

8-3. 재고 반영

체결된 레벨 수만큼 재고가 변동한다.
스텝당 최대 재고 변동은 n_levels(3)이다.


9. 체결 확률

9-1. 기본 구조

포아송 프로세스 구조를 유지한다.
lambda(delta) = A * exp(-k * delta)
P(fill) = min(lambda * dt, 1.0)

9-2. 즉시 체결 조건

delta <= 0이면 P(fill) = 1.0이다.
체결 가격은 mid price(옵션 이론가)로 처리한다.
delta > 0이면 정상적으로 해당 호가 가격으로 체결된다.

9-3. 방향성 기반 체결 확률 조정

주가의 t+1 시점 변동률을 기준으로 체결 확률을 조정한다.
옵션 가격 변동률이 아닌 주가 변동률을 사용하는 이유는 다음과 같다.
첫째, bucket threshold가 KOSPI200 지수 데이터로 캘리브레이션되었다.
둘째, 옵션 체결을 유도하는 근본 원인은 기초자산의 방향성이다.
셋째, 옵션 가격 수익률은 delta에 의해 증폭되어 bucket이 무의미해진다.

주가 변동률 계산은 다음과 같다.
stock_change_pct = (S_stock_{t+1} - S_stock_t) / S_stock_t * 100

bucket 구조는 다음과 같다.
변동률 절대값이 0.02% 미만이면 승수는 1.0이다.
변동률 절대값이 0.02% 이상 0.05% 미만이면 승수는 1.5이다.
변동률 절대값이 0.05% 이상 0.10% 미만이면 승수는 2.5이다.
변동률 절대값이 0.10% 이상이면 승수는 3.5이다.

승수 적용 규칙은 다음과 같다.
주가 상승이면 ask 확률에 승수를 곱하고, bid 확률은 승수로 나눈다.
주가 하락이면 bid 확률에 승수를 곱하고, ask 확률은 승수로 나눈다.


10. P&L 계산

Realized P&L은 체결된 거래에서 발생한 손익이다.
다단계 체결 시 각 레벨의 체결 가격 합으로 계산한다.

Mark-to-Market P&L은 미실현 손익이다.
현재 재고에 현재 옵션 이론가를 곱한 값이다.

Total P&L은 Realized P&L과 Mark-to-Market P&L의 합이다.


11. 구현 위치

develop.ipynb 파일에서 다음 부분을 참조한다.

DevelopConfig 클래스에서 A-S 파라미터, 주가 GBM 파라미터, BSM 파라미터, 확장 파라미터를 정의한다.

norm_cdf, bsm_call_price, bsm_delta 함수에서 BSM 계산을 수행한다.
generate_stock_path 함수에서 주가 GBM 경로를 생성한다.
generate_option_path 함수에서 주가 경로로부터 옵션 이론가와 델타 경로를 계산한다.

compute_reservation_price 함수에서 net_delta를 사용하여 RP를 계산한다.
compute_quotes 함수에서 RP와 Spread를 계산한 후 tick 반올림을 적용한다.

compute_fill_probability_develop 함수에서 t-1→t 주가 변동률 기준으로 방향성 승수를 적용한다.
run_develop_simulation 함수에서 1-step lag 구조로 다단계 호가, sweep 보정, 레벨별 체결을 수행한다.


12. 1-Step Lag 구조

12-1. 개념

호가를 설정하는 ���점의 정보와 체결을 판정하는 시점의 정보가 1 step 분리된다.
실제 마켓메이킹에서 호가를 먼저 깔고, 이후 시장이 움직��� 결과로 체결이 결정되는 현실을 반영한다.

12-2. 실행 순서

step 0에서는 첫 mid price를 기준으로 호가만 설정하고 체결은 없다.
step t (t >= 1)에서는 다음 순서로 실행된다.
1. t시��의 mid price 확인
2. t-1에서 깔아놓은 호가와 t시점 mid price 간 거리(delta) 계산
3. 체결 판정 및 체결 실행
4. t시점의 mid price로 새 호가 설정 (t+1에서 체결될 호가)

12-3. 효과

가격이 상승하면 t-1 ask가 mid에 가까워져 ask 체결 확률이 자연스럽게 높아진다.
가격이 하락하면 t-1 bid가 mid에 가까워져 bid 체결 확률이 자연스럽게 높아진다.
이 자연 비대칭에 bucket 승수가 추가��� 적용되어 방향성 체결을 강화한다.

12-4. bucket 승수 기준 변경

이���에는 t+1 주가��� 미리 보는 look-ahead 방��이었다.
1-step lag 도입 후에는 t-1→t 주가 변동률을 사용한다.
t시점 체결 판정 시 t-1→t 변동�� 이미 관찰된 정보이므로 look-ahead bias가 없다.


13. 향후 예정 사항

향후. 변동성 모델링
현재 sigma(A-S)와 sigma_bsm은 고정값이다.
GARCH 모형과 강화학습을 통해 변동성을 동적으로 조절하는 것이 최종 목표이다.
변동성에 따라 RP 조정력을 시간에 따라 조절할 수 있게 설정할 예정이다.


Last Updated: 2026-04-04 (1-step lag 구조, look-ahead bias 제거, bucket 승수 t-1→t 기준)
