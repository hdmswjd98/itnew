"""
품목별 수요 분석기
product_classification 결과를 기반으로 품목별 수요 분석을 수행합니다.

사용법:
    python product_analyzer.py
"""

import pandas as pd
from pathlib import Path


def analyze_products():
    """품목별 수요 분석 실행"""
    workspace = Path(__file__).parent
    output_dir = workspace / "output"
    output_dir.mkdir(exist_ok=True)

    # 1. 분류 결과 로드
    classification_path = output_dir / "product_classification.csv"
    if not classification_path.exists():
        print("[ERROR] product_classification.csv 를 찾을 수 없습니다.")
        print("  먼저 product_classifier.py 를 실행해주세요.")
        return

    product_df = pd.read_csv(classification_path, dtype=str)
    print(f"📊 품목 분류 결과 로드: {len(product_df)}건")

    # 2. 대분류별 요약
    category_summary = product_df.groupby("대분류").agg(
        주문_건수=("order_id", "count"),
        고유_고객수=("customer_id", "nunique"),
        고유_품목수=("item_name", "nunique"),
        중분류수=("중분류", "nunique")
    ).reset_index()
    category_summary["비율"] = (category_summary["주문_건수"] / category_summary["주문_건수"].sum() * 100).round(1)
    category_summary.to_csv(output_dir / "category_summary.csv", index=False, encoding="utf-8-sig")
    print(f"\n📈 대분류별 요약:")
    print(category_summary.to_string(index=False))
    print(f"  저장: output/category_summary.csv")

    # 3. 중분류별 요약
    subcategory_summary = product_df.groupby(["대분류", "중분류"]).agg(
        주문_건수=("order_id", "count"),
        고유_고객수=("customer_id", "nunique"),
        고유_품목수=("item_name", "nunique")
    ).reset_index()
    subcategory_summary["비율"] = (subcategory_summary["주문_건수"] / subcategory_summary["주문_건수"].sum() * 100).round(1)
    subcategory_summary.to_csv(output_dir / "subcategory_summary.csv", index=False, encoding="utf-8-sig")
    print(f"\n📈 중분류별 요약:")
    print(subcategory_summary.to_string(index=False))
    print(f"  저장: output/subcategory_summary.csv")

    # 4. 상위 품목 분석
    top_products = product_df.groupby("item_name").agg(
        주문_건수=("order_id", "count"),
        고유_고객수=("customer_id", "nunique"),
        대분류=("대분류", "first"),
        중분류=("중분류", "first")
    ).reset_index()
    top_products = top_products.sort_values("주문_건수", ascending=False)
    top_products["비율"] = (top_products["주문_건수"] / top_products["주문_건수"].sum() * 100).round(1)
    top_products.to_csv(output_dir / "top_products.csv", index=False, encoding="utf-8-sig")
    print(f"\n🏆 Top 10 품목:")
    print(top_products.head(10).to_string(index=False))
    print(f"  저장: output/top_products.csv")

    # 5. 고객군 연계 분석 (customer_groups.csv 가 있으면)
    groups_path = workspace / "customer_groups.csv"
    demand_analysis_path = output_dir / "product_demand_analysis.csv"

    if groups_path.exists():
        groups = pd.read_csv(groups_path, dtype=str)
        analysis_data = product_df.merge(groups[["customer_id", "고객군"]], on="customer_id", how="left")

        # 대분류 × 고객군
        demand_by_group = analysis_data.groupby(["대분류", "고객군"]).agg(
            주문_건수=("order_id", "count"),
            고유_고객수=("customer_id", "nunique")
        ).reset_index()
        demand_by_group["비율"] = demand_by_group.groupby("대분류")["주문_건수"].transform(
            lambda x: (x / x.sum() * 100).round(1)
        )
        demand_by_group.to_csv(demand_analysis_path, index=False, encoding="utf-8-sig")
        print(f"\n📊 대분류 × 고객군 수요 분석:")
        print(demand_by_group.to_string(index=False))
        print(f"  저장: output/product_demand_analysis.csv")

        # 중분류 × 고객군
        demand_sub = analysis_data.groupby(["중분류", "고객군"]).agg(
            주문_건수=("order_id", "count"),
            고유_고객수=("customer_id", "nunique")
        ).reset_index()
        demand_sub["비율"] = demand_sub.groupby("중분류")["주문_건수"].transform(
            lambda x: (x / x.sum() * 100).round(1)
        )
        demand_sub.to_csv(output_dir / "product_demand_subcategory.csv", index=False, encoding="utf-8-sig")
        print(f"\n📊 중분류 × 고객군 수요 분석:")
        print(demand_sub.to_string(index=False))
        print(f"  저장: output/product_demand_subcategory.csv")

    else:
        # customer_groups.csv 가 없으면 기본 분석만
        product_df.to_csv(demand_analysis_path, index=False, encoding="utf-8-sig")
        print(f"\n📊 품목별 기본 분석 (고객군 연계 없음):")
        print(product_df.head(10).to_string(index=False))
        print(f"  저장: output/product_demand_analysis.csv")

    # 6. 전체 결과 요약
    print(f"\n{'='*60}")
    print(f"🎉 품목별 수요 분석 완료!")
    print(f"{'='*60}")
    print(f"  생성 파일:")
    print(f"    - output/category_summary.csv")
    print(f"    - output/subcategory_summary.csv")
    print(f"    - output/top_products.csv")
    print(f"    - output/product_demand_analysis.csv")
    print(f"    - output/product_demand_subcategory.csv (고객군 연계 시)")


if __name__ == "__main__":
    analyze_products()
