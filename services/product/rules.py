"""기업별 품목 분류 규칙을 CSV에서 불러온다."""

from functools import lru_cache
import re

import pandas as pd

from shared.paths import CONFIG_DIR


RULES_PATH = CONFIG_DIR / "product_classification_rules.csv"
REQUIRED_COLUMNS = {"우선순위", "사용", "일치방식", "키워드", "대분류", "중분류"}


@lru_cache(maxsize=1)
def load_company_rules():
    """활성화된 기업 규칙을 우선순위 순서로 반환한다."""
    if not RULES_PATH.exists():
        return ()

    rules = pd.read_csv(RULES_PATH, dtype=str).fillna("")
    missing = REQUIRED_COLUMNS - set(rules.columns)
    if missing:
        raise ValueError(f"기업 품목 분류 규칙에 필수 컬럼이 없습니다: {sorted(missing)}")

    rules = rules[rules["사용"].str.strip().str.upper().isin({"Y", "YES", "TRUE", "1"})].copy()
    rules["우선순위"] = pd.to_numeric(rules["우선순위"], errors="coerce").fillna(999999)
    rules = rules.sort_values("우선순위", kind="stable")
    return tuple(rules.to_dict("records"))


def match_company_rule(item_name):
    """품목명과 처음 일치하는 기업 규칙의 카테고리를 반환한다."""
    for rule in load_company_rules():
        keyword = str(rule["키워드"]).strip().lower()
        match_type = str(rule["일치방식"]).strip()
        if not keyword:
            continue
        if match_type == "정확히":
            matched = item_name == keyword
        elif match_type == "정규식":
            matched = re.search(keyword, item_name) is not None
        else:
            matched = keyword in item_name
        if matched:
            return str(rule["대분류"]).strip(), str(rule["중분류"]).strip()
    return None


def reload_company_rules():
    """CSV 수정 후 캐시를 비워 다음 분류부터 새 규칙을 사용한다."""
    load_company_rules.cache_clear()


def save_exact_rule(item_name, main_category, subcategory):
    """수기 검토 결과를 품목명 정확히 일치 규칙으로 저장한다."""
    save_exact_rules([item_name], main_category, subcategory)


def save_exact_rules(item_names, main_category, subcategory):
    """여러 품목의 수기 검토 결과를 하나의 카테고리로 일괄 저장한다."""
    main_category = str(main_category).strip()
    subcategory = str(subcategory).strip()
    item_names = list(dict.fromkeys(str(item).strip() for item in item_names if str(item).strip()))
    if not item_names or not main_category or not subcategory:
        raise ValueError("품목명, 대분류, 중분류를 모두 입력해주세요.")

    if RULES_PATH.exists():
        rules = pd.read_csv(RULES_PATH, dtype=str).fillna("")
    else:
        rules = pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    for item_name in item_names:
        values = {
            "우선순위": "1",
            "사용": "Y",
            "일치방식": "정확히",
            "키워드": item_name,
            "대분류": main_category,
            "중분류": subcategory,
        }
        same_item = (
            rules["일치방식"].eq("정확히")
            & rules["키워드"].str.strip().str.lower().eq(item_name.lower())
        )
        if same_item.any():
            for column, value in values.items():
                rules.loc[same_item, column] = value
        else:
            rules = pd.concat([pd.DataFrame([values]), rules], ignore_index=True)

    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = RULES_PATH.with_suffix(".tmp")
    rules.to_csv(temporary_path, index=False, encoding="utf-8-sig")
    temporary_path.replace(RULES_PATH)
    reload_company_rules()
