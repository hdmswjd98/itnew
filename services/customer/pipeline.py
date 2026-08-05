"""
잇뉴 고객 분석 파이프라인 — 마스터 실행 스크립트
팀원 노트북에서 다음 명령어로 전체 파이프라인을 실행:
    python3 -m services.customer.pipeline

파이프라인 단계:
  1. 실제 Excel 변환
  2. 상세주소 GPS 변환 (선택, API 키 없으면 생략)
  3. 데이터 검증 및 로드 (data-validator + data-loader 통합)
  4. 데이터 병합 (data-merger)
  5. 고객별 지표 계산 (metrics-calculator)
  6. 이탈 위험 점수 산정 (churn-risk-scorer)
  7. 고객군 분류 (customer-classifier)
  8. 패턴 분석 (pattern-analyzer)
  9. 최종 검증 (validation-suite)

과거 10단계 "보고서 생성"(build_report.py → customer_analysis_result.md)은 Next.js 대시보드
어디에서도 읽지 않는 산출물이라 파이프라인에서 제거했다. 필요해지면 build_report.py를
직접 실행해서 볼 수 있다 (services/customer/build_report.py, git 이력에 남아있음).
"""

import sys

from .analyze_patterns import analyze_patterns as step6_pattern
from .churn import score_churn as step4_churn
from .classify import classify_groups as step5_classify
from .import_real_data import import_real_data
from .geocode import geocode_orders
from .merge_data import merge_data as step3_merge
from .metrics import calc_metrics as step4_metrics
from .paths import INPUT_DIR, OUTPUT_DIR, ensure_data_dirs
from .run_validation import run_validation as step7_validate
from .validate_and_load import validate_and_load as step1_validate_and_load

def run_pipeline():
    """파이프라인 전체 실행"""
    ensure_data_dirs()
    print("=" * 60)
    print("🏢 잇뉴 고객 분석 파이프라인")
    print("=" * 60)
    print(f"입력 데이터: {INPUT_DIR}")
    print(f"출력 데이터: {OUTPUT_DIR}")
    print(f"실행 시각: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 파이프라인 각 단계 실행
    def geocode_step():
        try:
            return geocode_orders()
        except RuntimeError as error:
            if "KAKAO_REST_API_KEY" in str(error):
                print(f"⚠️ 상세주소 좌표 변환 생략: {error}")
                return None
            raise

    steps = [
        ("1. 실제 Excel 변환", import_real_data),
        ("2. 상세주소 GPS 변환", geocode_step),
        ("3. 데이터 검증 및 로드", step1_validate_and_load),
        ("4. 데이터 병합", step3_merge),
        ("5. 고객별 지표 계산", step4_metrics),
        ("6. 이탈 위험 점수 산정", step4_churn),
        ("7. 고객군 분류", step5_classify),
        ("8. 패턴 분석", step6_pattern),
        ("9. 최종 검증", step7_validate),
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
    print(f"\n생성된 산출물 ({OUTPUT_DIR}):")
    print("  - validation_results.csv     (데이터 검증 결과)")
    print("  - invalid_records.csv        (제외 데이터)")
    print("  - valid_orders_raw.csv       (유효 주문 데이터)  ← 3단계 검증·로드에서 생성")
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
    print("\n대시보드 실행:")
    print("  cd web && npm run dev")
    print(f"  → http://localhost:3000")


if __name__ == "__main__":
    run_pipeline()
