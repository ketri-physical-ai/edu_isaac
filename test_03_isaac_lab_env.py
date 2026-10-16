#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[M10 / WBS 2.5] Isaac Lab 강화학습 환경 확인 — Cartpole 병렬 환경 + 랜덤 정책.

isaaclab_tasks 의 gym 태스크 등록 · 다중 환경 병렬 시뮬레이션 · 관측/보상 반환까지
강화학습 파이프라인 전체가 살아 있는지 확인한다. M10 강화학습 개념 시연의 최소 형태이기도 하다.
GUI 창에서 카트폴 여러 개가 동시에 무작위로 흔들리면 정상이다.

사용법:
    cd /data/src/isaaclab
    ./isaaclab.sh -p /data/src/test_code/test_03_isaac_lab_env.py                  # GUI
    ./isaaclab.sh -p /data/src/test_code/test_03_isaac_lab_env.py --headless       # 창 없이 점검만
    ./isaaclab.sh -p /data/src/test_code/test_03_isaac_lab_env.py --num_envs 64    # 환경 수 변경
"""

import argparse
import sys

import gymnasium as gym
import torch

import isaaclab_tasks  # noqa: F401  # gym 태스크 등록을 위해 import 필요
from isaaclab_tasks.utils import add_launcher_args, launch_simulation, resolve_task_config, setup_preset_cli

parser = argparse.ArgumentParser(description="Isaac Lab 강화학습 환경 동작 확인")
parser.add_argument("--task", type=str, default="Isaac-Cartpole-v0", help="확인할 태스크 이름")
parser.add_argument("--num_envs", type=int, default=16, help="병렬 환경 수 (기본 16)")
parser.add_argument("--steps", type=int, default=300, help="진행할 스텝 수 (기본 300)")
add_launcher_args(parser)
# Isaac Lab 3.0 은 --viz 를 지정하지 않으면 시각화 없이 실행된다. 교육용이므로 Kit 뷰어(GUI)를 기본으로 둔다.
parser.set_defaults(visualizer=["kit"])
args_cli, hydra_args = setup_preset_cli(parser)
sys.argv = [sys.argv[0]] + hydra_args

# Isaac Lab 3.0 에서 --headless 는 deprecated 이며 위 기본값(--viz kit)과 충돌해 실행이 중단된다.
# 다른 테스트 스크립트와 사용법을 맞추기 위해, --headless 를 '--viz none' 과 동일하게 변환한다.
if getattr(args_cli, "headless", False):
    args_cli.headless = False
    args_cli.visualizer = None
    args_cli.visualizer_explicit = True

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    """점검 결과 1건을 기록하고 즉시 출력한다."""
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    gui = args_cli.visualizer is not None
    print("=" * 70)
    print(" [03] Isaac Lab 강화학습 환경 확인")
    print(f"      모드: {'GUI' if gui else 'headless'}")
    print(f"      태스크: {args_cli.task} · 환경 {args_cli.num_envs}개 · {args_cli.steps} 스텝")
    print("=" * 70)

    torch.manual_seed(42)

    registered = args_cli.task in gym.registry
    check("gym 태스크 등록", registered, f"전체 {len(gym.registry)}개 태스크 등록됨")
    if not registered:
        return 1

    env_cfg, _ = resolve_task_config(args_cli.task, "")

    with launch_simulation(env_cfg, args_cli):
        env_cfg.scene.num_envs = args_cli.num_envs
        if args_cli.device is not None:
            env_cfg.sim.device = args_cli.device

        env = gym.make(args_cli.task, cfg=env_cfg)
        check("환경 생성", env is not None, f"관측 {env.observation_space} · 행동 {env.action_space}")

        obs, _ = env.reset()
        check("환경 리셋", obs is not None)

        total_reward = torch.zeros(env.unwrapped.num_envs, device=env.unwrapped.device)
        stepped = 0
        for step in range(args_cli.steps):
            with torch.inference_mode():
                # -1 ~ 1 범위의 무작위 행동 (학습 전 정책 = 랜덤)
                actions = 2 * torch.rand(env.action_space.shape, device=env.unwrapped.device) - 1
                _, reward, _, _, _ = env.step(actions)
                total_reward += reward
                stepped += 1
            if step % 100 == 0:
                print(f"        step {step:4d} · 평균 누적보상 = {total_reward.mean().item():.3f}")

        check("스텝 진행", stepped == args_cli.steps, f"{stepped}/{args_cli.steps} 스텝")
        check(
            "병렬 환경 · 보상 반환",
            total_reward.shape[0] == args_cli.num_envs and bool(torch.isfinite(total_reward).all()),
            f"환경 {total_reward.shape[0]}개 · 평균 누적보상 {total_reward.mean().item():.3f}",
        )
        env.close()

    fails = [r for r in results if not r[1]]
    print("-" * 70)
    print(f" 결과: 총 {len(results)}건 · 실패 {len(fails)}건")
    print(" >>> 강화학습 파이프라인 정상" if not fails else " >>> 이상 — 위 FAIL 항목 확인")
    print("=" * 70)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
