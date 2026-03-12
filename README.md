Pokémon ALife-Sim Modifications

This project is a modified version of the original ALife-Sim repository.
The main goal of my changes was to replace randomly generated soft robots with Pokémon-shaped robots, train them individually, and make the training and visualization pipeline better suited for comparison and presentation.

Main Changes
1. Training configuration was adjusted

Compared with the original repository, I changed several important parameters in config.yaml:

Reduced the number of parallel simulations:

from 16 to 4

Increased simulation length:

from 1000 to 6000

Increased learning steps:

from 40 to 300

Increased hidden layer size:

from 128 to 192

Increased CPG count:

from 6 to 12

Increased CPG frequency:

from 15.0 to 20.0

Reduced learning rate:

from 7e-3 to 3e-3

Changed Taichi backend:

from cpu to cuda

These changes make training longer, more stable, and more expressive, while also using GPU acceleration.

2. Robot resolution was increased

In the original project, robots were generated on an 8 × 8 grid.

I changed this to:

MASK_DIM = 15

This allows more detailed robot structures and makes it possible to build recognizable Pokémon-like shapes instead of simple random morphologies.

3. Random robots were replaced by hand-designed Pokémon seeds

Instead of sampling random robot bodies, I created fixed seed designs for several Pokémon-inspired robots.

This means:

robots are no longer randomly generated at the start

each robot has a predefined body shape and color layout

experiments become easier to reproduce and compare

This also makes the project more visually interesting and suitable for demonstrations.

4. Orientation handling was fixed

I added vertical flipping logic so that the robot design matches the intended visual orientation.

This was necessary because:

the way a grid is drawn by hand

and the way the simulator interprets row indices

do not naturally align.

By flipping the mask appropriately:

the Pokémon appears upright in the simulator

the physical structure and the visualization stay consistent

5. Training was changed from batch evolution to per-Pokémon training

The original repository trains a batch of robots together and saves only a few top results.

I changed the workflow so that:

each Pokémon seed is trained individually

each seed is evaluated before training

the best result after training is saved separately

For each Pokémon, the code now saves:

the best initial version: pokemon_seedX_v0.npy

the best final trained version: pokemon_seedX_vF.npy

the fitness history: fitness_history_seedX.npy

This makes it easier to compare performance before and after training for each character.

6. More detailed evaluation statistics were added

I added logic to record more useful training information, including:

initial best fitness

final best fitness

fitness improvement

the best learning step

the best simulation index

This gives a clearer picture of how much each Pokémon improves during optimization.

7. A command-line override for parallelism was added

I added a --parallel argument so that the number of parallel simulations can be changed from the command line without editing the config file manually.

This makes experimentation more flexible.

Overall Summary

In short, this project changes the original ALife-Sim from:

random 8 × 8 soft robots

shorter CPU-based training

generic batch optimization

into:

hand-designed 15 × 15 Pokémon-shaped robots

longer GPU-accelerated training

per-robot training and comparison

saved initial/final versions and fitness history

improved visualization consistency

The result is a more controlled, reproducible, and presentation-friendly version of ALife-Sim.
