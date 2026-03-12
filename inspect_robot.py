import numpy as np

r = np.load('pokemon_pikachu_v0.npy', allow_pickle=True).item()
print('mask shape', r.get('mask').shape if 'mask' in r else 'no mask')
print('n_masses', r['n_masses'], 'n_springs', r['n_springs'])
print('max_n_masses', r.get('max_n_masses'))
print('scale', r.get('scale'))
