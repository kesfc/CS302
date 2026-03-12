import numpy as np

r = np.load('pokemon_seed1_v0.npy', allow_pickle=True).item()
print(r['mask'])
