import numpy as np

# Check what's in the robot files
for name in ['seed1', 'seed2', 'seed3', 'seed4']:
    try:
        path = f"pokemon_{name}_vF.npy"
        robot = np.load(path, allow_pickle=True).item()
        print(f"\n{name}:")
        print(f"  Keys: {list(robot.keys())}")
        print(f"  'mask' in robot: {'mask' in robot}")
        print(f"  'colors' in robot: {'colors' in robot}")
        print(f"  'n_masses': {robot.get('n_masses')}")
        print(f"  'n_springs': {robot.get('n_springs')}")
    except FileNotFoundError:
        print(f"{name}: File not found")
    except Exception as e:
        print(f"{name}: ERROR - {type(e).__name__}: {e}")
