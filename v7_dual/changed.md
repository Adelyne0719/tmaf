# 변경 사항 (2026-03-01)

## 1. 헷지 프로토콜 BE 안전 조건 기준 변경

### 배경
기존에는 BE를 안전망 가격(safety_price)과 직접 비교하여 프로토콜 발동 여부를 판단했으나, 익절 수량 비율(tp_ratio)을 반영하지 않아 실제 필요한 상황에서 활성화되지 않는 문제 발생.

### 변경 내용 (`v7_dual_auto_trader.py`) — 3곳

**기준 변경**: 안전망 가격 직접 비교 → 메인 평균가와 안전망 가격의 익절비율(tp_ratio)% 지점과 비교

```python
# 수정 전
be_needs_fix = current_be > safety_price if self.side_mode == "LONG" else current_be < safety_price

# 수정 후
tp_ratio = self.hedge_protocol_tp_ratio / 100.0
if self.side_mode == "LONG":
    threshold = main_avg_price + (safety_price - main_avg_price) * tp_ratio
else:
    threshold = main_avg_price - (main_avg_price - safety_price) * tp_ratio
be_needs_fix = current_be > threshold if self.side_mode == "LONG" else current_be < threshold
```

### 예시 (SHORT, tp_ratio=50%)
| 항목 | 값 |
|------|------|
| 메인 평균가 | $1.3248 |
| 안전망 가격 | $1.2918 |
| 기준가 (50%) | $1.3083 |
| 현재 BE | $1.2983 |
| 결과 | BE < 기준가 → 활성화 |

> 기존 로직에서는 BE($1.2983) > 안전망($1.2918) 이므로 미충족이었으나, 변경 후 BE($1.2983) < 기준가($1.3083) 이므로 정상 활성화됨.

| 위치 | 용도 |
|------|------|
| H1 체결 | 프로토콜 최초 활성화 검사 |
| H2/H3 체결 | 재활성화 검사 |
| 되돌림 도달 | 익절 전 BE 안전성 재검사 |
