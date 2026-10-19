import numpy as np

def f(x):
    """目标函数"""
    x1, x2 = x
    return 4*x1**2 + x2**2 - 8*x1 + 4*x2 + 12

def grad_f(x):
    """梯度"""
    x1, x2 = x
    return np.array([8*x1 - 8, 2*x2 + 4])

def hessian_f(x):
    """海森矩阵（常数矩阵，与x无关）"""
    return np.array([[8, 0], [0, 2]])

def newton_method(x0, tol=1e-6, max_iter=100):
    """
    牛顿法求解极小点
    :param x0: 初始点
    :param tol: 梯度范数收敛阈值
    :param max_iter: 最大迭代次数
    :return: 极小点x, 迭代次数k
    """
    x = np.array(x0, dtype=float)
    for k in range(max_iter):
        grad = grad_f(x)
        grad_norm = np.linalg.norm(grad)
        if grad_norm < tol:
            print(f"迭代{k}次后收敛，梯度范数={grad_norm:.2e} < {tol}")
            return x, k
        # 计算海森矩阵的逆
        hess_inv = np.linalg.inv(hessian_f(x))
        # 牛顿法更新
        x = x - hess_inv @ grad
        print(f"迭代{k+1}: x = {x}, f(x) = {f(x):.4f}")
    print("达到最大迭代次数，未收敛")
    return x, max_iter

# 测试：取初始点x0=(0,0)
x0 = [0, 0]
x_min, iter_num = newton_method(x0)
print("\n===== 结果 =====")
print(f"极小点: x* = {x_min}")
print(f"极小值: f(x*) = {f(x_min):.4f}")