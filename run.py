# run.py  (gradient-based training version: 16x16 pokemon seeds, save v0 + best(vF))
from __future__ import annotations

from argparse import ArgumentParser
from typing import Dict, List

import numpy as np

from simulator import Simulator
from utils import load_config
from robot import mask_to_robot, SCALE


# =========================================================
# 1) Pokemon seeds (16x16)
# =========================================================
def rgb(r, g, b):
    return np.array([r, g, b], dtype=np.uint8)


PALETTE = {
    "EMPTY": [255, 255, 255],

    # Base colors
    "BLACK": [0, 0, 0],
    "WHITE": [255, 255, 255],
    "GRAY": [160, 160, 160],
    "DGRAY": [90, 90, 90],

    # Warm colors
    "RED": [255, 0, 0],
    "DRED": [180, 0, 0],
    "PINK": [255, 182, 193],
    "DPINK": [220, 120, 150],
    "ORANGE": [255, 128, 0],
    "DORANGE": [210, 90, 0],
    "YELLOW": [255, 219, 0],
    "DYELLOW": [220, 180, 0],
    "CREAM": [255, 245, 160],
    "BROWN": [139, 69, 19],
    "LBROWN": [181, 101, 29],
    "DBROWN": [92, 51, 23],

    # Cool colors
    "BLUE": [85, 153, 204],
    "LBLUE": [140, 200, 235],
    "DBLUE": [40, 90, 160],
    "CYAN": [120, 220, 255],

    # Greens
    "GREEN": [120, 200, 80],
    "DGREEN": [60, 120, 40],
    "LGREEN": [170, 230, 120],

    # Special effects
    "FIRE": [255, 69, 0],
    "LFIRE": [255, 140, 0],
    "GOLD": [255, 200, 60],
}

def make_seed(name: str, occ: List[str], col: List[str]) -> Dict:
    h = len(occ)
    w = len(occ[0])
    assert h > 0 and all(len(s) == w for s in occ), "occ must have equal-width rows"
    assert len(col) == h and all(len(s) == w for s in col), "col must match occ shape"

    mask = np.array([[1 if ch == "1" else 0 for ch in row] for row in occ], dtype=np.int32)

    legend = {
        
    ".": "EMPTY",

    # Original
    "Y": "YELLOW",
    "K": "BLACK",
    "R": "RED",
    "B": "BLUE",
    "N": "BROWN",
    "W": "WHITE",
    "O": "ORANGE",
    "C": "CREAM",
    "F": "FIRE",
    "G": "GREEN",
    "D": "DGREEN",
    "P": "PINK",

    # Added
    "A": "GRAY",
    "H": "DGRAY",
    "E": "DRED",
    "I": "DPINK",
    "J": "DORANGE",
    "L": "DYELLOW",
    "M": "LBROWN",
    "Q": "DBROWN",
    "U": "LBLUE",
    "V": "DBLUE",
    "X": "CYAN",
    "T": "LGREEN",
    "Z": "LFIRE",
    "S": "GOLD",
    }

    colors = np.zeros((h, w, 3), dtype=np.uint8)
    for i in range(h):
        for j in range(w):
            colors[i, j] = PALETTE[legend[col[i][j]]]

    return {"name": name, "mask": mask, "colors": colors}

def pad_square(rows: List[str], fill: str = ".") -> List[str]:
    h = len(rows)
    w = max(len(r) for r in rows)
    n = max(h, w)

    # 先把每一行补到同样宽度
    rows = [r.ljust(n, fill) for r in rows]

    # 再在上面补空行，补成 n 行
    if len(rows) < n:
        rows = [fill * n] * (n - len(rows)) + rows

    return rows


def make_pokemon_seeds() -> List[Dict]:
    seeds = []

    # =====================================================
    # seed1
    # =====================================================
    col = [
        ".K.......KKK..",
        "KOK......KOOOK.",
        "KORK....KOOOOK.",
        ".KOYK..KOOWOOO.",
        ".RYYR..KOOKOOOK",
        ".RYYR..KOOOOOOK",
        "..KOK..KOOOKKK.",
        "..KOOKKOOOOO...",
        "...KOOKOKKYK...",
        "...KOKOOOYYK...",
        "....KKOOKYYK...",
        ".....KOOKKOOK..",
        ".....KO.KKKK...",
    ]
    col = pad_square(col)
    occ = ["".join("1" if ch != "." else "." for ch in row) for row in col]
    seeds.append(make_seed("seed1", occ, col))

    # =====================================================
    # seed2 (mirrored)
    # =====================================================
    col = [
        ".........KKK...",
        "........KBBBK..",
        ".......KBBBBBK.",
        "......KKBBWBBK.",
        ".....KNKBBKBBBK",
        "....KNN.BBBBBBK",
        ".KBKKNNWKBKKKK.",
        "KBBBKNWBBKYYBBK",
        "KBKBKNWKBBKYKK.",
        ".KKBBWKYKKYK...",
        "...KKKBKYYKBK..",
        ".....KBBKKKK...",
        ".....KKK.......",
    ]
    col = pad_square(col)
    occ = ["".join("1" if ch != "." else "." for ch in row) for row in col]
    seeds.append(make_seed("seed2", occ, col))

    # =====================================================
    # seed3 (mirrored)
    # =====================================================
    col = [
        ".....KK........",
        "....KDDK.......",
        "...KKGGKK......",
        "..KGDGDGDKG....",
        ".KGGDGDGGDGKKK.",
        ".KGDGGGDGKKBBK.",
        ".KGDGGGKKBBBBK.",
        "..KDGGKBBBBBBBK",
        ".KBBKKBKBBBBBBK",
        ".KBKBBBBBWKBBBK",
        "..KWKBKBBWRBBK.",
        "...KBBBBBBBBK..",
        "...K.K.KKKKK...",
    ]
    col = pad_square(col)
    occ = ["".join("1" if ch != "." else "." for ch in row) for row in col]
    seeds.append(make_seed("seed3", occ, col))

    # =====================================================
    # seed4 (mirrored)
    # =====================================================
    col = [
        "...........K...",
        "....KK....KK...",
        ".KK.KKK...KYK..",
        "KYYK.KYKKKKYK..",
        "KYYYKKYYYYYYK..",
        ".KYYYKKYYYYYYK.",
        "..KYYKYYKYYYKK.",
        "..KYKKYRYYYYYR.",
        "...KYKYYYYYYYK.",
        "...KKYKYYYYYK..",
        "....KYYKYYYK...",
        "....KYYYYYYK...",
        ".....KYKKKK....",
    ]
    col = pad_square(col)
    occ = ["".join("1" if ch != "." else "." for ch in row) for row in col]
    seeds.append(make_seed("seed4", occ, col))

    return seeds


# =========================================================
# 2) Helpers
# =========================================================
def seed_to_robot_geometry(seed: Dict) -> Dict:
    """
    Convert seed mask into simulator robot dict with masses/springs.

    Masks generated by the pokemon seeds are drawn with the head at the
    top of the 2D array.  We flip the mask vertically here so that the
    stored robot["mask"] matches the masses/springs orientation (bottom
    on ground), and the visualizer shows the shape upright.
    """
    mask = seed["mask"].astype(bool)
    colors = seed["colors"].astype(np.uint8)

    masses, springs = mask_to_robot(mask)
    masses = masses.astype(np.float32) * float(SCALE)
    springs = springs.astype(np.int32)

    # Flip mask and colors for storage, so they match the flipped masses/springs
    mask_flipped = np.flipud(mask)
    colors_flipped = np.flipud(colors)

    return {
        "name": seed["name"],
        "mask": mask_flipped.astype(np.int32),
        "colors": colors_flipped,
        "scale": float(SCALE),
        "n_masses": int(masses.shape[0]),
        "n_springs": int(springs.shape[0]),
        "masses": masses,
        "springs": springs,
    }


def eval_fitness(sim: Simulator) -> np.ndarray:
    """
    Evaluate fitness for all sims in current simulator state (no weight update).
    fitness = -loss, because loss = com0 - comt
    """
    loss = sim.evaluation_step().astype(np.float32)
    return -loss


def ensure_numpy(x) -> np.ndarray:
    return np.asarray(x, dtype=np.float32)


def save_robot(
    path: str,
    base_robot: dict,
    control_params: dict,
    max_m: int,
    max_s: int,
    extra: dict | None = None
):
    out = dict(base_robot)
    out["control_params"] = control_params
    out["max_n_masses"] = int(max_m)
    out["max_n_springs"] = int(max_s)
    if extra:
        out.update(extra)
    np.save(path, out, allow_pickle=True)


# =========================================================
# 3) Train one pokemon with gradient method
# =========================================================
def train_one_pokemon(
    simulator: Simulator,
    robot: dict,
    learning_steps: int,
    snapshot_eps: float = 1e-6,
) -> tuple[float, float, float, dict, dict, np.ndarray, dict]:
    """
    Returns:
      v0_best_fit, best_fit, delta,
      v0_robot_save_dict(control params), best_robot_save_dict(control params),
      fitness_history array shape (n_sims, learning_steps + 2),
      best_meta dict
    """
    n_sims = int(simulator.n_sims[None])

    simulator.initialize([robot["masses"]] * n_sims, [robot["springs"]] * n_sims)

    fit0 = eval_fitness(simulator)
    v0_idx = int(np.argmax(fit0))
    v0_best_fit = float(fit0[v0_idx])

    v0_params = simulator.get_control_params([v0_idx])[0]

    hist = np.zeros((n_sims, learning_steps + 2), dtype=np.float32)
    hist[:, 0] = fit0

    best_fit = v0_best_fit
    best_idx = v0_idx
    best_step = 0
    best_params = v0_params

    for step in range(1, learning_steps + 1):
        loss = ensure_numpy(simulator.learning_step())
        fit = -loss
        hist[:, step] = fit

        cur_idx = int(np.argmax(fit))
        cur_best = float(fit[cur_idx])

        if cur_best > best_fit + snapshot_eps:
            best_fit = cur_best
            best_idx = cur_idx
            best_step = step
            best_params = simulator.get_control_params([best_idx])[0]

    fit_final = eval_fitness(simulator)
    hist[:, -1] = fit_final

    cur_idx = int(np.argmax(fit_final))
    cur_best = float(fit_final[cur_idx])
    if cur_best > best_fit + snapshot_eps:
        best_fit = cur_best
        best_idx = cur_idx
        best_step = learning_steps + 1
        best_params = simulator.get_control_params([best_idx])[0]

    delta = best_fit - v0_best_fit
    meta = {
        "best_sim_idx": int(best_idx),
        "best_step": int(best_step),
        "n_sims": int(n_sims),
        "learning_steps": int(learning_steps),
    }
    return v0_best_fit, best_fit, delta, v0_params, best_params, hist, meta


# =========================================================
# 4) Main
# =========================================================
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--parallel", type=int, default=None,
                        help="Override simulator.n_sims for parallel training (e.g., 16)")
    args = parser.parse_args()

    config = load_config(args.config)

    np.random.seed(int(config["seed"]))

    seeds = make_pokemon_seeds()
    robots = [seed_to_robot_geometry(s) for s in seeds]

    max_num_masses = max(r["n_masses"] for r in robots)
    max_num_springs = max(r["n_springs"] for r in robots)
    config["simulator"]["n_masses"] = int(max_num_masses)
    config["simulator"]["n_springs"] = int(max_num_springs)

    config["simulator"]["needs_grad"] = True

    if args.parallel is not None:
        config["simulator"]["n_sims"] = int(args.parallel)

    n_sims = int(config["simulator"]["n_sims"])
    learning_steps = int(config["simulator"]["learning_steps"])

    print(f"[CFG] n_sims={n_sims} learning_steps={learning_steps} "
          f"max_masses={max_num_masses} max_springs={max_num_springs}")

    simulator = Simulator(
        sim_config=config["simulator"],
        taichi_config=config["taichi"],
        seed=int(config["seed"]),
        needs_grad=True,
    )

    global_best = (-1e9, None)

    for r in robots:
        name = r["name"]
        print(f"\n=== Training {name} ===")

        v0_fit, best_fit, delta, v0_params, best_params, hist, meta = train_one_pokemon(
            simulator=simulator,
            robot=r,
            learning_steps=learning_steps,
            snapshot_eps=1e-6,
        )

        np.save(f"fitness_history_{name}.npy", hist)

        save_robot(
            f"pokemon_{name}_v0.npy",
            base_robot=r,
            control_params=v0_params,
            max_m=max_num_masses,
            max_s=max_num_springs,
            extra={"v0_best_fitness": float(v0_fit)},
        )
        save_robot(
            f"pokemon_{name}_vF.npy",
            base_robot=r,
            control_params=best_params,
            max_m=max_num_masses,
            max_s=max_num_springs,
            extra={"best_fitness": float(best_fit), **meta},
        )

        print(f"[RESULT] {name}: v0_best={v0_fit:.6f}  best={best_fit:.6f}  "
              f"delta={delta:.6f}  "
              f"(best_step={meta['best_step']}, best_sim={meta['best_sim_idx']})")
        print(f"[SAVED] pokemon_{name}_v0.npy , pokemon_{name}_vF.npy , fitness_history_{name}.npy")

        if best_fit > global_best[0]:
            global_best = (best_fit, name)

    print(f"\n[GLOBAL BEST] {global_best[1]} fitness={global_best[0]:.6f}")