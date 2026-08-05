"""품목명의 표기 차이를 줄이는 정규화 함수."""

import re
import unicodedata


def normalize_item_name(value):
    """품목명을 유니코드 NFC로 맞추고 불필요한 공백을 제거한다."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value)).strip().lower()
    return re.sub(r"\s+", " ", text)
