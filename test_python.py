import copy
from numpy.linalg import norm

rect_ct = [[532, 154], [502, 742], [1567,  739], [1505, 154]]
print(rect_ct)

rect_copy = copy.deepcopy(rect_ct)

ind_min = 0
ind_max = 0
biggest = norm(rect_copy[0])
lowest = norm(rect_copy[0])
for i in range(1, 3):
    temp = norm(rect_copy[i])
    if lowest > temp:
        lowest = temp
        ind_min = i
    elif biggest < temp:
        biggest = temp
        ind_max = i

rect_ct[0] = rect_copy[ind_min]
rect_ct[2] = rect_copy[ind_max]

if ind_min < ind_max:
    rect_copy.pop(ind_max)
    rect_copy.pop(ind_min)
else:
    rect_copy.pop(ind_min)
    rect_copy.pop(ind_max)

if rect_copy[0][0] < rect_copy[1][0]:
    rect_ct[1] = rect_copy[1]
    rect_ct[3] = rect_copy[0]
else:
    rect_ct[1] = rect_copy[0]
    rect_ct[3] = rect_copy[1]

del rect_copy

print(rect_ct)
