import numpy as np

# Check what's in the robot files
for name in ['seed1', 'seed2', 'seed3', 'seed4']:
    try:
        path = f"pokemon_{name}_vF.npy"
        robot = np.load(path, allow_pickle=True).item()
        print(f"\n{name}:")
        print(f"  Keys: {list(robot.keys())}")
        if 'mask' in robot:
            print(f"  mask shape: {np.asarray(robot['mask']).shape}")
        if 'colors' in robot:
            print(f"  colors shape: {np.asarray(robot['colors']).shape}")
    except Exception as e:
        print(f"{name}: ERROR - {e}")
