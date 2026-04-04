강화학습 기반 개선 계획

이 문서는 A-S 모델의 파라미터를 강화학습으로 동적 조절하는 계획을 다룬다.
프로젝트의 전체 철학과 방향은 프로젝트가이드.md에서 다루며, 이 문서에서는 다루지 않는다.
각 모드의 구현 상세는 paper모드.md, develop모드.md에서 다루며, 이 문서에서는 다루지 않는다.


1. 배경: Alpha-AS 논문

Alpha-AS 논문 "A reinforcement learning approach to improve the performance of the Avellaneda-Stoikov market-making algorithm"은 A-S 모델의 파라미터를 강화학습(Double DQN)으로 동적 조절하여 성능을 개선한다.


2. 조절 대상

gamma(위험민감도)는 inventory penalty 강도를 조절한다. gamma가 높으면 보수적이고, 낮으면 공격적이다.
skew는 bid/ask 비대칭 정도를 조절하며, 체결 방향 유도 강도를 결정한다.

본 프로젝트에서는 시장 상황에 따라 gamma를 동적으로 조절한다.
Trending market에서는 gamma를 높여 보수적으로 대응한다.
Range-bound market에서는 gamma를 낮춰 공격적으로 대응한다.


3. State Features

Private 카테고리에는 q_delta(델타 재고, 현재 방향성 노출)와 Score(P&L, 누적 손익)가 있다.
Market 카테고리에는 Microprice(호가잔량 가중 mid-price), Imbalance(매수/매도 잔량 불균형), 체결방향(최근 체결이 BUY/SELL 주도인지), 1초체결량(단기 거래 강도)이 있다.

Microprice는 (AskQty1 * BidPrice1 + BidQty1 * AskPrice1) / (AskQty1 + BidQty1) 로 계산된다.

Imbalance는 (BidQty - AskQty) / (BidQty + AskQty) 로 계산된다.
Imbalance가 양수이면 매수 압력이 우세하고, 음수이면 매도 압력이 우세하다.


4. Reward Function: Asymmetric Dampened P&L

Alpha-AS에서 제안한 보상 함수는 R = sign(delta_PnL) * |delta_PnL|^eta 이다.
eta(dampening)는 0.5로 큰 손익의 영향을 감소시킨다.
Asymmetric은 손실 가중치를 높여 손실에 더 민감하게 반응하도록 한다.
목적은 안정적인 수익 추구와 큰 손실 회피이다.


5. Action Cycle

5초 단위로 action을 결정한다(Alpha-AS 기준).
매 cycle마다 gamma, skew 조절 여부를 결정한다.


Last Updated: 2026-04-04 (중복 제거, RL 계획만 분리)
