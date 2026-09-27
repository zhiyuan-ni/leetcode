"""
Pattern: 矩阵原地标记

Core:
必须先记录、后修改，否则新写进去的 0 会被后续读取误当成原始数据。
- Solution: 用两个 set 记下要清零的行号和列号，再统一置零。空间 O(m + n)。
- InPlace: 把标记存在第一行和第一列里。先用两个布尔变量记下首行首列原本有没有 0，再用 (1,1) 之后的格子往首行首列打标记，然后回填内部，最后才处理首行首列。空间 O(1)。

Time: O(mn)
Space: Solution O(m + n)；InPlace O(1)

Mistake:
- rows / cols 用 list 存下标：`in` 是线性查找，而且会重复记录。200x200 全 0 时 cols 长 40000（去重只有 200），实测 23 ~ 64 ms；换成 set 后 1 ~ 3 ms。这是「循环里藏线性操作」第四次出现（128 的 min、238 的 index、41 的 set(nums)）。
- 第三个循环里写了 `if r in rows or c in cols`：外层已按 `for c in cols` 遍历，条件恒真，是冗余判断；整行已清零的行再逐列写 0 也是重复劳动，用 if / else 分开。

易错点:
- 边扫边清零：扫到 0 就立刻清整行整列，新写的 0 会被当成原始 0，示例一得到 [[1,0,0],[0,0,0],[0,0,0]]。
- 用首行首列当标记区时，必须先把它们自身原本有没有 0 记下来，并且最后才回填；先回填首行首列会让整个矩阵变成 0。
- matrix[r] = [0] * n 是替换外层列表的元素，调用方若持有某一行的引用就看不到变化；matrix[r][:] = ... 才是改内容。
"""


class Solution:
    def setZeroes(self, matrix: list[list[int]]) -> None:
        rows = set()
        cols = set()
        m = len(matrix)
        n = len(matrix[0])
        for r in range(m):
            for c in range(n):
                if matrix[r][c] == 0:
                    rows.add(r)
                    cols.add(c)
        for r in range(m):
            if r in rows:
                matrix[r][:] = [0] * n
            else:
                for c in cols:
                    matrix[r][c] = 0


class SolutionInPlace:
    def setZeroes(self, matrix: list[list[int]]) -> None:
        m = len(matrix)
        n = len(matrix[0])
        first_row = any(v == 0 for v in matrix[0])
        first_col = any(row[0] == 0 for row in matrix)
        for r in range(1, m):
            for c in range(1, n):
                if matrix[r][c] == 0:
                    matrix[0][c] = 0
                    matrix[r][0] = 0
        for r in range(1, m):
            for c in range(1, n):
                if matrix[0][c] == 0 or matrix[r][0] == 0:
                    matrix[r][c] = 0
        if first_row:
            matrix[0][:] = [0] * n
        if first_col:
            for row in matrix:
                row[0] = 0


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
        # 传进去的矩阵必须被原地修改；超时直接中断
        grid = [row[:] for row in matrix]
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            ret = cls().setZeroes(grid)
            return ret, grid, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, grid, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(matrix):
        # 先记录要清零的行列，再统一置零，只用于生成期望值
        rows = set()
        cols = set()
        for i, row in enumerate(matrix):
            for j, v in enumerate(row):
                if v == 0:
                    rows.add(i)
                    cols.add(j)
        return [[0 if i in rows or j in cols else matrix[i][j] for j in range(len(matrix[0]))]
                for i in range(len(matrix))]

    cases = [
        # 题目示例
        [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
        [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]],
        # 1x1
        [[1]],
        [[0]],
        # 2x2 的四个角，专测「边扫边清」会不会把新写的 0 当成原始 0
        [[1, 0], [1, 1]],
        [[0, 1], [1, 1]],
        [[1, 1], [1, 0]],
        [[1, 2], [3, 4]],
        [[0, 0], [0, 0]],
        # 单行 / 单列
        [[1, 2, 3]],
        [[0, 2, 3]],
        [[1], [0], [3]],
        # 0 出现在第一行 / 第一列（用首行首列当标记区时的边界）
        [[1, 0, 3], [4, 5, 6], [7, 8, 9]],
        [[1, 2, 3], [4, 0, 6], [7, 8, 9], [0, 1, 2]],
        # 32 位边界值不能被当成 0
        [[-1, 0], [2147483647, -2147483648]],
    ]

    # 随机小数据：行列数和 0 的比例都随机，期望值由 reference 算出
    random.seed(0)
    for _ in range(500):
        m = random.randint(1, 5)
        n = random.randint(1, 5)
        cases.append([[0 if random.random() < 0.25 else random.randint(1, 9) for _ in range(n)] for _ in range(m)])

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for matrix in cases:
            expected = reference(matrix)
            ret, grid, _ = call_with_limit(cls, matrix, 1.0)
            assert ret is not TIMED_OUT, f"{cls.__name__} {matrix}: 超过 1s，可能死循环"
            assert ret is None, f"{cls.__name__} {matrix}: 应该原地修改并返回 None，得到 {ret}"
            assert grid == expected, f"{cls.__name__} {matrix}: 期望 {expected}，得到 {grid}（注意是否原地修改）"

    # 题目 m, n <= 200。只对最终解 Solution 计时，超过 0.3s 直接中断。
    # 本地实测：记录行列集合 1 ~ 3ms，首行首列当标记区 1 ~ 3ms；
    # 每个格子都去扫自己整行整列（O(mn(m+n))）194 ~ 473ms；边扫边清零不仅慢，结果还是错的
    random.seed(1)
    m = n = 200
    perf_cases = [
        ("稀疏 0", [[0 if random.random() < 0.005 else random.randint(1, 100) for _ in range(n)] for _ in range(m)]),
        ("无 0", [[random.randint(1, 100) for _ in range(n)] for _ in range(m)]),
        ("全 0", [[0] * n for _ in range(m)]),
        ("第一行全 0", [[0] * n] + [[random.randint(1, 100) for _ in range(n)] for _ in range(m - 1)]),
        ("单行很长", [[0 if random.random() < 0.01 else 5 for _ in range(m * n)]]),
    ]
    timings = []

    for name, matrix in perf_cases:
        expected = reference(matrix)
        ret, grid, elapsed = call_with_limit(Solution, matrix, 0.3)
        assert ret is not TIMED_OUT, f"Solution 大数据（{name}）超过 0.3s 被中断，可能每个格子都在重扫整行整列"
        assert ret is None, f"Solution 大数据（{name}）: 应该返回 None，得到 {ret}"
        assert grid == expected, f"Solution 大数据（{name}）: 结果不对"
        timings.append(f"{name} {elapsed * 1000:.0f} ms")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {', '.join(timings)})")
