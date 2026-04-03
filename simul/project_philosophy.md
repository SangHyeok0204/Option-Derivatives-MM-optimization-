Avellaneda-Stoikov 모델 기반 KOSPI200 ATM 옵션 Market Making


대원칙

PAPER MODE는 논문과 똑같이 시뮬레이션하는 코드이다.
DEVELOP MODE는 논문에서 추가적으로 내 아이디어가 필요한 부분들을 반영해서 시뮬레이션을 돌리는 모드이다.


1. A-S 모델 개요 및 문제의식

1.1 논문의 문제의식

Avellaneda-Stoikov 논문은 시장조성자(Market Maker)가 유동성을 공급하면서 동시에 재고 리스크를 어떻게 통제할 것인가라는 문제를 다룬다.

딜러가 직면하는 대표적 위험은 크게 두 가지이다. 첫째는 Inventory Risk로, 자산의 방향성 있는 가격 변동으로 인해 발생하는 재고 리스크이다. 둘째는 Asymmetric Information Risk로, 정보 우위 투자자(informed trader)와 거래할 때 발생하는 역선택 리스크이다.

A-S 논문에서는 정보 보유자의 거래에 대해서는 다루지 않고, Inventory Risk 관리에 집중한다.

1.2 MM의 핵심 딜레마

MM은 스프레드 수익을 얻기 위해 시장 체결가 근처에 bid/ask를 제시해야 한다. 그러나 시장이 한쪽 방향으로 움직이면 양방향 호가 중 한쪽만 체결되면서 강제로 포지션이 생긴다. 재고가 쌓이면 방향성 노출(델타 노출)로 인해 P&L 변동성이 커진다. 따라서 MM은 재고 상태에 맞게 동적으로 비대칭 호가를 제시해야 한다.

1.3 A-S 모델의 핵심 해법

A-S 모델은 두 가지 수식으로 재고 리스크를 관리한다.

Reservation Price(기준가격)는 r(t) = s - q × γ × σ² × (T - t) 로 계산된다. 재고 q가 양수(롱)이면 기준가격을 mid보다 낮게 설정하여 매도를 유도하고, 재고 q가 음수(숏)이면 기준가격을 mid보다 높게 설정하여 매수를 유도한다.

Optimal Spread는 spread = γσ²(T-t) + (2/γ) × ln(1 + γ/k) 로 계산된다. 첫째 항은 재고 리스크 보상이고, 둘째 항은 체결확률 감소 보정이다.

1.4 A-S 모델의 철학

A-S 모델의 핵심은 체결확률을 높이는 공격적 호가 제시와 재고 리스크를 줄이는 보수적 재고관리 사이의 균형이다. A-S 전략은 최대 수익보다 위험 조정 후 안정적인 market making에 초점을 맞춘다.


2. 옵션 MM 적용 시 핵심 변경점

2.1 재고 단위: 계약 수에서 델타 노출량으로

왜 델타인가? 기초자산 MM에서는 재고 1계약이 1단위 방향성 노출과 같다. 그러나 옵션 MM에서는 재고 1계약이 1단위 방향성 노출과 같지 않다. 실제 리스크는 계약 수가 아니라 계약 수 × 델타이다.

예를 들어, 콜옵션 10계약 숏(델타 0.5)이면 지수 1pt 상승 시 5 × 승수 손실이 발생한다. 콜옵션 10계약 숏(델타 0.8)이면 지수 1pt 상승 시 8 × 승수 손실이 발생한다. 같은 10계약이라도 델타에 따라 리스크가 완전히 다르다.

수정된 재고 정의는 q_Δ = Σ(계약 수 × 델타) 이다. q_Δ = +2이면 선물 2계약 롱과 동일한 방향성 노출을 의미하고, q_Δ = -3이면 선물 3계약 숏과 동일한 방향성 노출을 의미한다.

2.2 델타의 동적 특성

핵심은 거래 없이도 델타(재고)가 실시간으로 변동한다는 것이다. 이것이 옵션 MM이 기초자산 MM보다 복잡한 근본적 이유이다.

변동 요인은 세 가지가 있다. 기초자산 가격 변동에 의한 Gamma Effect는 지수가 움직이면 델타가 변한다. 시간 경과에 의한 Charm Effect는 만기가 가까워지면 ATM 델타는 0.5로, ITM/OTM은 1/0으로 수렴한다. IV 변화에 의한 Vanna Effect는 변동성이 변하면 델타도 변한다.

실무적 의미로, 1시간 전에 델타 중립이었던 포지션이 지금은 델타 +3일 수 있다. 따라서 재고 관리 시스템은 실시간 델타 모니터링이 필수이다.

2.3 재고 관리 방식: Inventory Rebalancing (델타 헷징 X)

본 프로젝트의 핵심 설계 결정은 델타 헷징(선물 매매)을 하지 않고, 순수하게 옵션 호가 조절만으로 포지션을 관리한다는 것이다.

Inventory Rebalancing 방식의 제어 수단은 세 가지이다. Reservation Price 조절은 델타 노출 방향 반대로 기준가격을 이동시킨다. Spread 조절은 리스크 상황에 따라 스프레드를 확대하거나 축소한다. 호가 수량 조절은 체결 유도 방향의 수량을 증가시킨다.

이 방식의 장점은 순수 마켓메이킹 수익 구조를 유지하고, 헷징 비용(슬리피지, 수수료)이 없으며, A-S 모델의 원래 철학과 일치한다는 것이다.

이 방식의 리스크는 Trending Market 리스크이다. 시장이 한 방향으로 지속 이동 시, 역방향 체결이 어려워 손실이 누적될 수 있다. 강한 추세장에서는 inventory가 계속 쌓일 수 있다. 이를 완화하기 위해 γ(위험민감도)의 동적 조절이 필요하며, 이를 위해 강화학습을 적용한다.

2.4 시간지평의 재정의

원논문에서는 T가 옵션 만기였으나, 본 프로젝트에서는 T를 당일 장 마감으로 재정의한다.

이유는 실제 LP는 옵션 만기까지 재고를 들고 가지 않기 때문이다. 장중 또는 장마감 전에 재고를 정리한다. (T - t)는 당일 inventory exposure를 얼마나 더 안고 가야 하는가를 의미한다.


3. 수정된 모델 수식

3.1 상태변수

S_t는 KOSPI200 지수 가격이다. M_t는 ATM 옵션의 mid-price이다. q_t^opt는 옵션 계약 재고이다. Δ_t는 ATM 옵션의 현재 델타이다. X_t는 현금 계정(P&L)이다. t는 현재 시각이다.

핵심 상태변수인 순델타 노출은 q_Δ = q_t^opt × Δ_t 로 계산된다.

3.2 Reservation Price

원논문에서는 r(t) = s - q × γσ²(T - t) 이다.

옵션 MM 적용 시에는 r(t) = M_t - q_Δ × γ × σ²(T_close - t) 이다. 여기서 M_t는 옵션 현재 mid-price이고, q_Δ는 순델타 노출이고, γ는 위험민감도(risk aversion)이고, σ는 기초자산 변동성이고, T_close - t는 장 마감까지 남은 시간이다.

해석하면, q_Δ가 양수(롱 델타)이면 기준가격을 낮추어 옵션 매도를 유도하고, q_Δ가 음수(숏 델타)이면 기준가격을 높여 옵션 매수를 유도한다.

3.3 Spread

spread = γσ²(T - t) + (2/γ) × ln(1 + γ/k) 로 원논문 구조를 유지한다. k는 호가 민감도 파라미터(체결강도 감소 속도)이다.

3.4 호가 배치

p_bid = r(t) - δ_bid 이고, p_ask = r(t) + δ_ask 이다. 여기서 δ_bid + δ_ask = spread 이다.


4. 강화학습 기반 개선 (Alpha-AS 참조)

4.1 배경: Alpha-AS 논문

Alpha-AS 논문 "A reinforcement learning approach to improve the performance of the Avellaneda-Stoikov market-making algorithm"은 A-S 모델의 파라미터를 강화학습(Double DQN)으로 동적 조절하여 성능을 개선한다.

4.2 조절 대상

γ(위험민감도)는 inventory penalty 강도를 조절한다. γ가 높으면 보수적이고, 낮으면 공격적이다. skew는 bid/ask 비대칭 정도를 조절하며, 체결 방향 유도 강도를 결정한다.

본 프로젝트에서는 시장 상황에 따라 γ를 동적으로 조절한다. Trending market에서는 γ를 높여 보수적으로 대응하고, Range-bound market에서는 γ를 낮춰 공격적으로 대응한다.

4.3 State Features

Private 카테고리에는 q_Δ(델타 재고, 현재 방향성 노출)와 Score(P&L, 누적 손익)가 있다. Market 카테고리에는 Microprice(호가잔량 가중 mid-price), Imbalance(매수/매도 잔량 불균형), 체결방향(최근 체결이 BUY/SELL 주도인지), 1초체결량(단기 거래 강도)이 있다.

Microprice는 (AskQty₁ × BidPrice₁ + BidQty₁ × AskPrice₁) / (AskQty₁ + BidQty₁) 로 계산된다.

Imbalance는 (ΣBidQty - ΣAskQty) / (ΣBidQty + ΣAskQty) 로 계산된다. Imbalance가 양수이면 매수 압력이 우세하고, 음수이면 매도 압력이 우세하다.

4.4 Reward Function: Asymmetric Dampened P&L

Alpha-AS에서 제안한 보상 함수는 R = sign(ΔP&L) × |ΔP&L|^η 이다. η(dampening)는 0.5로 큰 손익의 영향을 감소시킨다. Asymmetric은 손실 가중치를 높여 손실에 더 민감하게 반응하도록 한다. 목적은 안정적인 수익 추구와 큰 손실 회피이다.

4.5 Action Cycle

5초 단위로 action을 결정한다(Alpha-AS 기준). 매 cycle마다 γ, skew 조절 여부를 결정한다.


5. 데이터 수집 설계

5.1 수집 주기

1초 스냅샷 방식을 채택한다. ATM 옵션 체결 빈도는 약 2-5회/초(평균)이다. 데이터 크기는 1시간에 약 3,600행으로 관리 가능하다. 초 단위 체결 패턴 분석이 가능하다.

5.2 수집 항목

기본 데이터로 옵션 시세(현재가, 체결시간, 누적거래량), 옵션 Greeks(IV, 델타, 감마, 세타, 베가, 로), 옵션 호가(매수/매도 호가 1~5단계, 잔량), 지수(KOSPI200 현재가, 등락률, 거래량)를 수집한다.

5.3 파생 컬럼 (실시간 계산)

1초체결량은 현재 누적거래량에서 이전 누적거래량을 빼서 계산하며, 단기 거래 강도를 파악하는 용도이다. 체결방향은 체결가와 호가를 비교하여 매수/매도 주도를 판단한다. 매수주도체결량은 체결방향이 BUY일 때 1초체결량으로 매수 압력을 측정한다. 매도주도체결량은 체결방향이 SELL일 때 1초체결량으로 매도 압력을 측정한다.

체결방향 판단 로직은 다음과 같다. 체결가가 매도호가1 이상이면 BUY(매수 주도, 시장가 매수)이다. 체결가가 매수호가1 이하이면 SELL(매도 주도, 시장가 매도)이다. 그 외에는 MID(중간 가격 체결)이다.

5.4 향후 추가 예정 컬럼

Microprice는 호가잔량 가중 mid-price로 계산한다. Imbalance는 (ΣBid - ΣAsk) / (ΣBid + ΣAsk)로 계산한다. Spread는 매도호가1에서 매수호가1을 빼서 계산한다.


6. 최종 정리

한 문장 요약

A-S 모델의 Reservation Price + Spread 구조를 유지하되, 재고 단위를 델타 노출량으로 변경하고, 델타 헷징 없이 순수 Inventory Rebalancing 방식으로 포지션을 관리하며, 강화학습을 통해 위험민감도(γ)를 동적으로 조절한다.

원논문 vs 본 프로젝트 비교

대상 자산은 원논문에서는 단일 주식이고, 본 프로젝트에서는 KOSPI200 ATM 옵션이다. 재고 정의는 원논문에서는 계약 수 q이고, 본 프로젝트에서는 델타 노출량 q_Δ이다. 재고 특성은 원논문에서는 거래 시에만 변동하고, 본 프로젝트에서는 실시간 변동(Gamma effect)한다. 재고 관리는 원논문에서는 호가 조절이고, 본 프로젝트에서는 호가 조절만(헷징 X)이다. 파라미터는 원논문에서는 고정 γ이고, 본 프로젝트에서는 RL 기반 동적 γ이다. 시간지평은 원논문에서는 옵션 만기이고, 본 프로젝트에서는 당일 장 마감이다. Mid price는 원논문에서는 시장 mid이고, 본 프로젝트에서는 실제 체결 기반 + IV 반영이다.

핵심 리스크 인지

Trending Market 리스크는 한 방향 추세 시 inventory가 누적되는 것으로, γ를 동적으로 증가시키는 RL로 대응한다. Dynamic Delta 리스크는 거래 없이 재고가 변동하는 것으로, 실시간 델타 모니터링으로 대응한다. Low Liquidity 리스크는 체결 지연으로 rebalancing이 실패하는 것으로, Spread 확대로 대응한다.


참고문헌

1. Avellaneda, M., & Stoikov, S. (2008). High-frequency trading in a limit order book. Quantitative Finance, 8(3), 217-224.

2. Falces, G., et al. (2023). A reinforcement learning approach to improve the performance of the Avellaneda-Stoikov market-making algorithm.

3. KRX 자료: 주가지수옵션 상품명세(https://open.krx.co.kr/contents/OPN/01/01040202/OPN01040202.jsp), 시장조성자 법적 의무(https://rule.krx.co.kr/out/index.do)

4. 기타 참고: Market Making & Inventory Management Guide(https://www.marketcalls.in/market-microstructure/understanding-market-making-inventory-management-a-traders-guide.html)


Last Updated: 2026-03-26
