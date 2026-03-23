# Avellaneda-Stoikov 모델 기반 KOSPI200 ATM 옵션 Market Making

---

## 1. A-S 모델 개요 및 문제의식

### 1.1 논문의 문제의식

Avellaneda-Stoikov 논문은 시장조성자(Market Maker)가 유동성을 공급하면서 동시에 재고 리스크를 어떻게 통제할 것인가라는 문제를 다룬다.

딜러가 직면하는 대표적 위험은 크게 두 가지이다:

| 위험 유형 | 설명 |
|----------|------|
| Inventory Risk | 자산의 방향성 있는 가격 변동으로 인해 발생하는 재고 리스크 |
| Asymmetric Information Risk | 정보 우위 투자자(informed trader)와 거래할 때 발생하는 역선택 리스크 |

A-S 논문에서는 정보 보유자의 거래에 대해서는 다루지 않고, **Inventory Risk 관리**에 집중한다.

### 1.2 MM의 핵심 딜레마

1. MM은 스프레드 수익을 얻기 위해 시장 체결가 근처에 bid/ask를 제시해야 한다
2. 그러나 시장이 한쪽 방향으로 움직이면 양방향 호가 중 한쪽만 체결되면서 강제로 포지션이 생긴다
3. 재고가 쌓이면 방향성 노출(델타 노출)로 인해 P&L 변동성이 커진다
4. 따라서 MM은 재고 상태에 맞게 **동적으로 비대칭 호가**를 제시해야 한다

### 1.3 A-S 모델의 핵심 해법

A-S 모델은 두 가지 수식으로 재고 리스크를 관리한다:

**Reservation Price (기준가격):**
```
r(t) = s - q × γ × σ² × (T - t)
```
- 재고 q > 0 (롱): 기준가격을 mid보다 낮게 → 매도 유도
- 재고 q < 0 (숏): 기준가격을 mid보다 높게 → 매수 유도

**Optimal Spread:**
```
spread = γσ²(T-t) + (2/γ) × ln(1 + γ/k)
```
- 첫째 항: 재고 리스크 보상
- 둘째 항: 체결확률 감소 보정

### 1.4 A-S 모델의 철학

> **"체결확률을 높이는 공격적 호가 제시"와 "재고 리스크를 줄이는 보수적 재고관리" 사이의 균형**

A-S 전략은 "최대 수익"보다 **"위험 조정 후 안정적인 market making"**에 초점을 맞춘다.

---

## 2. 옵션 MM 적용 시 핵심 변경점

### 2.1 재고 단위: 계약 수 → 델타 노출량

**왜 델타인가?**

| 구분 | 기초자산 MM | 옵션 MM |
|------|------------|---------|
| 재고 1계약 | = 1단위 방향성 노출 | ≠ 1단위 방향성 노출 |
| 실제 리스크 | 계약 수 | **계약 수 × 델타** |

**예시:**
- 콜옵션 10계약 숏 (델타 0.5) → 지수 1pt 상승 시 → **5** × 승수 손실
- 콜옵션 10계약 숏 (델타 0.8) → 지수 1pt 상승 시 → **8** × 승수 손실
- **같은 10계약이라도 델타에 따라 리스크가 완전히 다름**

**수정된 재고 정의:**
```
q_Δ = Σ(계약 수 × 델타)
```

q_Δ가 의미하는 것:
- q_Δ = +2 → "선물 2계약 롱과 동일한 방향성 노출"
- q_Δ = -3 → "선물 3계약 숏과 동일한 방향성 노출"

### 2.2 델타의 동적 특성

**핵심: 거래 없이도 델타(재고)가 실시간으로 변동한다**

이것이 옵션 MM이 기초자산 MM보다 복잡한 근본적 이유이다.

| 변동 요인 | 효과 | 설명 |
|----------|------|------|
| 기초자산 가격 변동 | **Gamma Effect** | 지수가 움직이면 델타가 변함 |
| 시간 경과 | Charm Effect | 만기가 가까워지면 ATM 델타는 0.5로, ITM/OTM은 1/0으로 수렴 |
| IV 변화 | Vanna Effect | 변동성이 변하면 델타도 변함 |

**실무적 의미:**
- 1시간 전에 델타 중립이었던 포지션이 지금은 델타 +3일 수 있음
- 따라서 재고 관리 시스템은 **실시간 델타 모니터링**이 필수

### 2.3 재고 관리 방식: Inventory Rebalancing (델타 헷징 X)

**본 프로젝트의 핵심 설계 결정:**

> 델타 헷징(선물 매매)을 하지 않고, **순수하게 옵션 호가 조절만으로 포지션을 관리**한다.

**Inventory Rebalancing 방식:**

| 제어 수단 | 방법 |
|----------|------|
| Reservation Price 조절 | 델타 노출 방향 반대로 기준가격 이동 |
| Spread 조절 | 리스크 상황에 따라 스프레드 확대/축소 |
| 호가 수량 조절 | 체결 유도 방향의 수량 증가 |

**이 방식의 장점:**
- 순수 마켓메이킹 수익 구조 유지
- 헷징 비용(슬리피지, 수수료) 없음
- A-S 모델의 원래 철학과 일치

**이 방식의 리스크:**

⚠️ **Trending Market 리스크**
- 시장이 한 방향으로 지속 이동 시, 역방향 체결이 어려워 손실 누적 가능
- 강한 추세장에서는 inventory가 계속 쌓일 수 있음
- 이를 완화하기 위해 γ(위험민감도)의 동적 조절 필요 → 강화학습 적용

### 2.4 시간지평의 재정의

| 원논문 | 본 프로젝트 |
|--------|------------|
| T = 옵션 만기 | T = **당일 장 마감** |

**이유:**
- 실제 LP는 옵션 만기까지 재고를 들고 가지 않음
- 장중 또는 장마감 전에 재고 정리
- (T - t)는 "당일 inventory exposure를 얼마나 더 안고 가야 하는가"를 의미

---

## 3. 수정된 모델 수식

### 3.1 상태변수

| 기호 | 의미 |
|------|------|
| S_t | KOSPI200 지수 가격 |
| M_t | ATM 옵션의 mid-price |
| q_t^{opt} | 옵션 계약 재고 |
| Δ_t | ATM 옵션의 현재 델타 |
| X_t | 현금 계정 (P&L) |
| t | 현재 시각 |

**핵심 상태변수: 순델타 노출**
```
q_Δ = q_t^{opt} × Δ_t
```

### 3.2 Reservation Price

**원논문:**
```
r(t) = s - q × γσ²(T - t)
```

**옵션 MM 적용:**
```
r(t) = M_t - q_Δ × γ × σ²(T_close - t)
```

| 기호 | 의미 |
|------|------|
| M_t | 옵션 현재 mid-price |
| q_Δ | 순델타 노출 |
| γ | 위험민감도 (risk aversion) |
| σ | 기초자산 변동성 |
| T_close - t | 장 마감까지 남은 시간 |

**해석:**
- q_Δ > 0 (롱 델타): 기준가격↓ → 옵션 매도 유도
- q_Δ < 0 (숏 델타): 기준가격↑ → 옵션 매수 유도

### 3.3 Spread

```
spread = γσ²(T - t) + (2/γ) × ln(1 + γ/k)
```

- 원논문 구조 유지
- k: 호가 민감도 파라미터 (체결강도 감소 속도)

### 3.4 호가 배치

```
p_bid = r(t) - δ_bid
p_ask = r(t) + δ_ask
```

여기서 δ_bid + δ_ask = spread

---

## 4. 강화학습 기반 개선 (Alpha-AS 참조)

### 4.1 배경: Alpha-AS 논문

> "A reinforcement learning approach to improve the performance of the Avellaneda-Stoikov market-making algorithm"

Alpha-AS는 A-S 모델의 파라미터를 **강화학습(Double DQN)**으로 동적 조절하여 성능을 개선한다.

### 4.2 조절 대상

| 파라미터 | 역할 | 조절 효과 |
|----------|------|----------|
| **γ (위험민감도)** | inventory penalty 강도 | 높으면 보수적, 낮으면 공격적 |
| **skew** | bid/ask 비대칭 정도 | 체결 방향 유도 강도 |

**본 프로젝트 적용:**
- 시장 상황에 따라 γ를 동적으로 조절
- Trending market에서는 γ↑ (보수적)
- Range-bound market에서는 γ↓ (공격적)

### 4.3 State Features

| 카테고리 | Feature | 설명 |
|----------|---------|------|
| **Private** | q_Δ (델타 재고) | 현재 방향성 노출 |
| | Score (P&L) | 누적 손익 |
| **Market** | Microprice | 호가잔량 가중 mid-price |
| | Imbalance | 매수/매도 잔량 불균형 |
| | 체결방향 | 최근 체결이 BUY/SELL 주도인지 |
| | 1초체결량 | 단기 거래 강도 |

**Microprice 계산:**
```
Microprice = (AskQty₁ × BidPrice₁ + BidQty₁ × AskPrice₁) / (AskQty₁ + BidQty₁)
```

**Imbalance 계산:**
```
Imbalance = (ΣBidQty - ΣAskQty) / (ΣBidQty + ΣAskQty)
```
- Imbalance > 0: 매수 압력 우세
- Imbalance < 0: 매도 압력 우세

### 4.4 Reward Function: Asymmetric Dampened P&L

Alpha-AS에서 제안한 보상 함수:

```
R = sign(ΔP&L) × |ΔP&L|^η
```

| 파라미터 | 값 | 효과 |
|----------|---|------|
| η (dampening) | 0.5 | 큰 손익의 영향 감소 |
| Asymmetric | 손실 가중치 ↑ | 손실에 더 민감하게 반응 |

**목적:** 안정적인 수익 추구, 큰 손실 회피

### 4.5 Action Cycle

- **5초 단위**로 action 결정 (Alpha-AS 기준)
- 매 cycle마다 γ, skew 조절 여부 결정

---

## 5. 데이터 수집 설계

### 5.1 수집 주기

**1초 스냅샷 방식 채택**

| 근거 | 설명 |
|------|------|
| ATM 옵션 체결 빈도 | 약 2-5회/초 (평균) |
| 데이터 크기 | 1시간 ≈ 3,600행 (관리 가능) |
| 분석 해상도 | 초 단위 체결 패턴 분석 가능 |

### 5.2 수집 항목

**기본 데이터:**

| 카테고리 | 항목 |
|----------|------|
| 옵션 시세 | 현재가, 체결시간, 누적거래량 |
| 옵션 Greeks | IV, 델타, 감마, 세타, 베가, 로 |
| 옵션 호가 | 매수/매도 호가 1~5단계, 잔량 |
| 지수 | KOSPI200 현재가, 등락률, 거래량 |

### 5.3 파생 컬럼 (실시간 계산)

| 컬럼명 | 계산 방법 | 용도 |
|--------|----------|------|
| **1초체결량** | 현재 누적거래량 - 이전 누적거래량 | 단기 거래 강도 |
| **체결방향** | 체결가 vs 호가 비교 | 매수/매도 주도 판단 |
| **매수주도체결량** | 체결방향=BUY일 때 1초체결량 | 매수 압력 측정 |
| **매도주도체결량** | 체결방향=SELL일 때 1초체결량 | 매도 압력 측정 |

**체결방향 판단 로직:**
```
if 체결가 >= 매도호가1:
    direction = 'BUY'   # 매수 주도 (시장가 매수)
elif 체결가 <= 매수호가1:
    direction = 'SELL'  # 매도 주도 (시장가 매도)
else:
    direction = 'MID'   # 중간 가격 체결
```

### 5.4 향후 추가 예정 컬럼

| 컬럼명 | 계산 방법 |
|--------|----------|
| Microprice | 호가잔량 가중 mid-price |
| Imbalance | (ΣBid - ΣAsk) / (ΣBid + ΣAsk) |
| Spread | 매도호가1 - 매수호가1 |

---

## 6. 최종 정리

### 한 문장 요약

> **A-S 모델의 Reservation Price + Spread 구조를 유지하되, 재고 단위를 델타 노출량으로 변경하고, 델타 헷징 없이 순수 Inventory Rebalancing 방식으로 포지션을 관리하며, 강화학습을 통해 위험민감도(γ)를 동적으로 조절한다.**

### 원논문 vs 본 프로젝트 비교

| 항목 | 원논문 (A-S) | 본 프로젝트 |
|------|-------------|------------|
| 대상 자산 | 단일 주식 | KOSPI200 ATM 옵션 |
| 재고 정의 | 계약 수 q | **델타 노출량 q_Δ** |
| 재고 특성 | 거래 시에만 변동 | **실시간 변동 (Gamma effect)** |
| 재고 관리 | 호가 조절 | **호가 조절만 (헷징 X)** |
| 파라미터 | 고정 γ | **RL 기반 동적 γ** |
| 시간지평 | 옵션 만기 | **당일 장 마감** |
| Mid price | 시장 mid | **실제 체결 기반 + IV 반영** |

### 핵심 리스크 인지

| 리스크 | 설명 | 대응 |
|--------|------|------|
| Trending Market | 한 방향 추세 시 inventory 누적 | γ 동적 증가 (RL) |
| Dynamic Delta | 거래 없이 재고 변동 | 실시간 델타 모니터링 |
| Low Liquidity | 체결 지연으로 rebalancing 실패 | Spread 확대 |

---

## 참고문헌

1. **Avellaneda, M., & Stoikov, S. (2008)**
   - "High-frequency trading in a limit order book"
   - Quantitative Finance, 8(3), 217-224

2. **Falces, G., et al. (2023)**
   - "A reinforcement learning approach to improve the performance of the Avellaneda-Stoikov market-making algorithm"

3. **KRX 자료**
   - [주가지수옵션 상품명세](https://open.krx.co.kr/contents/OPN/01/01040202/OPN01040202.jsp)
   - [시장조성자 법적 의무](https://rule.krx.co.kr/out/index.do)

4. **기타 참고**
   - [Market Making & Inventory Management Guide](https://www.marketcalls.in/market-microstructure/understanding-market-making-inventory-management-a-traders-guide.html)

---

*Last Updated: 2026-03-23*
