"""
잇뉴 고객 분석 파이프라인 — 마스터 실행 스크립트
팀원 노트북에서 다음 명령어로 전체 파이프라인을 실행:
    python analysis/run_pipeline.py

파이프라인 단계:
  1. 데이터 로드 및 검증 (data-validator)
  2. 데이터 병합 (data-merger)
  3. 고객별 지표 계산 (metrics-calculator)
  4. 이탈 위험 점수 산정 (churn-risk-scorer)
  5. 고객군 분류 (customer-classifier)
  6. 패턴 분석 (pattern-analyzer)
  7. 최종 검증 (validation-suite)
  8. 보고서 생성 (dashboard-formatter)
"""

import sys
from pathlib import Path

# 파이프라인 모듈을 같은 디렉토리에서 임포트
sys.path.insert(0, str(Path(__file__).parent))

from validate import run_validation as step1_validate
from load_data import load_data as step2_load
from merge_data import merge_data as step3_merge
from calc_metrics import calc_metrics as step4_metrics
from score_churn import score_churn as step4_churn
from classify import classify_groups as step5_classify
from analyze_patterns import analyze_patterns as step6_pattern
from run_validation import run_validation as step7_validate
from build_report import build_report as step8_report

# 작업 디렉토리 (스크립트가 있는 디렉토리 = analysis/)
WORKSPACE = Path(__file__).parent


def run_pipeline():
    """파이프라인 전체 실행"""
    print("=" * 60)
    print("🏢 잇뉴 고객 분석 파이프라인")
    print("=" * 60)
    print(f"작업 디렉토리: {WORKSPACE.absolute()}")
    print(f"실행 시각: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 파이프라인 각 단계 실행
    steps = [
        ("1. 데이터 검증", step1_validate),
        ("2. 데이터 로드", step2_load),
        ("3. 데이터 병합", step3_merge),
        ("4. 고객별 지표 계산", step4_metrics),
        ("5. 이탈 위험 점수 산정", step4_churn),
        ("6. 고객군 분류", step5_classify),
        ("7. 패턴 분석", step6_pattern),
        ("8. 최종 검증", step7_validate),
        ("9. 보고서 생성", step8_report),
    ]

    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"▶ {step_name} 실행 중...")
        print(f"{'='*60}")
        try:
            step_func()
            print(f"✅ {step_name} 완료")
        except Exception as e:
            print(f"❌ {step_name} 실패: {e}")
            print("파이프라인을 중단합니다.")
            sys.exit(1)

    print(f"\n{'='*60}")
    print("🎉 파이프라인 전체 완료!")
    print(f"{'='*60}")
    print("\n생성된 산출물:")
    print("  - validation_results.csv     (데이터 검증 결과)")
    print("  - invalid_records.csv        (제외 데이터)")
    print("  - valid_orders_raw.csv       (유효 주문 데이터)  ← 2단계 로드에서 생성")
    print("  - merged_data.csv            (통합 데이터셋)")
    print("  - customer_metrics.csv       (고객별 이용 지표)")
    print("  - churn_scores.csv           (이탈 위험 점수)")
    print("  - customer_groups.csv        (고객군 분류 결과)")
    print("  - churn_risk_customers.csv   (이탈 위험 고객 목록)")
    print("  - group_counts.csv           (고객군별 인원)")
    print("  - region_analysis.csv        (지역 특성)")
    print("  - industry_analysis.csv      (업종 특성)")
    print("  - product_analysis.csv       (품목 분석)")
    print("  - ai_summary.txt             (AI 분석 요약)")
    print("  - validation_final.csv       (최종 검증 결과)")
    print("  - customer_analysis_result.md (최종 보고서)")
    print("\n대시보드 실행:")
    print("  streamlit run streamlit_dashboard.py")
    print(f"  → http://localhost:8501")


if __name__ == "__main__":
    run_pipeline()
