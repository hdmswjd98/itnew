"""품목 정규화·분류·분석 서비스."""

from .normalizer import normalize_item_name


def classify_item(item_name):
    """분류 모듈을 필요할 때 불러와 패키지 실행 경고를 피한다."""
    from .classifier import classify_item as _classify_item

    return _classify_item(item_name)


__all__ = ["classify_item", "normalize_item_name"]
