"""
Pattern: 网格 DFS 数连通块（扫描 + 淹没）

Core:
- 每个陆地格子是一个节点，和上下左右的陆地相连；岛屿数就是连通块数。
- 外层逐格扫描，遇到 '1' 就是一座新岛：计数加 1，再从这里 DFS 把整座岛改成 '0'。之后同一座岛的其他格子都是 '0'，不会重复计数。
- dfs 开头一行挡掉越界和不是陆地的格子；进入格子时立刻改成 '0'（先标记再往四个方向走），否则会在相邻两格之间来回走。
- 原地改 grid 当 visited（题目没禁止）；不想改输入就另开 m×n 的 visited。

Time: O(mn)
Space: O(mn) 递归栈（蛇形岛屿深度约 mn/2）
实测 300×300 最慢 49.1 ms。

Mistake:
- 边界写成 r <= 0、c <= 0：0 是合法下标，第 0 行、第 0 列被当成界外，既淹不掉、也挡住了从它们出发的 DFS。
  示例 1 期望 1 得 8：(0, 0) 到 (0, 3)、(1, 0)、(2, 0) 都被单独计了一次。改成 r < 0、c < 0（用户随后自己改了）。
- 写法上：grid[r][c] != '1' 并进越界判断，elif 分支去掉；row_cnt / col_cnt → m / n，cnt → islands，row_idx / col_idx → r / c。

易错点:
- 格子里是字符串 '1'，和整数 1 比较永远不相等。
- 下标 -1 不会报错：Python 的 grid[-1] 是最后一行，下界不挡住会把第一行和最后一行连起来。
- 只往右、下两个方向走：U 形、拐回来的岛会被拆开。
- 本地 Python 3.9 主线程递归 3~6 万层会段错误：300×300 的蛇形岛递归深度约 4.5 万，测试把大网格放进大栈线程里跑。
"""


class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        m, n = len(grid), len(grid[0])

        def dfs(r: int, c: int) -> None:
            if r < 0 or r >= m or c < 0 or c >= n or grid[r][c] != '1':
                return
            grid[r][c] = '0'
            dfs(r + 1, c)
            dfs(r, c + 1)
            dfs(r - 1, c)
            dfs(r, c - 1)

        islands = 0
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell == '1':
                    islands += 1
                    dfs(r, c)
        return islands


if __name__ == "__main__":
    import gc
    import itertools
    import random
    import signal
    import sys
    import threading
    import time

    # 网格最大 300×300，蛇形岛屿的 DFS 深度能到 4.5 万。Python 3.9 主线程递归到 3~6 万层就会段错误，
    # 所以大网格放到 512 MB 栈的线程里跑（见 run_deep），递归上限放宽到 20 万
    sys.setrecursionlimit(200_000)

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()

    def parse(rows):
        """["110", "011"] → [["1", "1", "0"], ["0", "1", "1"]]，和题目输入一样是字符串。"""
        return [list(r) for r in rows]

    def show(grid):
        return [" ".join(r) for r in grid]

    def count(grid, dirs, wrap=False):
        """按给定方向数连通块（显式栈）。wrap=True 模拟下标 -1 被 Python 当成最后一行 / 最后一列。"""
        m, n = len(grid), len(grid[0])
        seen = [[False] * n for _ in range(m)]
        islands = 0
        for si in range(m):
            for sj in range(n):
                if grid[si][sj] != "1" or seen[si][sj]:
                    continue
                islands += 1
                seen[si][sj] = True
                stack = [(si, sj)]
                while stack:
                    i, j = stack.pop()
                    for di, dj in dirs:
                        a, b = i + di, j + dj
                        if wrap and (a == -1 or b == -1):
                            a, b = a % m, b % n
                        if 0 <= a < m and 0 <= b < n and grid[a][b] == "1" and not seen[a][b]:
                            seen[a][b] = True
                            stack.append((a, b))
        return islands

    FOUR = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    EIGHT = FOUR + [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    def reference(grid):
        return count(grid, FOUR)

    def guesses_for(grid, got):
        out = []
        ones = sum(r.count("1") for r in grid)
        if got == 0 and ones > 0:
            out.append("一个都没数到：grid 里是字符串 \"1\" / \"0\"，和整数 1 比较永远不相等")
        if got == ones and ones != reference(grid):
            out.append("数的是陆地格子数：每个格子都算了一个岛，没有把连在一起的标记掉")
        if got == count(grid, EIGHT):
            out.append("把斜对角也连起来了：题目只算上下左右")
        if got == count(grid, FOUR, wrap=True):
            out.append("下标 -1 没有挡住：Python 里 grid[-1] 是最后一行，第一行和最后一行（第一列和最后一列）被连起来了")
        if got > reference(grid) and not out:
            out.append("多数了：只往两个方向（右、下）走？U 形、拐回来的岛会被拆成几个")
        return out

    def call_with_limit(cls, grid, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().numIslands(grid)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_deep(cls, grid, seconds):
        """大网格在大栈线程里跑。线程里收不到 SIGALRM，超时用 join(timeout) 判断（超时线程收不回来，只能报错退出）。"""
        box = {}

        def work():
            try:
                start = time.perf_counter()
                box["got"] = cls().numIslands(grid)
                box["elapsed"] = time.perf_counter() - start
            except BaseException as e:  # 线程里的异常不会自己传出来
                box["error"] = e

        threading.stack_size(512 * 1024 * 1024)
        t = threading.Thread(target=work, daemon=True)
        t.start()
        t.join(seconds)
        threading.stack_size(0)
        if t.is_alive():
            return TIMED_OUT, None
        if "error" in box:
            raise box["error"]
        return box["got"], box["elapsed"]

    modified = set()  # 改了 grid 的类：题目没禁止、LeetCode 能过，只在最后提示一次

    def run_case(cls, name, grid, seconds=2.0, deep=False):
        m, n = len(grid), len(grid[0])
        expected = reference(grid)
        given = [row[:] for row in grid]  # 给解法一份拷贝，原网格留着算诊断
        tag = f"{cls.__name__} {name}: 输入 {show(grid) if m * n <= 30 else f'{m}×{n}'}"
        try:
            got, elapsed = (run_deep if deep else call_with_limit)(cls, given, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 20 万）") from e
        except IndexError as e:
            raise AssertionError(f"{tag}，IndexError: {e}（边界检查漏了？或者行列下标写反了：grid[i][j] 里 i 是行、范围 0..m-1）") from e
        except Exception as e:
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断：死循环？走过的格子没有标记，来回重复走？"
        assert got is not None, f"{tag}，期望 {expected}，得到 None（忘了 return？）"
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}"
        if got != expected:
            hint = "；或者".join(guesses_for(grid, got)) or "没对上常见错误"
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}（{hint}）")
        if given != grid:
            modified.add(cls.__name__)
        return elapsed

    cases = []  # (名字, grid, deep)
    for name, rows in [
        # 题目示例
        ("题目示例 1", ["11110", "11010", "11000", "00000"]),
        ("题目示例 2", ["11000", "11000", "00100", "00011"]),
        ("单格陆地", ["1"]),
        ("单格水", ["0"]),
        ("全是水", ["000", "000"]),
        ("全是陆地", ["111", "111"]),
        ("一行", ["1011001"]),
        ("一列", ["1", "0", "1", "1", "0", "1"]),
        ("斜对角不算连通", ["101", "010", "101"]),
        ("U 形：只往右、下走会拆成两个", ["101", "101", "111"]),
        ("从右上往左下拐的岛", ["001", "011", "110"]),
        ("环形，中间是水", ["111", "101", "111"]),
        ("第一行和最后一行同一列：下标 -1 会连起来", ["100", "000", "100"]),
        ("第一列和最后一列同一行：下标 -1 会连起来", ["101", "000", "000"]),
        ("不是方阵：行列写反会越界", ["11000", "00011"]),
    ]:
        cases.append((name, parse(rows), False))

    # 穷举：m×n ≤ 12 的所有网格（行、列都在 1~4，每格 0 / 1）
    for m in range(1, 5):
        for n in range(1, 5):
            if m * n > 12:
                continue
            for bits in itertools.product("01", repeat=m * n):
                grid = [list(bits[i * n:(i + 1) * n]) for i in range(m)]
                cases.append((f"穷举 {show(grid)}", grid, False))

    rng = random.Random(200)
    for i in range(150):  # 随机：1~60 行列，陆地密度 0.2~0.8
        m, n = rng.randint(1, 60), rng.randint(1, 60)
        p = rng.uniform(0.2, 0.8)
        grid = [["1" if rng.random() < p else "0" for _ in range(n)] for _ in range(m)]
        cases.append((f"随机 #{i}", grid, False))

    # 题目上限 300×300
    N = 300
    snake = [["1" if i % 2 == 0 or (i % 4 == 1 and j == N - 1) or (i % 4 == 3 and j == 0) else "0"
              for j in range(N)] for i in range(N)]
    big = [
        ("300×300 全是陆地", [["1"] * N for _ in range(N)]),
        ("300×300 蛇形，一个岛走 4.5 万格", snake),
        ("300×300 棋盘格，4.5 万个岛", [["1" if (i + j) % 2 == 0 else "0" for j in range(N)] for i in range(N)]),
        ("300×300 随机，密度 0.6", [["1" if rng.random() < 0.6 else "0" for _ in range(N)] for _ in range(N)]),
    ]

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    timings = {}
    for cls in classes:
        # 同一个实例连调两次：visited 或计数存在 self 上、没有在每次调用时新建，第二次会带着上一次的结果
        # 只在「各用一个新实例都算对」时才查，否则算法本身有错，交给下面的用例报
        a, b = ["11", "01"], ["101"]
        # 新实例连算两次同一个网格结果都不一样：状态放在类属性上，所有实例共享
        r1, r2 = cls().numIslands(parse(b)), cls().numIslands(parse(b))
        assert r1 == r2, (
            f"{cls.__name__}：两个新实例先后算同一个 {b}，第一次 {r1}、第二次 {r2}"
            "——visited 或计数放在了类属性上（class 里直接写 seen = set()），所有实例共用一份？")
        if cls().numIslands(parse(a)) == 1 and cls().numIslands(parse(b)) == 2:
            sol = cls()
            first, second = sol.numIslands(parse(a)), sol.numIslands(parse(b))
            assert (first, second) == (1, 2), (
                f"{cls.__name__}：同一个实例先算 {a}（期望 1）得 {first}，再算 {b}（期望 2）得 {second}"
                "（各用一个新实例时都对）——visited 或计数存在了 self 或类属性上、每次调用没有新建？")
        for name, grid, deep in cases:
            run_case(cls, name, grid, deep=deep)
        gc.collect()
        gc.disable()
        try:
            timings[cls.__name__] = [run_case(cls, name, grid, deep=True) for name, grid in big]
        finally:
            gc.enable()

    worst = max(max(t) for t in timings.values())
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases) + len(big)} 组用例; "
          f"300×300 最慢 {worst * 1000:.1f} ms)")
    if modified:
        print(f"提示：{', '.join(sorted(modified))} 改了输入的 grid（把陆地改成 \"0\" 当 visited）。"
              "题目没禁止、LeetCode 能过；不想改输入就另开一个 visited")
