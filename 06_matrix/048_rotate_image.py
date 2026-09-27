"""
Pattern: 矩阵原地变换

Core:
顺时针转 90 度 = 沿主对角线转置 + 每行反转（另一种等价写法：先整体上下翻转 matrix.reverse() 再转置）。
转置时配对的是 (i, j) 与 (j, i)，所以只遍历一半（j < i）；每行反转时配对的是 (i, j) 与 (i, n-1-j)，所以减半的是列下标 j。

Time: O(n^2)
Space: O(1)（每行反转的切片是一行的临时副本，不随 n^2 增长）

Mistake:
- 转置遍历了全部下标 (i, j) in range(n) x range(n)：同一对元素被交换两次，整段等于没做，矩阵原样不动。
- 每行反转写成 matrix[i][j] 与 matrix[-i][j] 交换：列下标没变、行下标在变，这是上下翻转；而且 i = 0 时 -0 还是 0，那一行自己和自己换（和 189 题 nums[-0:] 同一个坑）。
- 第二版把该减半的下标搞反：i 只跑 range(n//2)、j 跑满 range(n)，同一对又换两次，后一半的行完全没动，结果变成纯转置 [[1,4,7],[2,5,8],[3,6,9]]。

易错点:
- 交换一对元素的循环，被减半的必须是真正配对的那个下标。
- 方向别记混：转置 + 每行反转是顺时针；转置 + 整体上下翻转是逆时针。
- 每行反转用 matrix[i][:] = matrix[i][::-1] 或 row.reverse()，比手写双下标交换更难出错。
"""


class Solution:
    def rotate(self, matrix: list[list[int]]) -> None:
        n = len(matrix)
        for i in range(n):
            for j in range(i):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

        for i in range(n):
            matrix[i][:] = matrix[i][::-1]


if __name__ == "__main__":
    import random
    import signal
    import time

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return」得到的 None 区分开

    def call_with_limit(cls, matrix, seconds):
        # 传进去的矩阵必须被原地修改
        grid = [row[:] for row in matrix]
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            ret = cls().rotate(grid)
            return ret, grid, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, grid, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(matrix):
        # 顺时针转 90 度：新矩阵第 i 行是原矩阵第 i 列自下往上。新建矩阵，和原地做法是两套逻辑
        n = len(matrix)
        return [[matrix[n - 1 - j][i] for j in range(n)] for i in range(n)]

    cases = [
        # 题目示例
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]],
        # 1x1 / 2x2：最小的会暴露「转置范围写成全部下标」的形状
        [[1]],
        [[1, 2], [3, 4]],
        # 负数、重复值、边界值
        [[-1, -2], [-3, -4]],
        [[7, 7], [7, 7]],
        [[1000, -1000], [-1000, 1000]],
        # 中心对称 / 对角线上有特殊值
        [[1, 0, 0], [0, 2, 0], [0, 0, 3]],
    ]

    # 穷举 n = 1..8，矩阵填 1,2,3,... 方便对照
    for n in range(1, 9):
        cases.append([[r * n + c + 1 for c in range(n)] for r in range(n)])

    # 随机小数据（题目 n <= 20）
    random.seed(0)
    for _ in range(300):
        n = random.randint(1, 20)
        cases.append([[random.randint(-1000, 1000) for _ in range(n)] for _ in range(n)])

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for matrix in cases:
            expected = reference(matrix)
            ret, grid, _ = call_with_limit(cls, matrix, 1.0)
            assert ret is not TIMED_OUT, f"{cls.__name__} {matrix}: 超过 1s，可能死循环"
            assert ret is None, f"{cls.__name__} {matrix}: 应该原地修改并返回 None，得到 {ret}"
            assert grid == expected, f"{cls.__name__} {matrix}: 期望 {expected}，得到 {grid}（注意是否原地修改、方向是否顺时针）"

    # 转两次应该等于上下左右都翻转，转四次回到原样（额外的自检）
    for cls in classes:
        matrix = [[r * 5 + c for c in range(5)] for r in range(5)]
        grid = [row[:] for row in matrix]
        for _ in range(4):
            cls().rotate(grid)
        assert grid == matrix, f"{cls.__name__}: 连续转四次没有回到原样，得到 {grid}"

    # 题目只给到 n <= 20，这里放大到 300 是为了拦住每个元素都重建矩阵之类的写法。
    # 本地实测：转置 + 每行反转 3ms，先整体反转再转置 2ms，四元素一组的环旋转 6ms，zip 重排 0ms
    n = 300
    big = [[r * n + c for c in range(n)] for r in range(n)]
    expected = reference(big)
    ret, grid, elapsed = call_with_limit(Solution, big, 1.0)
    assert ret is not TIMED_OUT, "Solution 大数据（n=300）超过 1s 被中断"
    assert ret is None, "Solution 大数据（n=300）: 应该返回 None"
    assert grid == expected, "Solution 大数据（n=300）: 结果不对"

    print(f"ok ({', '.join(c.__name__ for c in classes)}; n=300 {elapsed * 1000:.0f} ms)")
