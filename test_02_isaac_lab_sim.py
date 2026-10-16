#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[M10 / WBS 2.5] Isaac Lab 동작 확인 — AppLauncher · 물리 시뮬레이션 · GUI.

Isaac Lab 의 AppLauncher 로 Isaac Sim 을 띄우고, 바닥 위 1m 높이에서
큐브를 떨어뜨려 중력·충돌이 실제로 계산되는지 확인한다.
GUI 창에서 큐브가 떨어져 바닥에 멈추면 정상이다.

사용법:
    cd /data/src/isaaclab
    ./isaaclab.sh -p /data/src/test_code/test_02_isaac_lab_sim.py            # GUI
    ./isaaclab.sh -p /data/src/test_code/test_02_isaac_lab_sim.py --headless # 창 없이 점검만
"""

import argparse
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Isaac Lab 설치 동작 확인")
parser.add_argument("--steps", type=int, default=400, help="물리 스텝 수 (기본 400 ≈ 6.7초)")
# --headless, --device 등 Isaac Lab 표준 인자를 붙인다.
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# Isaac Lab 3.0 은 '--viz kit' 이 없으면 창을 띄우지 않는다(구버전의 기본 동작과 반대).
# 교육용 확인 스크립트이므로 기본을 GUI 로 두고, --headless 는 '--viz none' 으로 변환한다.
# 사용자가 --viz 를 직접 지정한 경우에는 그 선택을 그대로 존중한다.
if not getattr(args_cli, "visualizer_explicit", False):
    GUI_MODE = not args_cli.headless
    args_cli.headless = False
    args_cli.visualizer = ["kit"] if GUI_MODE else None
    args_cli.visualizer_explicit = True
else:
    GUI_MODE = bool(args_cli.visualizer) and "kit" in args_cli.visualizer

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# --- 앱 기동 이후에만 import 가능 ---
import torch  # noqa: E402

import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.assets import RigidObject, RigidObjectCfg  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402

DROP_HEIGHT = 1.0  # 큐브 초기 높이 [m]
CUBE_SIZE = 0.2  # 큐브 한 변 [m]

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """점검 결과 1건을 기록하고 즉시 출력한다."""
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def design_scene() -> RigidObject:
    """바닥 · 조명 · 낙하 큐브를 배치하고 큐브 핸들을 반환한다."""
    ground_cfg = sim_utils.GroundPlaneCfg()
    ground_cfg.func("/World/defaultGroundPlane", ground_cfg)

    light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.8, 0.8, 0.8))
    light_cfg.func("/World/Light", light_cfg)

    cube_cfg = RigidObjectCfg(
        prim_path="/World/Cube",
        spawn=sim_utils.CuboidCfg(
            size=(CUBE_SIZE, CUBE_SIZE, CUBE_SIZE),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            mass_props=sim_utils.MassPropertiesCfg(mass=1.0),
            collision_props=sim_utils.CollisionPropertiesCfg(),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.0, 0.85, 0.1), metallic=0.2),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.0, 0.0, DROP_HEIGHT)),
    )
    return RigidObject(cfg=cube_cfg)


def main() -> int:
    print("=" * 70)
    print(" [02] Isaac Lab 동작 확인 (물리 시뮬레이션)")
    print(f"      모드: {'GUI' if GUI_MODE else 'headless'}")
    print("=" * 70)

    check("Isaac Lab AppLauncher 기동", simulation_app is not None)

    sim_cfg = sim_utils.SimulationCfg(device=args_cli.device)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[1.5, 1.5, 1.0], target=[0.0, 0.0, 0.2])
    check("SimulationContext 생성", sim is not None, f"device={sim.device}, dt={sim.get_physics_dt():.5f}s")

    cube = design_scene()
    sim.reset()
    check("씬 구성 · 리셋", cube.num_instances > 0, f"강체 {cube.num_instances}개")

    sim_dt = sim.get_physics_dt()
    z_start = float(cube.data.root_pos_w.torch[0, 2])
    z_min = z_start

    for step in range(args_cli.steps):
        if not simulation_app.is_running():
            break
        cube.write_data_to_sim()
        sim.step()
        cube.update(sim_dt)
        z_now = float(cube.data.root_pos_w.torch[0, 2])
        z_min = min(z_min, z_now)
        if step % 100 == 0:
            print(f"        step {step:4d} · 큐브 높이 z = {z_now:.4f} m")

    z_end = float(cube.data.root_pos_w.torch[0, 2])

    # 중력이 계산되었다면 시작 높이보다 확실히 내려와 있어야 한다.
    check("중력 적용 (낙하)", z_end < z_start - 0.1, f"z {z_start:.3f} m → {z_end:.3f} m")
    # 바닥 충돌이 동작했다면 큐브 반높이 근처에서 멈추고 바닥을 뚫지 않는다.
    expected_rest = CUBE_SIZE / 2.0
    check(
        "바닥 충돌 (관통 없음)",
        z_min > expected_rest - 0.05 and abs(z_end - expected_rest) < 0.05,
        f"최저 z={z_min:.3f} m · 정지 z={z_end:.3f} m (기대 {expected_rest:.3f} m)",
    )
    check("GPU 텐서 파이프라인", torch.cuda.is_available() or sim.device == "cpu", f"torch {torch.__version__} · {sim.device}")

    fails = [r for r in results if not r[1]]
    print("-" * 70)
    print(f" 결과: 총 {len(results)}건 · 실패 {len(fails)}건")
    print(" >>> Isaac Lab 정상 동작" if not fails else " >>> Isaac Lab 이상 — 위 FAIL 항목 확인")
    print("=" * 70)
    return 1 if fails else 0


if __name__ == "__main__":
    exit_code = main()
    simulation_app.close()
    sys.exit(exit_code)
