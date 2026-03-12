# Pokémon ALife-Sim Modifications

This project is a modified version of the original **ALife-Sim** repository. The main goal of these changes was to replace randomly generated soft robots with **Pokémon-shaped robots**, train them individually, and make the training and visualization pipeline better suited for comparison and presentation.

## Overview

Compared with the original ALife-Sim project, this version introduces:

- hand-designed Pokémon-inspired robot seeds
- higher-resolution robot bodies
- GPU-based training
- per-Pokémon training instead of batch evolution
- better reproducibility and comparison
- improved visualization consistency
- more detailed saved results and statistics

## Main Modifications

### Training Configuration Changes

Several important parameters in `config.yaml` were changed from the original repository:

| Parameter | Original | Modified |
|---|---:|---:|
| Parallel simulations | 16 | 4 |
| Simulation length | 1000 | 6000 |
| Learning steps | 40 | 300 |
| Hidden layer size | 128 | 192 |
| CPG count | 6 | 12 |
| CPG frequency | 15.0 | 20.0 |
| Learning rate | 7e-3 | 3e-3 |
| Taichi backend | cpu | cuda |

These changes make training longer, more stable, and more expressive, while also enabling GPU acceleration.

### Higher Robot Resolution

In the original project, robots were generated on an **8 × 8** grid.

In this version, the robot resolution was increased to:

```python
MASK_DIM = 15
```

This allows more detailed robot structures and makes it possible to build recognizable Pokémon-like shapes instead of simple random morphologies.

### Hand-Designed Pokémon Seeds

Instead of sampling random robot bodies, this version uses fixed seed designs for several Pokémon-inspired robots.

This means:

- robots are no longer randomly generated at startup
- each robot has a predefined body shape and color layout
- experiments are easier to reproduce
- side-by-side comparison becomes more meaningful

This also makes the project more visually interesting and suitable for demonstrations.

### Orientation Fix

Vertical flipping logic was added so that robot designs match the intended visual orientation.

This was necessary because:

- the way the grid is drawn by hand
- and the way the simulator interprets row indices

do not naturally align.

With the flipping fix:

- Pokémon appear upright in the simulator
- physical structure and rendered visualization remain consistent

### Per-Pokémon Training Workflow

The original repository trains a batch of robots together and saves only a small number of top results.

This project changes the workflow so that:

- each Pokémon seed is trained individually
- each seed is evaluated before training
- the best trained result is saved separately for each Pokémon

For each Pokémon, the following files are saved:

- `pokemon_seedX_v0.npy` — best initial version before training
- `pokemon_seedX_vF.npy` — best final trained version after training
- `fitness_history_seedX.npy` — fitness history during optimization

This makes it easier to compare performance before and after training for each character.

### Additional Evaluation Statistics

Extra logging and result tracking were added to record:

- initial best fitness
- final best fitness
- fitness improvement
- best learning step
- best simulation index

These statistics provide a clearer picture of how much each Pokémon improves during optimization.

### Command-Line Control for Parallelism

A `--parallel` command-line argument was added so that the number of parallel simulations can be changed without manually editing `config.yaml`.

This makes experimentation more flexible and easier to manage.

## Workflow Summary

The original ALife-Sim workflow was mainly focused on:

- random **8 × 8** soft robots
- shorter CPU-based training
- generic batch optimization

This modified version focuses on:

- hand-designed **15 × 15** Pokémon-shaped robots
- longer GPU-accelerated training
- per-robot training and comparison
- saved initial and final robot versions
- saved fitness histories
- improved visualization consistency

## Output Files

For each trained Pokémon seed, the pipeline saves:

- `pokemon_seedX_v0.npy`
- `pokemon_seedX_vF.npy`
- `fitness_history_seedX.npy`

These outputs make it easier to inspect:

- initial morphology
- final trained morphology
- training progress over time

## Why These Changes Were Made

These modifications were designed to make the project:

- more reproducible
- easier to compare across individual robots
- visually more engaging
- better suited for presentations and demonstrations
- more expressive in terms of robot morphology and control

## Summary

Overall, this project transforms the original ALife-Sim from a random soft-robot training framework into a more controlled and presentation-friendly system built around Pokémon-inspired robot designs.

The final result is:

- more structured
- more reproducible
- visually distinctive
- easier to evaluate on a per-robot basis

## Credits

This project is based on the original **ALife-Sim** repository, with substantial modifications for custom robot design, training, and visualization.
