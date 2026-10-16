#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[M10 / WBS 2.5] Isaac Sim 단독 동작 확인 — GUI 창 · USD 스테이지 · 렌더 루프.

Isaac Lab 을 거치지 않고 Isaac Sim(Kit) 자체가 뜨는지 확인한다.
GUI 창이 열리고, 바닥 위에 노란 큐브 하나가 보이고, 뷰포트가 렌더링되면 정상이다.

사용법:
    cd /data/src/isaaclab
    ./_isaac_sim/python.sh /data/src/edu_isaac/test_01_isaac_sim.py            # GUI
    ./_isaac_sim/python.sh /data/src/edu_isaac/test_01_isaac_sim.py --headless # 창 없이 점검만
"""

import argparse
import sys

parser = argparse.ArgumentParser(description="Isaac Sim 설치 동작 확인")
parser.add_argument("--headless", action="store_true", help="GUI 창 없이 실행")
parser.add_argument("--frames", type=int, default=600, help="렌더할 프레임 수 (기본 600 ≈ 10초)")
args_cli = parser.parse_args()

# --- Isaac Sim(Kit) 앱을 가장 먼저 띄운다. 이후에야 omni/pxr 모듈을 import 할 수 있다. ---
from isaacsim import SimulationApp  # noqa: E402

simulation_app = SimulationApp({"headless": args_cli.headless})

import omni.usd  # noqa: E402
from pxr import Gf, UsdGeom, UsdLux  # noqa: E402

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """점검 결과 1건을 기록하고 즉시 출력한다."""
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def build_stage():
    """빈 스테이지에 조명 · 바닥 · 큐브를 올린다."""
    context = omni.usd.get_context()
    context.new_stage()
    stage = context.get_stage()

    UsdGeom.Xform.Define(stage, "/World")

    # 돔 라이트 — GUI 에서 물체가 보이도록
    dome = UsdLux.DomeLight.Define(stage, "/World/DomeLight")
    dome.CreateIntensityAttr(1000.0)

    # 바닥 — 큐브를 넓고 얇게 눌러 판으로 사용
    ground = UsdGeom.Cube.Define(stage, "/World/Ground")
    ground.CreateSizeAttr(1.0)
    UsdGeom.XformCommonAPI(ground).SetScale(Gf.Vec3f(10.0, 10.0, 0.02))
    ground.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.35, 0.4)])

    # 노란 큐브 — 육안 확인용 기준 물체
    cube = UsdGeom.Cube.Define(stage, "/World/Cube")
    cube.CreateSizeAttr(1.0)
    UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(0.0, 0.0, 0.5))
    cube.CreateDisplayColorAttr([Gf.Vec3f(1.0, 0.85, 0.1)])

    return stage


def main() -> int:
    print("=" * 70)
    print(" [01] Isaac Sim 단독 동작 확인")
    print(f"      모드: {'headless' if args_cli.headless else 'GUI'}")
    print("=" * 70)

    check("Isaac Sim 앱 기동", simulation_app is not None)

    stage = build_stage()
    check("USD 스테이지 생성", stage is not None)
    check("프림 생성 (조명·바닥·큐브)", all(stage.GetPrimAtPath(p).IsValid() for p in ("/World/DomeLight", "/World/Ground", "/World/Cube")))

    # 뷰포트는 GUI 모드에서만 존재한다. headless 에서는 점검 대상이 아니다.
    if not args_cli.headless:
        try:
            from omni.kit.viewport.utility import get_active_viewport

            viewport = get_active_viewport()
            check("GUI 뷰포트 활성화", viewport is not None, "화면에 Isaac Sim 창이 보여야 정상")
        except Exception as exc:  # noqa: BLE001 - 확장 미로드 등 모든 원인을 실패로 처리
            check("GUI 뷰포트 활성화", False, f"{type(exc).__name__}: {exc}")

    # 렌더 루프 — 창을 사용자가 닫으면 도중에 빠져나온다.
    rendered = 0
    for _ in range(args_cli.frames):
        if not simulation_app.is_running():
            break
        simulation_app.update()
        rendered += 1
    check("렌더 루프", rendered > 0, f"{rendered}/{args_cli.frames} 프레임 렌더")

    fails = [r for r in results if not r[1]]
    print("-" * 70)
    print(f" 결과: 총 {len(results)}건 · 실패 {len(fails)}건")
    print(" >>> Isaac Sim 정상 동작" if not fails else " >>> Isaac Sim 이상 — 위 FAIL 항목 확인")
    print("=" * 70)
    return 1 if fails else 0


if __name__ == "__main__":
    exit_code = main()
    simulation_app.close()
    sys.exit(exit_code)
