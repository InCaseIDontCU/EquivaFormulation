import lippy as lp


c_vec = [3, 3, 7]
a_matrix = [
    [1, 1, 1],
    [1, 4, 0],
    [0, 0.5, 3]
]
b_vec = [3, 5, 7]


gomory = lp.CuttingPlaneMethod(c_vec, a_matrix, b_vec,log_mode=lp.LogMode.MEDIUM_LOG)
gomory.solve()