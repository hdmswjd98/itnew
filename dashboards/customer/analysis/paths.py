"""프로젝트의 입력 및 출력 데이터 경로를 한곳에서 관리한다."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "input"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"


def ensure_data_dirs():
    """파이프라인 실행에 필요한 데이터 폴더를 생성한다."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
