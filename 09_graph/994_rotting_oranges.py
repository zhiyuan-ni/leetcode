"""
Pattern: 多源 BFS，按层扩散（一层 = 一分钟）

Core:
- SolutionRescan：每分钟重扫全部橘子，收集当前所有烂橘子（先收集再传染，同一分钟新烂的不会接着传），没有新烂的就停；
  minutes 从 -1 起步抵消最后空跑的一轮。O(分钟数 × 格子数)。
- Solution：rotten 一开始放所有烂橘子（同时出发），每轮只处理上一分钟刚烂的这一层，传染到的收集进 next_rotten，
  整层替换（102 的写法），一轮就是一分钟。fresh 计数代替最后的扫描：while rotten and fresh 在没有新鲜橘子时就停，
  最后 fresh > 0 说明有传不到的，返回 -1；一开始 fresh == 0 直接返回 0。

Time: 重扫 O((mn)^2)；按层 BFS O(mn)
Space: O(mn)
实测蛇形网格（分钟数约 mn/2）：
| 蛇形 N×N | 分钟数 | SolutionRescan | Solution |
| 10×10 | 54 | 0.4 ms | 0.03 ms |
| 30×30 | 464 | 25.7 ms | 0.25 ms |
| 60×60 | 1829 | 376.8 ms | 0.89 ms |
| 100×100 | 5049 | 2905.9 ms | 2.54 ms |
题目上限 10×10，两种都能过。

Mistake:
- （本题一次通过，未出错）但每分钟都从头重扫所有橘子、让所有烂橘子（包括早就烂了的）再试一遍邻居，只有上一分钟刚烂的那一层需要处理。
- 写法上：四段复制的 if 合成方向循环 + 0 <= a < m and 0 <= b < n；r+1 <= m-1 写成 r + 1 < m；cell == 1 or cell == 2 写成 cell != 0；逗号后补空格。

易错点:
- 同一分钟里新烂的不能接着传（边扫描边原地改会一分钟传到底）。
- 多个烂橘子同时出发；只从第一个出发会多算。
- 最后一轮「什么都没传到」不算一分钟；没有新鲜橘子（包括全是空格）答案是 0，传不到时是 -1。
"""


class SolutionRescan:
    def orangesRotting(self, grid: list[list[int]]) -> int:
        m,n = len(grid), len(grid[0])
        oranges = []
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell == 1 or cell == 2:
                    oranges.append((r,c))

        minutes = -1
        while True:
            rotten = []
            for r,c in oranges:
                if grid[r][c] == 2:
                    rotten.append((r,c))
            rotted = 0
            for r,c in rotten:
                if r+1 <= m-1 and grid[r+1][c] == 1:
                    grid[r+1][c] = 2
                    rotted += 1
                if c+1 <= n-1 and grid[r][c+1] == 1:
                    grid[r][c+1] = 2
                    rotted += 1
                if r-1 >= 0 and grid[r-1][c] == 1:
                    grid[r-1][c] = 2
                    rotted += 1
                if c-1 >= 0 and grid[r][c-1] == 1:
                    grid[r][c-1] = 2
                    rotted += 1
            minutes += 1
            if rotted == 0:
                for r,c in oranges:
                    if grid[r][c] == 1:
                        return -1
                return minutes


class Solution:
    def orangesRotting(self, grid: list[list[int]]) -> int:
        m, n = len(grid), len(grid[0])
        rotten = [(r, c) for r in range(m) for c in range(n) if grid[r][c] == 2]
        fresh = sum(row.count(1) for row in grid)

        minutes = 0
        while rotten and fresh:
            next_rotten = []
            for r, c in rotten:
                for a, b in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= a < m and 0 <= b < n and grid[a][b] == 1:
                        grid[a][b] = 2
                        fresh -= 1
                        next_rotten.append((a, b))
            rotten = next_rotten
            minutes += 1
        return -1 if fresh else minutes


if __name__ == "__main__":
    import itertools
    import random
    import signal
    import time

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()

    FOUR = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    EIGHT = FOUR + [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    def parse(rows):
        """["211", "110"] → [[2, 1, 1], [1, 1, 0]]，和题目输入一样是整数。"""
        return [[int(ch) for ch in r] for r in rows]

    def show(grid):
        return ["".join(map(str, r)) for r in grid]

    def spread(grid, dirs=FOUR, sources=None):
        """多源 BFS：返回 (每个格子腐烂的分钟数, 最后一个腐烂的分钟数)。sources 默认是所有初始烂橘子。"""
        m, n = len(grid), len(grid[0])
        if sources is None:
            sources = [(i, j) for i in range(m) for j in range(n) if grid[i][j] == 2]
        time_at = {s: 0 for s in sources}
        level, minute = list(sources), 0
        while level:
            nxt = []
            for i, j in level:
                for di, dj in dirs:
                    a, b = i + di, j + dj
                    if 0 <= a < m and 0 <= b < n and grid[a][b] == 1 and (a, b) not in time_at:
                        time_at[(a, b)] = minute + 1
                        nxt.append((a, b))
            if nxt:
                minute += 1
            level = nxt
        return time_at, minute

    def answer(grid, dirs=FOUR, sources=None):
        time_at, minute = spread(grid, dirs, sources)
        fresh = [(i, j) for i, r in enumerate(grid) for j, v in enumerate(r) if v == 1]
        return -1 if any(f not in time_at for f in fresh) else minute

    def reference(grid):
        return answer(grid)

    def scan_in_place(grid):
        """错误写法：每分钟按行扫描、原地把邻居改成 2，同一分钟里新烂的又接着传染下去。"""
        g = [r[:] for r in grid]
        m, n = len(g), len(g[0])
        minute = 0
        while True:
            changed = False
            for i in range(m):
                for j in range(n):
                    if g[i][j] == 2:
                        for di, dj in FOUR:
                            a, b = i + di, j + dj
                            if 0 <= a < m and 0 <= b < n and g[a][b] == 1:
                                g[a][b] = 2
                                changed = True
            if not changed:
                break
            minute += 1
        return -1 if any(1 in r for r in g) else minute

    def guesses_for(grid, got):
        expected = reference(grid)
        has_fresh = any(1 in r for r in grid)
        time_at, minute = spread(grid)
        out = []
        if not has_fresh and got != 0:
            out.append("一开始就没有新鲜橘子时答案是 0（包括整个网格都没有橘子）")
        if expected >= 0 and got == expected + 1:
            out.append("多算了一分钟：最后一层扩散完后，又把「没有新橘子腐烂」的那一轮也算进去了")
        if expected > 0 and got == expected - 1:
            out.append("少算了一分钟：分钟数在哪一步加？")
        if expected == -1 and got != -1:
            out.append("有新鲜橘子永远烂不掉时要返回 -1：BFS 结束后检查还有没有剩下的 1")
        if expected >= 0 and got == -1 and has_fresh:
            out.append("所有橘子都能烂，却返回了 -1：剩余新鲜数没减对？或者统计「剩下的 1」时网格没更新？")
        if got == answer(grid, EIGHT) and got != expected:
            out.append("把斜对角也算进去了：只有上下左右会传染")
        if got == scan_in_place(grid) and got != expected:
            out.append("同一分钟里新烂的橘子立刻又传染了别人：这一分钟要传染的只能是上一分钟结束时已经烂的（按层 BFS，或者先收集再统一改）")
        rotten = [(i, j) for i, r in enumerate(grid) for j, v in enumerate(r) if v == 2]
        if len(rotten) > 1 and got != expected:
            singles = [answer(grid, sources=[s]) for s in rotten]
            if got == answer(grid, sources=rotten[:1]):
                out.append("只从第一个烂橘子出发：所有烂橘子要同时出发（多源 BFS，一开始把它们都放进队列）")
            elif got == max(singles) or got == sum(s for s in singles if s > 0):
                out.append("每个烂橘子各自跑一遍 BFS 再合并：它们是同时传染的，一个格子取最早被传染的时间")
        return out

    def call_with_limit(cls, grid, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().orangesRotting(grid)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    modified = set()  # 改了 grid 的类：题目没禁止、LeetCode 能过，只在最后提示一次

    def run_case(cls, name, grid, seconds=2.0):
        expected = reference(grid)
        given = [row[:] for row in grid]  # 给解法一份拷贝，原网格留着算诊断
        tag = f"{cls.__name__} {name}: 输入 {show(grid)}"
        try:
            got, elapsed = call_with_limit(cls, given, seconds)
        except IndexError as e:
            raise AssertionError(f"{tag}，IndexError: {e}（边界检查漏了？或者行列下标写反了）") from e
        except Exception as e:
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断：死循环？已经烂的橘子又被放回队列？"
        assert got is not None, f"{tag}，期望 {expected}，得到 None（忘了 return？）"
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}"
        if got != expected:
            hint = "；或者".join(guesses_for(grid, got)) or "没对上常见错误"
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}（{hint}）")
        if given != grid:
            modified.add(cls.__name__)
        return elapsed

    cases = []  # (名字, grid)
    for name, rows in [
        # 题目示例
        ("题目示例 1", ["211", "110", "011"]),
        ("题目示例 2", ["211", "011", "101"]),
        ("题目示例 3", ["02"]),
        ("全是空格", ["000", "000"]),
        ("单个新鲜橘子，没有烂的", ["1"]),
        ("单个烂橘子", ["2"]),
        ("没有新鲜橘子", ["2002", "0200"]),
        ("有新鲜橘子但一个烂的都没有", ["110", "011"]),
        ("被空格隔开，传不过去", ["21", "00", "11"]),
        ("斜对角不传染", ["21", "01"]),
        ("两个烂橘子从两头同时出发", ["2111112"]),
        ("同一分钟里新烂的不能接着传", ["2111"]),
        ("一列", ["2", "1", "1", "0", "1"]),
        ("烂橘子在右下角，往左上扩散", ["111", "111", "112"]),
    ]:
        cases.append((name, parse(rows)))

    # 穷举：m×n ≤ 8 的所有网格（行、列都在 1~4，每格 0 / 1 / 2）
    for m in range(1, 5):
        for n in range(1, 5):
            if m * n > 8:
                continue
            for cells in itertools.product((0, 1, 2), repeat=m * n):
                grid = [list(cells[i * n:(i + 1) * n]) for i in range(m)]
                cases.append((f"穷举 {show(grid)}", grid))

    rng = random.Random(994)
    for i in range(300):  # 随机：题目上限 10×10，烂橘子少、新鲜多，传得更远
        m, n = rng.randint(1, 10), rng.randint(1, 10)
        grid = [[rng.choices((0, 1, 2), (0.2, 0.75, 0.05))[0] for _ in range(n)] for _ in range(m)]
        cases.append((f"随机 #{i}", grid))

    # 10×10 蛇形：唯一的烂橘子在一头，要走完整条蛇
    snake = [[1 if i % 2 == 0 or (i % 4 == 1 and j == 9) or (i % 4 == 3 and j == 0) else 0 for j in range(10)] for i in range(10)]
    snake[0][0] = 2
    cases.append(("10×10 蛇形，从一头烂到另一头", snake))
    cases.append(("10×10 全是新鲜，左上角一个烂的", [[2 if i == j == 0 else 1 for j in range(10)] for i in range(10)]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 新实例算同一个网格，中间夹一次别的网格，结果就变了：状态放在类属性上，所有实例共享
        a, b = ["211"], ["21", "01"]
        c, d = ["11", "21"], ["112"]
        r1 = cls().orangesRotting(parse(c))
        cls().orangesRotting(parse(d))
        r2 = cls().orangesRotting(parse(c))
        assert r1 == r2, (
            f"{cls.__name__}：新实例算 {c} 得 {r1}；中间用另一个新实例算了 {d}，再用新实例算 {c} 得 {r2}"
            "——队列、visited 或计数放在了类属性上（class 里直接写），所有实例共用一份？")
        # 同一个实例连调两次：状态存在 self 上、没有在每次调用时新建
        if cls().orangesRotting(parse(a)) == 2 and cls().orangesRotting(parse(b)) == 1:
            sol = cls()
            first, second = sol.orangesRotting(parse(a)), sol.orangesRotting(parse(b))
            assert (first, second) == (2, 1), (
                f"{cls.__name__}：同一个实例先算 {a}（期望 2）得 {first}，再算 {b}（期望 1）得 {second}"
                "（各用一个新实例时都对）——状态存在了 self 上、每次调用没有新建？")
        for name, grid in cases:
            run_case(cls, name, grid)

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
    if modified:
        print(f"提示：{', '.join(sorted(modified))} 改了输入的 grid（把新鲜橘子改成 2 当 visited）。"
              "题目没禁止、LeetCode 能过；不想改输入就另开一个 visited")
