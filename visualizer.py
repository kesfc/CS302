from flask import Flask, render_template, Response, jsonify
from argparse import ArgumentParser
from simulator import Simulator
from utils import load_config
import threading
import time
import json
import numpy as np
import os

app = Flask(
    __name__,
    template_folder="visualizer/templates",
    static_folder="visualizer/static",
)

TARGET_FPS = 60.0
MAX_RACERS = 12
ROWS = 4
COLS = 1

state_lock = threading.Lock()

app_state = {
    "started": False,
    "race_finished": False,
    "step_index": 0,
    "actual_fps": 0.0,
    "target_distance": 12.0,
    "finish_mode": "first",  # "first" or "all"
    "start_com_x": [],
    "current_com_x": [],
    "distances": [],
    "finished": [],
    "finish_order": [],
}

# Globals populated in __main__
config = None
simulator = None
robots = []
n_racers = 0
n_masses_list = []
n_springs_list = []
voxel_payloads = []


# ----------------------------
# Name helpers
# ----------------------------
def infer_display_name(path: str) -> str:
    """
    Examples:
      pokemon_Charmander_vF.npy -> Charmander
      pokemon_seed1_vF.npy      -> Seed1
      my_robot.npy              -> My Robot
    """
    base = os.path.basename(path)
    stem = os.path.splitext(base)[0]  # remove .npy

    if stem.startswith("pokemon_"):
        stem = stem[len("pokemon_"):]

    if stem.endswith("_vF"):
        stem = stem[:-3]

    stem = stem.replace("_", " ").replace("-", " ").strip()

    if not stem:
        return "Pokemon"

    return " ".join(part.capitalize() for part in stem.split())


# ----------------------------
# Voxel helpers
# ----------------------------
def voxel_to_masses(row, col):
    return [
        [col, row],
        [col + 1, row],
        [col, row + 1],
        [col + 1, row + 1],
    ]


def compute_voxel_mass_indices(robot: dict):
    """
    Returns:
      voxels: list of dicts:
        { "r": int, "c": int, "mass_ids": [i0,i1,i2,i3], "color": [r,g,b] }
      mask_dim: int
      scale: float
    """
    if "mask" not in robot:
        raise ValueError("robot file missing 'mask' (needed for colored voxel rendering).")
    if "colors" not in robot:
        raise ValueError("robot file missing 'colors' (needed for colored voxel rendering).")

    mask = np.asarray(robot["mask"], dtype=np.int32)
    colors = np.asarray(robot["colors"], dtype=np.uint8)
    scale = float(robot.get("scale", 0.1))
    masses = np.asarray(robot["masses"], dtype=np.float32)

    grid_xy = np.rint(masses / scale).astype(int)
    coord_to_idx = {(int(x), int(y)): i for i, (x, y) in enumerate(grid_xy)}

    voxels = []
    rs, cs = np.where(mask > 0)
    for r, c in zip(rs.tolist(), cs.tolist()):
        corners = voxel_to_masses(r, c)
        try:
            ids = [coord_to_idx[(corners[k][0], corners[k][1])] for k in range(4)]
        except KeyError:
            continue

        col_rgb = colors[r, c].tolist()
        voxels.append({
            "r": int(r),
            "c": int(c),
            "mass_ids": ids,
            "color": col_rgb,
        })

    return voxels, int(mask.shape[0]), float(scale)


# ----------------------------
# Race helpers
# ----------------------------
def get_positions_for_step(step_idx: int):
    """
    Return list of positions arrays, one per racer, at step_idx.
    Each positions array is shape (n_masses_i, 2).
    """
    x_np = simulator.x.to_numpy()
    max_steps = x_np.shape[1]
    step_idx = max(0, min(int(step_idx), max_steps - 1))

    out = []
    for i in range(n_racers):
        nm = int(n_masses_list[i])
        out.append(x_np[i, step_idx, :nm].copy())
    return out


def compute_com_x_from_positions(positions_list):
    xs = []
    for pos in positions_list:
        com = pos.mean(axis=0)
        xs.append(float(com[0]))
    return xs


def reset_race_state(started: bool):
    """
    Reinitialize robots and reset race bookkeeping.
    If started=False, race waits for /start.
    """
    global simulator

    simulator.reinitialize_robots()

    initial_positions = get_positions_for_step(0)
    start_com_x = compute_com_x_from_positions(initial_positions)

    with state_lock:
        app_state["started"] = started
        app_state["race_finished"] = False
        app_state["step_index"] = 0
        app_state["actual_fps"] = 0.0
        app_state["start_com_x"] = start_com_x[:]
        app_state["current_com_x"] = start_com_x[:]
        app_state["distances"] = [0.0 for _ in range(n_racers)]
        app_state["finished"] = [False for _ in range(n_racers)]
        app_state["finish_order"] = []


def build_init_payload():
    racers_payload = []
    for i, robot in enumerate(robots):
        racers_payload.append({
            "id": i,
            "name": robot.get("name", f"pokemon_{i+1}"),
            "springs": np.asarray(robot["springs"]).tolist(),
            "voxels": voxel_payloads[i],
            "n_masses": int(n_masses_list[i]),
            "n_springs": int(n_springs_list[i]),
        })

    return {
        "type": "init",
        "rows": ROWS,
        "cols": COLS,
        "target_distance": float(app_state["target_distance"]),
        "ground_height": float(config["simulator"]["ground_height"]),
        "started": bool(app_state["started"]),
        "race_finished": bool(app_state["race_finished"]),
        "finish_mode": app_state["finish_mode"],
        "racers": racers_payload,
    }


def build_idle_step_payload():
    with state_lock:
        step_idx = int(app_state["step_index"])
        fps = float(app_state["actual_fps"])
        started = bool(app_state["started"])
        race_finished = bool(app_state["race_finished"])
        finish_order = list(app_state["finish_order"])
        distances = list(app_state["distances"])
        finished = list(app_state["finished"])

    positions_list = get_positions_for_step(step_idx)

    racers_payload = []
    for i in range(n_racers):
        racers_payload.append({
            "id": i,
            "name": robots[i].get("name", f"pokemon_{i+1}"),
            "positions": positions_list[i].tolist(),
            "distance": float(distances[i]),
            "finished": bool(finished[i]),
            "rank": (finish_order.index(i) + 1) if i in finish_order else None,
        })

    return {
        "type": "step",
        "step": step_idx,
        "fps": fps,
        "started": started,
        "race_finished": race_finished,
        "finish_order": finish_order,
        "racers": racers_payload,
    }


def step_once():
    """
    Advance simulation by one step if race is started and not finished.
    Returns step payload dict.
    """
    global simulator

    with state_lock:
        started = app_state["started"]
        race_finished = app_state["race_finished"]
        t = int(app_state["step_index"])

    if not started:
        return build_idle_step_payload()

    if race_finished:
        return build_idle_step_payload()

    max_steps = int(simulator.steps[None])

    if t >= max_steps - 1:
        with state_lock:
            app_state["race_finished"] = True
        return build_idle_step_payload()

    simulator.compute_com(t)
    simulator.nn1(t)
    simulator.nn2(t)
    simulator.apply_spring_force(t)
    simulator.advance(t + 1)

    positions_next = get_positions_for_step(t + 1)

    someone_finished_now = False
    all_finished_now = True

    with state_lock:
        for i in range(n_racers):
            pos = positions_next[i]
            com_x = float(pos.mean(axis=0)[0])
            dist = com_x - app_state["start_com_x"][i]

            app_state["current_com_x"][i] = com_x
            app_state["distances"][i] = dist

            if (not app_state["finished"][i]) and dist >= app_state["target_distance"]:
                app_state["finished"][i] = True
                app_state["finish_order"].append(i)
                someone_finished_now = True

            if not app_state["finished"][i]:
                all_finished_now = False

        app_state["step_index"] = t + 1

        if app_state["finish_mode"] == "first":
            if someone_finished_now:
                app_state["race_finished"] = True
        else:
            if all_finished_now:
                app_state["race_finished"] = True

        payload = {
            "type": "step",
            "step": int(app_state["step_index"]),
            "fps": float(app_state["actual_fps"]),
            "started": bool(app_state["started"]),
            "race_finished": bool(app_state["race_finished"]),
            "finish_order": list(app_state["finish_order"]),
            "racers": [],
        }

        for i in range(n_racers):
            payload["racers"].append({
                "id": i,
                "name": robots[i].get("name", f"pokemon_{i+1}"),
                "positions": positions_next[i].tolist(),
                "distance": float(app_state["distances"][i]),
                "finished": bool(app_state["finished"][i]),
                "rank": (app_state["finish_order"].index(i) + 1) if i in app_state["finish_order"] else None,
            })

    return payload


# ----------------------------
# Flask routes
# ----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_race():
    reset_race_state(started=True)
    return jsonify({"ok": True})


@app.route("/reset", methods=["POST"])
def reset_race():
    reset_race_state(started=False)
    return jsonify({"ok": True})


@app.route("/stream")
def stream():
    def event_stream():
        yield f"data: {json.dumps(build_init_payload())}\n\n"

        fps_samples = []
        last_fps_update = time.perf_counter()

        while True:
            frame_start = time.perf_counter()
            target_interval = 1.0 / TARGET_FPS

            payload = step_once()
            yield f"data: {json.dumps(payload)}\n\n"

            frame_end = time.perf_counter()
            work_time = frame_end - frame_start

            sleep_time = target_interval - work_time
            if sleep_time > 0.001:
                time.sleep(sleep_time)

            total_frame_time = time.perf_counter() - frame_start
            if total_frame_time > 0:
                fps_samples.append(1.0 / total_frame_time)

            current_time = time.perf_counter()
            if current_time - last_fps_update >= 0.5:
                if fps_samples:
                    with state_lock:
                        app_state["actual_fps"] = sum(fps_samples) / len(fps_samples)
                    fps_samples = []
                last_fps_update = current_time

    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--inputs",
        nargs="+",
        default=[
            "pokemon_Charmander_vF.npy",
            "pokemon_Squirtle_vF.npy",
            "pokemon_Bulbasaur_vF.npy",
            "pokemon_Pikachu_vF.npy",
        ],
        help="Paths to saved robot .npy files (up to 12). Example: --inputs a.npy b.npy c.npy ...",
    )
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--target-distance", type=float, default=13.0, help="Race finish distance in world x units")
    parser.add_argument(
        "--finish-mode",
        type=str,
        default="first",
        choices=["first", "all"],
        help="'first' = first finisher wins immediately; 'all' = wait until everyone finishes",
    )
    args = parser.parse_args()

    input_paths = args.inputs[:MAX_RACERS]
    if len(input_paths) == 0:
        raise ValueError("Please provide at least one robot file with --inputs")
    if len(args.inputs) > MAX_RACERS:
        print(f"Warning: received {len(args.inputs)} inputs, only first {MAX_RACERS} will be used.")

    print("Loading robots:")
    robots = []
    for p in input_paths:
        r = np.load(p, allow_pickle=True).item()

        # Force display name from filename instead of internal saved name like seed1/seed2
        r["name"] = infer_display_name(p)

        robots.append(r)
        print(f"  {p}: {r['name']} | masses={r['n_masses']} springs={r['n_springs']}")

    n_racers = len(robots)

    config = load_config(args.config)

    max_n_masses = 0
    max_n_springs = 0
    for r in robots:
        if "max_n_masses" in r and "max_n_springs" in r:
            max_n_masses = max(max_n_masses, int(r["max_n_masses"]))
            max_n_springs = max(max_n_springs, int(r["max_n_springs"]))
        else:
            max_n_masses = max(max_n_masses, int(r["n_masses"]))
            max_n_springs = max(max_n_springs, int(r["n_springs"]))

    config["simulator"]["n_masses"] = int(max_n_masses)
    config["simulator"]["n_springs"] = int(max_n_springs)
    config["simulator"]["n_sims"] = int(n_racers)

    print(f"Using simulator dimensions: max_masses={max_n_masses}, max_springs={max_n_springs}, n_sims={n_racers}")

    print("Initializing simulator.")
    simulator = Simulator(
        sim_config=config["simulator"],
        taichi_config=config["taichi"],
        seed=config["seed"],
        needs_grad=False,
    )

    simulator.initialize(
        [r["masses"] for r in robots],
        [r["springs"] for r in robots],
    )

    control_ids = []
    control_params = []
    for i, r in enumerate(robots):
        if "control_params" in r:
            control_ids.append(i)
            control_params.append(r["control_params"])

    if control_ids:
        simulator.set_control_params(control_ids, control_params)
        print(f"Loaded control parameters for {len(control_ids)} racer(s)")
    else:
        print("No control parameters found - using simulator defaults")

    n_masses_list = [int(simulator.n_masses[i]) for i in range(n_racers)]
    n_springs_list = [int(simulator.n_springs[i]) for i in range(n_racers)]

    voxel_payloads = []
    for r in robots:
        voxels, _, _ = compute_voxel_mass_indices(r)
        voxel_payloads.append(voxels)

    app_state["target_distance"] = float(args.target_distance)
    app_state["finish_mode"] = args.finish_mode

    reset_race_state(started=False)

    print(f"\nPokemon racing visualizer running at http://localhost:{args.port}")
    print(f"Rows x Cols: {ROWS} x {COLS}")
    print(f"Racers: {n_racers}")
    print(f"Target distance: {args.target_distance}")
    print(f"Finish mode: {args.finish_mode}")
    print("Press Start Race in the browser to begin.\n")

    app.run(host="0.0.0.0", port=args.port, debug=args.debug, threaded=True, use_reloader=False)