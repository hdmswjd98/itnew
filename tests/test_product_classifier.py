"""품목 분류기의 핵심 도메인 규칙 회귀 테스트."""

import unittest

from services.product.classifier import classify_item


class ProductClassifierTest(unittest.TestCase):
    def test_kimchi_abbreviations(self):
        for item in ["포기5", "맛10", "겉절이2", "포기2+총각1", "신나는(2단)3"]:
            with self.subTest(item=item):
                self.assertEqual(classify_item(item), ("식품", "김치류"))

    def test_business_specific_categories(self):
        cases = {
            "포장박스1개": ("포장재", "포장용품"),
            "국,반찬": ("식품", "가공식품"),
            "한약 1상자": ("건강식품", "한약"),
            "제주 옥돔": ("신선식품", "수산물"),
            "신선갈치": ("신선식품", "수산물"),
            "제주 고등어살 1kg": ("신선식품", "수산물"),
            "동아오츠카 포카리스웨트 240ml": ("음료", "음료"),
            "동아오츠카 데미소다 애플 250ml": ("음료", "음료"),
            "Linevassa Carbonated Water 500ml": ("음료", "음료"),
            "무지개망고 5kg": ("신선식품", "과일"),
            "표고버섯": ("신선식품", "채소"),
            "수산물": ("신선식품", "수산물"),
            "주류": ("음료", "주류"),
            "도서": ("도서/문구", "도서"),
        }
        for item, expected in cases.items():
            with self.subTest(item=item):
                self.assertEqual(classify_item(item), expected)

    def test_water_does_not_match_order_goods(self):
        self.assertNotEqual(classify_item("의료창고 주문물품"), ("음료", "생수"))
        self.assertEqual(classify_item("물"), ("음료", "생수"))

    def test_unknown_operational_values_stay_unclassified(self):
        for item in ["미상", ".", "-", "반품"]:
            with self.subTest(item=item):
                self.assertEqual(classify_item(item), ("기타", "기타"))


if __name__ == "__main__":
    unittest.main()
