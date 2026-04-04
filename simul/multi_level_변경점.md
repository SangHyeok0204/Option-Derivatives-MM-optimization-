# Multi-Level Quoting 변경점

## 1. DevelopConfig

n_levels (int, 기본값 3)과 tick_size (float, 기본값 0.05) 두 파라미터를 추가했다.
나머지 파라미터는 변경 없다.


## 2. SimulationState

bid_fill, ask_fill의 타입을 bool에서 int로 변경했다. 체결된 레벨 수를 기록한다.
bid_levels_detail, ask_levels_detail (str)을 추가했다. 레벨별 체결 여부를 "1,1,0" 형태로 기록한다.


## 3. run_develop_simulation

변경은 체결 판정 부분에만 있다. RP/Spread 계산은 기존과 동일하다.

(1) 호가 생성: Level 0(best) 기준으로 tick 단위로 n_levels개 호가를 깐다.
    bid_levels[i] = bid - i * tick_size
    ask_levels[i] = ask + i * tick_size

(2) 체결 판정: 각 레벨의 delta를 계산해서 기존 compute_fill_probability_develop에 넣는다.
    바깥 레벨일수록 delta가 커서 체결 확률이 자연스럽게 낮아진다.

(3) Sweep 보정: 바깥 레벨이 체결됐으면 안쪽 레벨도 강제 체결한다.
    (Level 2 체결 → Level 0, 1도 체결)

(4) 체결 가격: 각 레벨은 자기 호가 가격으로 체결. delta ≤ 0이면 mid price.

(5) 재고/현금: 기존 ±1 대신 체결된 레벨 수만큼 반영한다.
