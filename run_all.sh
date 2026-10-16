#!/usr/bin/env bash
# [M10 / WBS 2.5] Isaac Sim · Isaac Lab 설치 검토 테스트 일괄 실행
#
# 사용법:
#   ./run_all.sh              # GUI 창을 띄우며 순서대로 실행
#   ./run_all.sh --headless   # 창 없이 점검만 (원격 접속 · 자동 점검용)

set -u

ISAACLAB_PATH="${ISAACLAB_PATH:-/data/src/isaaclab}"
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEADLESS=""
[ "${1:-}" = "--headless" ] && HEADLESS="--headless"

PASS_COUNT=0
FAIL_COUNT=0
declare -a SUMMARY

run_step() {
    local title="$1"; shift
    echo ""
    echo "######################################################################"
    echo "# ${title}"
    echo "######################################################################"
    if "$@"; then
        SUMMARY+=("PASS  ${title}")
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        SUMMARY+=("FAIL  ${title}")
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# [00] 설치 경로 · GPU · 버전 사전 점검 (시스템 python3, 수 초)
run_step "[00] 설치 사전 점검" python3 "${TEST_DIR}/test_00_env_check.py"

# 사전 점검이 실패하면 이후 단계는 반드시 실패하므로 여기서 중단한다.
if [ "${FAIL_COUNT}" -ne 0 ]; then
    echo ""
    echo ">>> 사전 점검 실패. Isaac Sim / Isaac Lab 설치를 먼저 완료할 것."
    exit 1
fi

# [01] Isaac Sim 단독 (Isaac Sim 의 python.sh 로 실행)
run_step "[01] Isaac Sim 단독 동작" \
    "${ISAACLAB_PATH}/_isaac_sim/python.sh" "${TEST_DIR}/test_01_isaac_sim.py" ${HEADLESS}

# [02] Isaac Lab 물리 시뮬레이션 (isaaclab.sh -p 로 실행)
run_step "[02] Isaac Lab 물리 시뮬레이션" \
    "${ISAACLAB_PATH}/isaaclab.sh" -p "${TEST_DIR}/test_02_isaac_lab_sim.py" ${HEADLESS}

# [03] Isaac Lab 강화학습 환경
run_step "[03] Isaac Lab 강화학습 환경" \
    "${ISAACLAB_PATH}/isaaclab.sh" -p "${TEST_DIR}/test_03_isaac_lab_env.py" ${HEADLESS}

echo ""
echo "######################################################################"
echo "# 최종 결과"
echo "######################################################################"
for line in "${SUMMARY[@]}"; do
    echo "  ${line}"
done
echo "----------------------------------------------------------------------"
echo "  통과 ${PASS_COUNT}건 · 실패 ${FAIL_COUNT}건"
if [ "${FAIL_COUNT}" -eq 0 ]; then
    echo "  >>> Isaac Sim / Isaac Lab 설치 검증 완료. M10 시연 가능."
else
    echo "  >>> 실패 항목 있음. 위 로그 확인 후 재실행할 것."
fi
echo "######################################################################"

exit "${FAIL_COUNT}"
