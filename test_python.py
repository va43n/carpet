import numpy as np

x, w = 1000, 600
step = 900

x_span = list(map(int, np.arange(x, x + w, step)))

print(x_span)
