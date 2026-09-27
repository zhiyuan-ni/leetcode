"""
Pattern: 矩阵分层剥壳

Core:
维护 top / bottom / left / right 四个边界，每圈依次走顶边（左到右）、右边（上到下）、底边（右到左）、左边（下到上），每走完一条边就把对应边界往里收一格，循环条件 top <= bottom and left <= right。
剥到只剩一行或一列时，底边和左边会把同一批元素再走一遍，所以走底边前要再判 top <= bottom，走左边前要再判 left <= right。

Time: O(mn)
Space: O(1)（不算输出）

Mistake:
- 第一版想把答案拆成「行下标序列」和「列下标序列」，最后用双重循环组合：螺旋顺序是一条路径，第 k 个元素的行列是成对的，笛卡尔积会产生 len(row) * len(col) 个元素。3x3 的正确路径是 (0,0)(0,1)(0,2)(1,2)(2,2)(2,1)(2,0)(1,0)(1,1)，无法由两个独立序列拼出。
- 同一个列表里混放列表和整数（row.append([[i] * k]) 又 row.append(n//2 + 1)），len(row) 的含义变得不明确；res.append([matrix[i][j]]) 还把每个值包成了单元素列表，而题目要扁平列表。
- 用负数下标表示「从末尾数」并和正下标混用，-(m-2*i)-2 这类边界表达式无法验证。

易错点:
- 后两条边必须二次判断边界，否则单行 / 单列会重复输出：示例二 [[1,2,3,4],[5,6,7,8],[9,10,11,12]] 会多出一个 6。
- 走底边前判 top <= bottom、走左边前判 left <= right 就够了，两个条件都判并不错，但多了一半。
"""


class Solution:
    def spiralOrder(self, matrix: list[list[int]]) -> list[int]:
        top = left = 0
        bottom = len(matrix) - 1
        right = len(matrix[0]) - 1
        res = []
        while top <= bottom and left <= right:
            for c in range(left, right + 1):
                res.append(matrix[top][c])
            top += 1

            for r in range(top, bottom + 1):
                res.append(matrix[r][right])
            right -= 1

            if top <= bottom:
                for c in range(right, left - 1, -1):
                    res.append(matrix[bottom][c])
                bottom -= 1

            if left <= right:
                for r in range(bottom, top - 1, -1):
                    res.append(matrix[r][left])
                left += 1
        return res


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
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().spiralOrder([row[:] for row in matrix])
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(matrix):
        # 用 visited 标记逐格走，撞墙或撞到走过的格子就右转。和分层剥壳是两套独立逻辑
        m, n = len(matrix), len(matrix[0])
        seen = [[False] * n for _ in range(m)]
        dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        r = c = d = 0
        res = []
        for _ in range(m * n):
            res.append(matrix[r][c])
            seen[r][c] = True
            nr, nc = r + dirs[d][0], c + dirs[d][1]
            if not (0 <= nr < m and 0 <= nc < n and not seen[nr][nc]):
                d = (d + 1) % 4
                nr, nc = r + dirs[d][0], c + dirs[d][1]
            r, c = nr, nc
        return res

    cases = [
        # 题目示例
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1, 2, 3, 6, 9, 8, 7, 4, 5]),
        ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]], [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]),
        # 1x1
        ([[7]], [7]),
        # 单行 / 单列：剥到最后一层时，缺少二次边界判断会重复走
        ([[1, 2, 3]], [1, 2, 3]),
        ([[1], [2], [3]], [1, 2, 3]),
        # 2x2 / 2x3 / 3x2
        ([[1, 2], [3, 4]], [1, 2, 4, 3]),
        ([[1, 2, 3], [4, 5, 6]], [1, 2, 3, 6, 5, 4]),
        ([[1, 2], [3, 4], [5, 6]], [1, 2, 4, 6, 5, 3]),
        # 负数和重复值
        ([[-1, -2], [-3, -3]], [-1, -2, -3, -3]),
        ([[0, 0], [0, 0]], [0, 0, 0, 0]),
    ]

    # 穷举 1..8 行 x 1..8 列的所有形状，期望值由 reference 算出
    for m in range(1, 9):
        for n in range(1, 9):
            grid = [[r * n + c + 1 for c in range(n)] for r in range(m)]
            cases.append((grid, reference(grid)))

    # 随机小数据（含负数、重复值）
    random.seed(0)
    for _ in range(300):
        m = random.randint(1, 10)
        n = random.randint(1, 10)
        grid = [[random.randint(-100, 100) for _ in range(n)] for _ in range(m)]
        cases.append((grid, reference(grid)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for matrix, expected in cases:
            got, _ = call_with_limit(cls, matrix, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {matrix}: 超过 1s，可能死循环"
            assert got is not None, f"{cls.__name__} {matrix}: 返回了 None"
            assert list(got) == expected, f"{cls.__name__} {matrix}: 期望 {expected}，得到 {got}"

    # 题目只给到 m, n <= 10，这里放大到 200x300 是为了拦住「每取一个元素都重建矩阵」之类的写法。
    # 本地实测：分层剥壳 2ms，visited 逐格走 8ms，剥第一行 + 旋转剩余部分 30ms
    m, n = 200, 300
    big = [[r * n + c for c in range(n)] for r in range(m)]
    expected = reference(big)
    got, elapsed = call_with_limit(Solution, big, 1.0)
    assert got is not TIMED_OUT, "Solution 大数据（200x300）超过 1s 被中断"
    assert got is not None, "Solution 大数据（200x300）: 返回了 None"
    assert list(got) == expected, "Solution 大数据（200x300）: 结果不对"

    print(f"ok ({', '.join(c.__name__ for c in classes)}; 200x300 {elapsed * 1000:.0f} ms)")
