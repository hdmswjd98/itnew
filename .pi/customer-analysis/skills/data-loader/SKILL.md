---
name: data-loader
description: [고객분석] 회원·주문·배송 CSV 파일을 workspace 에서 읽어들여 pandas DataFrame 으로 로드하고, 기본 구조와 결측 여부를 확인한다.
---
# 고객분석 영역
# 실제 실행 코드: services/customer/



## 목적
분석 파이프라인의 첫 단계로, members.csv / orders.csv / deliveries.csv / invalid_orders.csv 를 로드하고 각 파일의 컬럼명·행수·결측 현황을 확인한다.

## 사용 시점
파이프라인 시작 전, 또는 데이터 소스를 변경했을 때

## 실행 방법
```bash
python .pi/skills/data-loader/scripts/load_data.py
```

## 출력
- 콘솔: 각 파일의 컬럼명, 행수, 결측값 요약
- workspace 내 임시 로그는 남기지 않음 (프로세스 내부에서만 사용)
