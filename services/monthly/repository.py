"""SQLite 기반 월별 운영보고서 저장소."""

import json
import sqlite3
from pathlib import Path

from shared.paths import OUTPUT_DIR


DATABASE_PATH = OUTPUT_DIR / "monthly_reports.db"


class ReportStoreError(RuntimeError):
    """월간보고서 저장소 접근 실패."""


class MonthlyReportStore:
    def __init__(self, database_path=DATABASE_PATH):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        try:
            with self._connect() as connection:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS monthly_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_month TEXT NOT NULL UNIQUE,
                        current_sales INTEGER NOT NULL DEFAULT 0,
                        previous_sales INTEGER NOT NULL DEFAULT 0,
                        issues TEXT NOT NULL DEFAULT '[]',
                        actions TEXT NOT NULL DEFAULT '[]',
                        results TEXT NOT NULL DEFAULT '[]',
                        next_month_plan TEXT NOT NULL DEFAULT '',
                        partner_requests TEXT NOT NULL DEFAULT '',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except sqlite3.Error as error:
            raise ReportStoreError(f"월간보고서 DB를 초기화하지 못했습니다: {error}") from error

    @staticmethod
    def _deserialize(row):
        if row is None:
            return None
        report = dict(row)
        for field in ["issues", "actions", "results"]:
            report[field] = json.loads(report.get(field) or "[]")
        return report

    def get(self, report_month):
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM monthly_reports WHERE report_month = ?", (report_month,)
                ).fetchone()
            return self._deserialize(row)
        except (sqlite3.Error, json.JSONDecodeError) as error:
            raise ReportStoreError(f"{report_month} 보고서를 불러오지 못했습니다: {error}") from error

    def list_months(self):
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT report_month FROM monthly_reports ORDER BY report_month DESC"
                ).fetchall()
            return [row["report_month"] for row in rows]
        except sqlite3.Error as error:
            raise ReportStoreError(f"저장된 보고서 목록을 불러오지 못했습니다: {error}") from error

    def save(self, payload):
        values = dict(payload)
        for field in ["issues", "actions", "results"]:
            values[field] = json.dumps(values.get(field, []), ensure_ascii=False)
        try:
            with self._connect() as connection:
                connection.execute("""
                    INSERT INTO monthly_reports (
                        report_month, current_sales, previous_sales, issues, actions, results,
                        next_month_plan, partner_requests
                    ) VALUES (
                        :report_month, :current_sales, :previous_sales, :issues, :actions, :results,
                        :next_month_plan, :partner_requests
                    )
                    ON CONFLICT(report_month) DO UPDATE SET
                        current_sales = excluded.current_sales,
                        previous_sales = excluded.previous_sales,
                        issues = excluded.issues,
                        actions = excluded.actions,
                        results = excluded.results,
                        next_month_plan = excluded.next_month_plan,
                        partner_requests = excluded.partner_requests,
                        updated_at = CURRENT_TIMESTAMP
                """, values)
            return self.get(values["report_month"])
        except sqlite3.Error as error:
            raise ReportStoreError(f"보고서를 저장하지 못했습니다: {error}") from error


def get_report_store():
    return MonthlyReportStore()
