"""
Pattern: 阶梯查找（从右上角走）

Core:
从右上角出发：target 更小就往左走（这一列剩下的都比它大），更大就往下走（这一行剩下的都比它小），相等即找到。每一步排掉一整列或一整行，最多走 m + n 步。

Time: O(m + n)
Space: O(1)

Mistake:
- （本题一次通过，未出错）

易错点:
- 起点只能选右上角或左下角。左上角是最小值，往右和往下都变大，无法判断该走哪边；题目示例找 5 会返回 False。右下角同理（往左和往上都变小）。
- 循环条件只需 r < m and c >= 0：r 单调增、c 单调减，另外两个比较恒真。
- 300x300 的规模下靠计时区分不出 O(mn) 和 O(m + n)（整行 in 是 C 层扫描，90000 个元素只要几毫秒）。测试改用 CountingRow 统计元素访问次数：阶梯 1990 次、逐行二分 11741 次、逐行整行扫描 405600 次（300x300 六次查询）。
"""


class Solution:
    def searchMatrix(self, matrix: list[list[int]], target: int) -> bool:
        m = len(matrix)
        n = len(matrix[0])
        r = 0
        c = n - 1
        while r < m and c >= 0:
            if target < matrix[r][c]:
                c -= 1
            elif target > matrix[r][c]:
                r += 1
            else:
                return True
        return False


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

    class CountingRow(list):
        """统计元素访问次数，用来验证没有把整个矩阵扫一遍。"""

        counter = [0]

        def __getitem__(self, i):
            CountingRow.counter[0] += 1
            return list.__getitem__(self, i)

        def __contains__(self, v):
            CountingRow.counter[0] += len(self)
            return list.__contains__(self, v)

        def __iter__(self):
            CountingRow.counter[0] += len(self)
            return list.__iter__(self)

    def call_with_limit(cls, matrix, target, seconds, count=False):
        grid = [CountingRow(row) if count else list(row) for row in matrix]
        CountingRow.counter[0] = 0
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().searchMatrix(grid, target)
            return got, time.perf_counter() - start, CountingRow.counter[0]
        except Timeout:
            return TIMED_OUT, None, CountingRow.counter[0]
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(matrix, target):
        # 逐行查找，只用于生成期望值
        return any(target in row for row in matrix)

    def make_sorted(m, n, rng):
        # 生成每行递增、每列也递增的矩阵
        grid = [[0] * n for _ in range(m)]
        for r in range(m):
            v = (rng.randint(-50, 50) if r == 0 else grid[r - 1][0]) + rng.randint(1, 5)
            grid[r][0] = v
            for c in range(1, n):
                grid[r][c] = grid[r][c - 1] + rng.randint(1, 5)
        for c in range(n):
            for r in range(1, m):
                if grid[r][c] <= grid[r - 1][c]:
                    grid[r][c] = grid[r - 1][c] + 1
        return grid

    cases = [
        # 题目示例
        ([[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]], 5, True),
        ([[1, 4, 7, 11, 15], [2, 5, 8, 12, 19], [3, 6, 9, 16, 22], [10, 13, 14, 17, 24], [18, 21, 23, 26, 30]], 20, False),
        # 1x1
        ([[5]], 5, True),
        ([[5]], 4, False),
        # 单行 / 单列
        ([[1, 3, 5]], 3, True),
        ([[1, 3, 5]], 4, False),
        ([[1], [3], [5]], 5, True),
        ([[1], [3], [5]], 0, False),
        # 四个角
        ([[1, 2], [3, 4]], 1, True),
        ([[1, 2], [3, 4]], 2, True),
        ([[1, 2], [3, 4]], 3, True),
        ([[1, 2], [3, 4]], 4, True),
        # 比最小值还小 / 比最大值还大
        ([[1, 2], [3, 4]], 0, False),
        ([[1, 2], [3, 4]], 5, False),
        # 目标落在行内空隙里（从左上角出发的错误写法会漏掉这类）
        ([[1, 4], [2, 5]], 2, True),
        ([[1, 4], [2, 5]], 3, False),
        # 负数与重复值（行列都是非递减）
        ([[-5, -3], [-4, -1]], -4, True),
        ([[1, 1], [1, 1]], 1, True),
        ([[1, 1], [1, 1]], 2, False),
        # 数值范围边界
        ([[-10**9, 0], [0, 10**9]], 10**9, True),
        ([[-10**9, 0], [0, 10**9]], 7, False),
    ]

    # 随机小矩阵：每个存在的值都要能找到，另外试若干不存在的值
    rng = random.Random(0)
    for _ in range(150):
        m = rng.randint(1, 6)
        n = rng.randint(1, 6)
        grid = make_sorted(m, n, rng)
        present = [grid[rng.randrange(m)][rng.randrange(n)] for _ in range(3)]
        absent = [grid[0][0] - 1, grid[-1][-1] + 1] + [rng.randint(-60, 200) for _ in range(3)]
        for t in present:
            cases.append((grid, t, True))
        for t in absent:
            cases.append((grid, t, reference(grid, t)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for matrix, target, expected in cases:
            got, _, _ = call_with_limit(cls, matrix, target, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} target={target}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} target={target}: 返回了 None"
            assert bool(got) == expected, f"{cls.__name__} matrix={matrix} target={target}: 期望 {expected}，得到 {got}"

    # 题目 m, n <= 300，进阶要求比 O(mn) 更好。这里用 CountingRow 统计元素访问次数：
    # 阶梯查找（右上角出发）每次只访问 m + n 量级；逐行二分约 m * log n；逐行整行扫描是 m * n。
    # 预算设成 m * n // 8，前两种都能过，整行扫描会超。
    # 本地实测 300x300 六次查询：阶梯 1990 次访问，逐行二分 11741 次，逐行扫描 405600 次
    rng = random.Random(1)
    for m, n in [(300, 300), (1000, 1000)]:
        grid = make_sorted(m, n, rng)
        budget = m * n // 8
        probes = [
            ("矩阵中间的值", grid[m // 2][n // 3], True),
            ("左上角", grid[0][0], True),
            ("右下角", grid[-1][-1], True),
            ("比最小值小 1", grid[0][0] - 1, False),
            ("比最大值大 1", grid[-1][-1] + 1, False),
            ("不存在的中间值", grid[m // 2][n // 3] + 1 if grid[m // 2][n // 3] + 1 not in grid[m // 2] else grid[0][0] - 2, None),
        ]
        for name, target, expected in probes:
            if expected is None:
                expected = reference(grid, target)
            got, elapsed, reads = call_with_limit(Solution, grid, target, 1.0, count=True)
            assert got is not TIMED_OUT, f"Solution 大数据（{m}x{n} {name}）超过 1s 被中断"
            assert bool(got) == expected, f"Solution 大数据（{m}x{n} {name}）: 期望 {expected}，得到 {got}"
            assert reads <= budget, (
                f"Solution 大数据（{m}x{n} {name}）: 访问了 {reads} 个元素，超过预算 {budget}，"
                f"说明还在整行整列地扫（阶梯查找只需 {m + n} 量级）")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; 300x300 与 1000x1000 的访问次数都在预算内)")
