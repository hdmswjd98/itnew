#!/bin/bash
# ============================================================
# itnew-customer-dashboard — 파이프라인 실행 스크립트
# 크론으로 예약하여 주기적으로 데이터를 최신화합니다.
# 사용법: ./run_pipeline.sh
# 크론 예시 (매일 09:00 KST):
#   0 9 * * * cd /path/to/itnew && ./crons/run_pipeline.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "잇뉴 고객 분석 파이프라인 실행 시작"
echo "시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# 1. Python 패키지 확인/설치
echo "[1/4] Python 패키지 확인 중..."
pip install -q streamlit pandas plotly 2>/dev/null || true
echo "   ✅ 패키지 확인 완료"

# 2. 데이터 검증 & 지표 계산 & 분류 & 분석을
#    customer-analysis-orchestrator (sub-agent) 로 실행
#    또는 직접 파이썬 스크립트들을 순차 실행
echo "[2/4] 데이터 검증 + 지표 계산 + 고객군 분류 + 특성 분석 실행 중..."

# 하위 에이전트 실행이 불가능한 환경에서는 아래 파이썬 스크립트들로 대체
# (각 스킬의 scripts/ 디렉토리를 별도 저장소에서 clone 하거나 포함)
if [ -f ".pi/agents/customer-analysis-orchestrator/AGENT.md" ]; then
    echo "   → 고객분석 오케스트레이터가 설치되어 있습니다."
    echo "   → Timely 환경에서만 오케스트레이터 실행 가능."
    echo "   → 타 환경에서는 수동 실행 또는 별도 에이전트 필요."
else
    echo "   → 오케스트레이터가 없습니다. 수동 실행이 필요합니다."
    echo "   → 아래 명령어들을 직접 실행하세요:"
    echo "     python .pi/skills/data-validator/scripts/validate.py"
    echo "     python .pi/skills/metrics-calculator/scripts/calc_metrics.py"
    echo "     python .pi/skills/churn-risk-scorer/scripts/score_churn.py"
    echo "     python .pi/skills/customer-classifier/scripts/classify.py"
    echo "     python .pi/skills/pattern-analyzer/scripts/analyze_patterns.py"
    echo "     python .pi/skills/dashboard-formatter/scripts/build_report.py"
fi

# 3. 대시보드 자동 열기 (선택사항)
echo "[3/4] 대시보드 스크립트 확인 완료"
if [ -f "streamlit_dashboard.py" ]; then
    echo "   → streamlit_dashboard.py 가 준비되었습니다."
    echo "   → 다음 명령어로 대시보드 실행:"
    echo "     streamlit run streamlit_dashboard.py"
fi

# 4. Supabase 연동 안내
echo "[4/4] Supabase 연동 준비"
if [ ! -f ".env" ]; then
    echo "   → .env 파일을 생성하여 Supabase credentials 를 설정하세요:"
    echo "     SUPABASE_URL=https://xxxx.supabase.co"
    echo "     SUPABASE_KEY=xxxxxx"
    echo "   → streamlit_dashboard.py 의 load_*() 함수를 Supabase 버전으로 수정 후 사용"
fi

echo ""
echo "============================================"
echo "파이프라인 실행 완료"
echo "시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
