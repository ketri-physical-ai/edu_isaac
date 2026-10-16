# Isaac Sim / Isaac Lab 설치 검토 테스트 — 실행 안내서

KS260818 모방학습 교육 · WBS **2.5 설치 검토 테스트 코드 작성 · 실행** 중
**Isaac Sim / Isaac Lab** 부분 (WBS 2.4 연계, M10 시연용).

GUI 로 눈으로 확인하면서 동시에 `PASS`/`FAIL` 로 자동 판정한다.

---

## 1. 준비 — 실행 전 확인

| 항목 | 값 |
|---|---|
| Isaac Lab 경로 | `/data/src/isaaclab` |
| Isaac Sim 경로 | `/data/src/isaaclab/_isaac_sim` (심볼릭 링크) |
| 테스트 코드 경로 | `/data/src/edu_isaac` |

**모든 명령은 `/data/src/isaaclab` 에서 실행한다.**
Isaac Sim / Isaac Lab 은 전용 파이썬(`python.sh`)을 쓰므로 시스템 `python3` 로 실행하면 안 된다.

```bash
cd /data/src/isaaclab
```

GUI 로 실행하려면 화면(DISPLAY)이 있어야 한다. SSH 접속 상태라면 `--headless` 를 붙인다.

---

## 2. 가장 빠른 실행 — 일괄 실행

```bash
# GUI 창이 순서대로 떴다 닫힌다 (약 4분)
/data/src/edu_isaac/run_all.sh

# 창 없이 점검만 — 원격 접속 · PC 9대 복제 후 자동 점검용 (약 3분)
/data/src/edu_isaac/run_all.sh --headless
```

`run_all.sh` 는 `[00] → [01] → [02] → [03]` 순서로 실행하고 마지막에 요약을 출력한다.
`[00]` 이 실패하면 이후 단계를 실행하지 않고 즉시 중단한다.

정상일 때 마지막 출력:

```
  PASS  [00] 설치 사전 점검
  PASS  [01] Isaac Sim 단독 동작
  PASS  [02] Isaac Lab 물리 시뮬레이션
  PASS  [03] Isaac Lab 강화학습 환경
----------------------------------------------------------------------
  통과 4건 · 실패 0건
  >>> Isaac Sim / Isaac Lab 설치 검증 완료. M10 시연 가능.
```

---

## 3. 개별 실행 명령

### [00] 설치 사전 점검 — 수 초

OS · GPU 드라이버 · 디스크 · DISPLAY · 설치 경로 · 버전을 확인한다.
Isaac Sim 을 띄우지 않으므로 **시스템 `python3` 로 실행**한다.

```bash
python3 /data/src/edu_isaac/test_00_env_check.py
```

옵션 없음.

### [01] Isaac Sim 단독 동작 — 약 1분

Isaac Sim(Kit) 자체가 뜨는지, USD 스테이지·렌더링이 되는지 확인한다.
**Isaac Sim 의 `python.sh` 로 실행**한다 (Isaac Lab 을 거치지 않는다).

```bash
cd /data/src/isaaclab

# GUI (기본)
./_isaac_sim/python.sh /data/src/edu_isaac/test_01_isaac_sim.py

# 창 없이 점검만
./_isaac_sim/python.sh /data/src/edu_isaac/test_01_isaac_sim.py --headless

# 짧게 (렌더 프레임 수 축소)
./_isaac_sim/python.sh /data/src/edu_isaac/test_01_isaac_sim.py --frames 120
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--headless` | 꺼짐 | GUI 창 없이 실행 |
| `--frames N` | `600` | 렌더할 프레임 수 (600 ≈ 10초) |

### [02] Isaac Lab 물리 시뮬레이션 — 약 1분

Isaac Lab AppLauncher 로 앱을 띄우고 중력·바닥충돌이 실제로 계산되는지 확인한다.
**`isaaclab.sh -p` 로 실행**한다.

```bash
cd /data/src/isaaclab

# GUI (기본)
./isaaclab.sh -p /data/src/edu_isaac/test_02_isaac_lab_sim.py

# 창 없이 점검만
./isaaclab.sh -p /data/src/edu_isaac/test_02_isaac_lab_sim.py --headless

# 짧게 / CPU 로 실행
./isaaclab.sh -p /data/src/edu_isaac/test_02_isaac_lab_sim.py --steps 120
./isaaclab.sh -p /data/src/edu_isaac/test_02_isaac_lab_sim.py --device cpu
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--headless` | 꺼짐 | GUI 창 없이 실행 |
| `--steps N` | `400` | 물리 스텝 수 (400 ≈ 6.7초) |
| `--device` | `cuda:0` | `cpu` / `cuda` / `cuda:N` |

### [03] Isaac Lab 강화학습 환경 — 약 2분

gym 태스크 등록 · 병렬 환경 · 관측/보상 반환까지 강화학습 파이프라인 전체를 확인한다.
M10 "강화학습 개념 시연" 의 최소 형태이기도 하다.

```bash
cd /data/src/isaaclab

# GUI (기본) — 카트폴 16개가 무작위로 흔들린다
./isaaclab.sh -p /data/src/edu_isaac/test_03_isaac_lab_env.py

# 창 없이 점검만
./isaaclab.sh -p /data/src/edu_isaac/test_03_isaac_lab_env.py --headless

# 환경 수 · 스텝 수 조정 (시연 시 환경을 늘리면 화면이 화려해진다)
./isaaclab.sh -p /data/src/edu_isaac/test_03_isaac_lab_env.py --num_envs 64 --steps 600

# 다른 태스크로 확인
./isaaclab.sh -p /data/src/edu_isaac/test_03_isaac_lab_env.py --task Isaac-Reach-Franka-v0
```

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--headless` | 꺼짐 | GUI 창 없이 실행 |
| `--task` | `Isaac-Cartpole-v0` | 확인할 gym 태스크 이름 |
| `--num_envs N` | `16` | 병렬 환경 수 |
| `--steps N` | `300` | 진행할 스텝 수 |
| `--device` | 태스크 기본값 | `cpu` / `cuda` / `cuda:N` |

---

## 4. GUI 에서 무엇이 보여야 정상인가

| 테스트 | 화면 |
|---|---|
| `[01]` | Isaac Sim 창 + 회색 바닥판 위 **노란 큐브 1개** (정지, 물리 없음) |
| `[02]` | 바닥면 위 **노란 큐브가 1m 높이에서 떨어져** 바닥에 멈춤 |
| `[03]` | **카트폴 16개**가 격자로 배치되어 각각 무작위로 흔들림 (학습 전 랜덤 정책) |

각 스크립트는 정해진 프레임/스텝을 마치면 **자동으로 창을 닫고 종료**한다.
더 오래 보고 싶으면 `--frames` / `--steps` 를 늘린다.

---

## 5. 결과 판정

- 종료 코드로 판정한다. `0` = 정상, `1` = 실패.
- 콘솔에는 항목별로 `[PASS]` / `[FAIL]` 이 출력되고, `[FAIL]` 줄에 원인이 함께 표시된다.
- 스크립트만 자동 판정에 쓰려면:

```bash
/data/src/edu_isaac/run_all.sh --headless && echo "이 PC 정상" || echo "이 PC 점검 필요"
```

---

## 6. 자주 나오는 실패와 조치

| 증상 | 원인 | 조치 |
|---|---|---|
| `[00] Isaac Sim 경로 FAIL` | `_isaac_sim` 심볼릭 링크 미연결 | `ln -s <isaac-sim 설치경로> /data/src/isaaclab/_isaac_sim` |
| `[00] NVIDIA 드라이버 FAIL` | 드라이버 미설치 | 드라이버 535 이상 설치 후 재부팅 |
| `[00] 디스플레이 WARN` | SSH 등 DISPLAY 없음 | `--headless` 로 실행 |
| GUI 를 켰는데 창이 안 뜸 | Isaac Lab 3.0 은 `--viz kit` 없이는 창을 띄우지 않음 | `[02]` `[03]` 은 스크립트가 자동으로 `--viz kit` 을 넣는다. 직접 `--viz` 를 준 경우 `--viz kit` 인지 확인 |
| `visualizer(s) ['kit'] could not be configured` | `--headless` 와 `--viz kit` 충돌 (Isaac Lab 3.0 이슈) | `--headless` 대신 `--viz none` 사용. `[02]` `[03]` 은 스크립트가 자동 변환한다 |
| `ModuleNotFoundError: isaaclab` | 시스템 `python3` 로 실행함 | `./isaaclab.sh -p` 또는 `./_isaac_sim/python.sh` 로 실행 |
| 첫 실행이 매우 느림 (5분+) | 셰이더 · Warp 커널 캐시 최초 생성 | 정상. 2회차부터 빨라짐 (`~/.cache/warp`, `/data/apps/isaacsim_cache`) |

---

## 7. PC 9대 복제 배포 후 점검 (WBS 2.8 · 2.9)

복제된 PC 마다 아래 한 줄로 최종 확인한다.

```bash
/data/src/edu_isaac/run_all.sh --headless && echo "이 PC 정상"
```

GUI 확인까지 필요하면 `--headless` 를 뺀다.

---

## 부록 — 검증 환경 및 버전 주의

2026-08-19 마스터 PC 실측 기준, 아래 환경에서 전 항목 PASS 확인.

| 항목 | 값 |
|---|---|
| OS | Ubuntu 22.04.5 LTS |
| GPU / 드라이버 | RTX 5080 (16GB) / 580.173.02 |
| Isaac Sim | **6.0.1-rc.7** (`/home/ketri/dev_ws/isaac_sim/isaacsim` 소스 빌드) |
| Isaac Lab | **3.0.0** (`/data/src/isaaclab`) |
| Python / PyTorch | 3.12.13 / 2.10.0+cu128 |

> **버전 주의** — WBS 2.4 에는 "Isaac Sim 5.1.0" 으로 기재돼 있으나 실제 설치본은 **6.0.1-rc.7** 이다.
> 5.1.0 용 예제 코드는 그대로 동작하지 않으므로 M10 교안(WBS 5.5) 작성 시 주의할 것.
> 주요 변경점:
> - Isaac Sim 6.0 에서 `isaacsim.core.api` (World, DynamicCuboid 등) 제거
> - Isaac Lab 3.0 에서 `--headless` 가 deprecated 되고 `--viz {kit,newton,rerun,viser,none}` 로 대체.
>   **`--viz kit` 이 없으면 GUI 창이 뜨지 않는다** (구버전과 기본 동작이 반대)
> - 자산 데이터 접근이 `obj.data.root_pos_w.torch` 형태로 변경
