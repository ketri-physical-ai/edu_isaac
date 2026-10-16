#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[M10 / WBS 2.5] Isaac Sim · Isaac Lab 설치 사전 점검 (앱 실행 없음).

Isaac Sim GUI를 띄우기 전에, 설치 경로 · GPU 드라이버 · 버전만 빠르게 확인한다.
시스템 python3 로 실행되며 외부 패키지를 요구하지 않는다(수 초 내 완료).

사용법:
    python3 /data/src/test_code/test_00_env_check.py
"""

import os
import shutil
import subprocess
import sys

ISAACLAB_PATH = os.environ.get("ISAACLAB_PATH", "/data/src/isaaclab")

results: list[tuple[str, str, str]] = []


def record(name: str, status: str, detail: str = "") -> None:
    """점검 결과 1건을 기록하고 즉시 출력한다."""
    results.append((name, status, detail))
    print(f"  [{status:4s}] {name}" + (f" — {detail}" if detail else ""))


def run(cmd: list[str]) -> str:
    """명령을 실행하고 표준출력을 반환한다. 실패 시 빈 문자열."""
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def check_os() -> None:
    """Ubuntu 배포판 버전 확인 (교육 표준: 22.04 LTS)."""
    pretty = ""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    pretty = line.split("=", 1)[1].strip().strip('"')
    if not pretty:
        record("OS 확인", "FAIL", "/etc/os-release 를 읽을 수 없음")
    elif "22.04" in pretty:
        record("OS 확인", "PASS", pretty)
    else:
        record("OS 확인", "WARN", f"{pretty} (교육 표준은 Ubuntu 22.04 LTS)")


def check_gpu() -> None:
    """NVIDIA 드라이버 · GPU · VRAM 확인."""
    if shutil.which("nvidia-smi") is None:
        record("NVIDIA 드라이버", "FAIL", "nvidia-smi 없음 — 드라이버 미설치")
        return
    out = run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"])
    if not out:
        record("NVIDIA 드라이버", "FAIL", "nvidia-smi 실행 실패")
        return
    for line in out.splitlines():
        name, driver, vram = (x.strip() for x in line.split(","))
        # Isaac Sim 5.x 이상은 드라이버 535 이상을 요구한다.
        major = int(driver.split(".")[0]) if driver.split(".")[0].isdigit() else 0
        status = "PASS" if major >= 535 else "WARN"
        record("GPU / 드라이버", status, f"{name} · driver {driver} · VRAM {vram}")


def check_disk() -> None:
    """설치 경로의 여유 디스크 용량 확인 (Isaac Sim 캐시 포함 최소 50GB 권장)."""
    target = ISAACLAB_PATH if os.path.exists(ISAACLAB_PATH) else "/"
    free_gb = shutil.disk_usage(target).free / (1024**3)
    status = "PASS" if free_gb >= 50 else "WARN"
    record("디스크 여유", status, f"{free_gb:.1f} GB free ({target})")


def check_isaac_sim() -> None:
    """Isaac Sim 설치 경로 · 버전 · python.sh 확인."""
    sim_path = os.path.join(ISAACLAB_PATH, "_isaac_sim")
    if not os.path.exists(sim_path):
        record("Isaac Sim 경로", "FAIL", f"{sim_path} 없음 (심볼릭 링크 미연결)")
        return
    real = os.path.realpath(sim_path)
    record("Isaac Sim 경로", "PASS", real)

    version_file = os.path.join(sim_path, "VERSION")
    if os.path.exists(version_file):
        with open(version_file, encoding="utf-8") as f:
            record("Isaac Sim 버전", "PASS", f.read().strip())
    else:
        record("Isaac Sim 버전", "FAIL", "VERSION 파일 없음")

    python_sh = os.path.join(sim_path, "python.sh")
    if os.access(python_sh, os.X_OK):
        record("Isaac Sim python.sh", "PASS", python_sh)
    else:
        record("Isaac Sim python.sh", "FAIL", f"{python_sh} 실행 불가")


def check_isaac_lab() -> None:
    """Isaac Lab 저장소 · 버전 · 실행 스크립트 확인."""
    if not os.path.isdir(ISAACLAB_PATH):
        record("Isaac Lab 경로", "FAIL", f"{ISAACLAB_PATH} 없음")
        return
    record("Isaac Lab 경로", "PASS", ISAACLAB_PATH)

    version_file = os.path.join(ISAACLAB_PATH, "VERSION")
    if os.path.exists(version_file):
        with open(version_file, encoding="utf-8") as f:
            record("Isaac Lab 버전", "PASS", f.read().strip())
    else:
        record("Isaac Lab 버전", "FAIL", "VERSION 파일 없음")

    sh = os.path.join(ISAACLAB_PATH, "isaaclab.sh")
    record("isaaclab.sh", "PASS" if os.access(sh, os.X_OK) else "FAIL", sh)


def check_display() -> None:
    """GUI 창을 띄울 수 있는 디스플레이가 있는지 확인."""
    display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    if display:
        record("디스플레이(GUI)", "PASS", f"DISPLAY={display}")
    else:
        record("디스플레이(GUI)", "WARN", "DISPLAY 없음 — GUI 테스트는 --headless 로만 가능")


def main() -> int:
    print("=" * 70)
    print(" [00] Isaac Sim / Isaac Lab 설치 사전 점검")
    print("=" * 70)
    check_os()
    check_gpu()
    check_disk()
    check_display()
    check_isaac_sim()
    check_isaac_lab()

    fails = [r for r in results if r[1] == "FAIL"]
    warns = [r for r in results if r[1] == "WARN"]
    print("-" * 70)
    print(f" 결과: 총 {len(results)}건 · 실패 {len(fails)}건 · 경고 {len(warns)}건")
    if fails:
        print(" >>> 설치 미완료. 아래 항목을 먼저 해결할 것:")
        for name, _, detail in fails:
            print(f"     - {name}: {detail}")
    else:
        print(" >>> 사전 점검 통과. test_01 부터 순서대로 실행할 것.")
    print("=" * 70)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
