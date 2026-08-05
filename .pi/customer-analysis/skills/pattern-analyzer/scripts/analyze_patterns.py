"""대시보드에서 사용하는 최신 패턴 분석 코드를 실행한다."""

from pathlib import Path
import runpy
import sys


ANALYSIS_DIR = Path(__file__).resolve().parents[4] / "dashboards" / "customer" / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))
runpy.run_path(str(ANALYSIS_DIR / "analyze_patterns.py"), run_name="__main__")
