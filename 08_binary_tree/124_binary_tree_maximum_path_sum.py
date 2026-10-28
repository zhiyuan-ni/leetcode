"""
Pattern: 二叉树后序递归，返回值同时带两种信息（543 的带负数版本）

Core:
- 任意路径都有一个最高点 x：路径 = 左边往下的一条 + x + 右边往下的一条（两边都可以为空）。
- dfs(node) 返回 (best, down)：best 是子树里最好的路径和，down 是从 node 出发往下最好的一条。
  down = node.val + max(左 down, 右 down, 0)：往上只能带一边，负的贡献不要。
  best = max(node.val + max(左 down, 0) + max(右 down, 0), 左 best, 右 best)：在这里拐弯，或者答案在某棵子树里。
- 空节点返回 (-inf, 0)：空树里没有路径，best 不能是 0（全负数的树答案是负数）；往下的贡献是空路径 0。

Time: O(n)
Space: O(h) 递归栈
实测 3×10^4 个节点（链和随机树）最慢 15.1 ms。

Mistake:
- down 漏了节点自己：part = max(left_max, right_max, 0)，每个节点交给父节点的都是 0，示例 1 [1, 2, 3] 期望 6 得 1。
- 用 _ 丢掉了子树的 best，只剩根的「在这里拐弯」，等于只算经过根的路径：示例 2 期望 42（15 → 20 → 7）得 34。
- 子树 best 往上传以后，空节点的 best 还是 0：[-3] 期望 -3 得 0；改成 -inf。三处都是用户自己改的。
- 命名：max_path_sum_internal → dfs，cur / part → best / down，left_max → left_down。

易错点:
- 往上返回时不能把左右两边都带上（路径分叉）；两边都要只能在当前节点拐弯、记进 best。
- 答案初值 / 空树的 best 不能是 0。
"""


from __future__ import annotations

# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right


class Solution:
    def maxPathSum(self, root: TreeNode | None) -> int:
        def dfs(node: TreeNode | None) -> tuple[float, int]:
            """返回 (子树里最好的路径和, 从 node 出发往下最好的一条)。空树没有路径，best 为 -inf。"""
            if not node:
                return float("-inf"), 0
            left_best, left_down = dfs(node.left)
            right_best, right_down = dfs(node.right)
            best = max(node.val + max(left_down, 0) + max(right_down, 0), left_best, right_best)
            down = node.val + max(left_down, right_down, 0)
            return best, down

        return dfs(root)[0]

if __name__ == "__main__":
    import gc
    import itertools
    import random
    import signal
    import sys
    import threading
    import time

    if "TreeNode" not in globals():
        class TreeNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, left=None, right=None):
                self.val = val
                self.left = left
                self.right = right

    # 节点数上限 3×10^4，链状树深 3×10^4。Python 3.9 主线程递归到 3~6 万层就会段错误，
    # 所以深链放到 512 MB 栈的线程里跑（见 run_deep），递归上限放宽到 10 万
    sys.setrecursionlimit(100_000)

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()

    def from_level(vals):
        """LeetCode 的层序格式（None 表示空位）→ root。"""
        if not vals or vals[0] is None:
            return None
        it = iter(vals)
        root = TreeNode(next(it))
        queue, i = [root], 0
        while i < len(queue):
            node = queue[i]
            i += 1
            for side in ("left", "right"):
                v = next(it, StopIteration)
                if v is StopIteration:
                    return root
                if v is not None:
                    child = TreeNode(v)
                    setattr(node, side, child)
                    queue.append(child)
        return root

    def to_level(root):
        """TreeNode → LeetCode 的层序格式，出错时用来显示树的形状。"""
        out, queue, i = [], [root], 0
        while i < len(queue):
            node = queue[i]
            i += 1
            out.append(None if node is None else node.val)
            if node is not None:
                queue += [node.left, node.right]
        while out and out[-1] is None:
            out.pop()
        return out

    def from_shape(shape, vals):
        """shape 是 (编号, 左子树 shape, 右子树 shape)。用显式栈建树。"""
        holder = TreeNode()
        stack = [(shape, holder, "left")]
        while stack:
            s, parent, side = stack.pop()
            if s is None:
                continue
            idx, left, right = s
            node = TreeNode(vals[idx])
            setattr(parent, side, node)
            stack.append((left, node, "left"))
            stack.append((right, node, "right"))
        return holder.left

    def all_shapes(lo, hi):
        """中序下标 lo..hi-1 能组成的所有二叉树形状（卡特兰数个）。"""
        if lo == hi:
            return [None]
        out = []
        for r in range(lo, hi):
            for left in all_shapes(lo, r):
                for right in all_shapes(r + 1, hi):
                    out.append((r, left, right))
        return out

    def random_shape(n, rng):
        """n 个节点的随机形状：不递归，逐个把节点挂到随机的空位上。"""
        root = [0, None, None]
        slots = [(root, 1), (root, 2)]
        for i in range(1, n):
            parent, side = slots.pop(rng.randrange(len(slots)))
            child = [i, None, None]
            parent[side] = child
            slots += [(child, 1), (child, 2)]

        def freeze(node):  # list → tuple，用显式栈避免深递归
            done = {}
            stack = [(node, False)]
            while stack:
                cur, ready = stack.pop()
                if cur is None:
                    continue
                if ready:
                    done[id(cur)] = (cur[0], done.get(id(cur[1])), done.get(id(cur[2])))
                else:
                    stack += [(cur, True), (cur[1], False), (cur[2], False)]
            return done[id(node)]

        return freeze(root)

    def chain(n, side):
        shape = None
        for i in range(n):
            shape = (i, shape, None) if side == "left" else (n - 1 - i, None, shape)
        return shape

    def post_order(root):
        """后序（子节点在父节点之前）的节点列表，显式栈。"""
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            out.append(node)
            stack += [c for c in (node.left, node.right) if c is not None]
        return out[::-1]

    def variants(root):
        """按定义算正确答案，顺带算几种常见错误写法会得到的值，用来诊断。全部显式栈。"""
        gain, raw, fork = {None: 0}, {None: 0}, {None: 0}
        best = best_raw = best_fork = -float("inf")
        for node in post_order(root):
            gl, gr = max(0, gain[node.left]), max(0, gain[node.right])
            gain[node] = node.val + max(gl, gr)  # 往上只能带一边，负的不要
            best = max(best, node.val + gl + gr)  # 在这个节点拐弯
            # 错误 1：子树的贡献是负数也照样加（空子树当 0）
            rl, rr = raw[node.left], raw[node.right]
            raw[node] = node.val + max(rl, rr)
            best_raw = max(best_raw, node.val + rl + rr)
            # 错误 2：往上返回时把两边都带上（路径分叉了）
            fork[node] = node.val + max(0, fork[node.left]) + max(0, fork[node.right])
            best_fork = max(best_fork, fork[node])
        return {
            "expected": best,
            "不截断负贡献": best_raw,
            "往上返回两边": best_fork,
            "只算经过根": root.val + max(0, gain[root.left]) + max(0, gain[root.right]),
            "只算从根往下": gain[root],
            "答案初值为 0": max(0, best),
        }

    GUESSES = {
        "不截断负贡献": "子树的贡献是负数时也加上了：负的那一边应该不要（和 0 取 max）",
        "往上返回两边": "往上返回时把左右两边都带上了：路径不能分叉，往上只能带一边；两边都要的情况只能在当前节点拐弯、记进答案",
        "只算经过根": "只算了经过根的路径：路径可以在任意节点拐弯，每个节点都要更新答案",
        "只算从根往下": "返回的是「从根往下的一条」：答案要在每个节点算「左 + 自己 + 右」并取最大",
        "答案初值为 0": "答案初值写成了 0：节点全为负时答案是负数（最大的那个节点自己）；初值用 -inf 或根的值",
    }

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().maxPathSum(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_deep(cls, root, seconds):
        """深链在大栈线程里跑。线程里收不到 SIGALRM，超时用 join(timeout) 判断（超时线程收不回来，只能报错退出）。"""
        box = {}

        def work():
            try:
                start = time.perf_counter()
                box["got"] = cls().maxPathSum(root)
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

    def run_case(cls, name, root, seconds=2.0, deep=False):
        before = to_level(root)
        n = len(post_order(root))
        v = variants(root)
        expected = v["expected"]
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}"
        try:
            got, elapsed = (run_deep if deep else call_with_limit)(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 10 万）") from e
        except Exception as e:
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, (
            f"{tag}，超过 {seconds}s 被中断：死循环？或者对每个节点都重新算一遍子树（O(n^2)）？")
        assert got is not None, f"{tag}，期望 {expected}，得到 None（忘了 return？）"
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}（答案初值用了 -inf 却没被更新？或者返回了 float）"
        if got != expected:
            guesses = [GUESSES[k] for k in GUESSES if v[k] == got]
            hint = "；或者".join(guesses) if guesses else "没对上常见错误"
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}（{hint}）")
        assert to_level(root) == before, f"{tag}，调用后树被改了"
        return elapsed

    cases = []  # (名字, root, deep)
    for name, level in [
        # 题目示例
        ("题目示例 1", [1, 2, 3]),
        ("题目示例 2", [-10, 9, 20, None, None, 15, 7]),
        ("单节点", [5]),
        ("单个负节点", [-3]),
        ("全是负数：答案是最大的那个节点", [-3, -1, -2]),
        ("路径不经过根", [-10, 2, None, 3, 4]),
        ("一边是负的，不要它", [2, -1, 3]),
        ("负数子树下面藏着大正数", [1, -2, 3, 10, None, None, None]),
        ("在中间节点拐弯", [-5, 4, None, 3, 2]),
        ("拐弯后不能再往上走", [10, 2, None, 20, 1]),
        ("值的上下限", [-1000, 1000, -1000, None, None, -1000, 1000]),
    ]:
        cases.append((name, from_level(level), False))

    # 穷举：1~5 个节点的所有形状 × 每个节点取 -3 / -1 / 2（约 1.2 万组）
    for n in range(1, 6):
        for shape in all_shapes(0, n):
            for vals in itertools.product((-3, -1, 2), repeat=n):
                root = from_shape(shape, list(vals))
                cases.append((f"穷举 {to_level(root)}", root, False))

    rng = random.Random(124)
    for i in range(150):  # 随机：1~3000 个节点，值在 ±1000 里，混一些「大部分为负」的树
        n = rng.choice([rng.randint(1, 30), rng.randint(1, 3000)])
        lo = rng.choice([-1000, -1000, -10])
        vals = [rng.randint(lo, 1000) if rng.random() < 0.6 else rng.randint(-1000, -1) for _ in range(n)]
        cases.append((f"随机 #{i}", from_shape(random_shape(n, rng), vals), False))

    big = []  # 题目上限 3×10^4 个节点
    n = 30_000
    for side in ("left", "right"):
        tag = "左" if side == "left" else "右"
        big.append((f"3×10^4 的链（全往{tag}），全是 1000", from_shape(chain(n, side), [1000] * n), True))
        big.append((f"3×10^4 的链（全往{tag}），全是 -1000", from_shape(chain(n, side), [-1000] * n), True))
        big.append((f"3×10^4 的链（全往{tag}），随机值", from_shape(chain(n, side), [rng.randint(-1000, 1000) for _ in range(n)]), True))
    big.append(("3×10^4 个节点的随机树", from_shape(random_shape(n, rng), [rng.randint(-1000, 1000) for _ in range(n)]), True))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    timings = {}
    for cls in classes:
        # 同一个实例连调两次：答案存在 self 上、没有在每次调用时重置，第二次会带着上一次的结果
        # 只在「各用一个新实例都算对」时才查，否则算法本身有错，交给下面的用例报
        a, b = from_level([1, 2, 3]), from_level([-3])
        if cls().maxPathSum(a) == 6 and cls().maxPathSum(b) == -3:
            sol = cls()
            first, second = sol.maxPathSum(a), sol.maxPathSum(b)
            assert (first, second) == (6, -3), (
                f"{cls.__name__}：同一个实例先算 [1, 2, 3]（期望 6）得 {first}，再算 [-3]（期望 -3）得 {second}"
                "（各用一个新实例时都对）——答案存在了 self 或类属性上、每次调用没有重置？")
        for name, root, deep in cases:
            run_case(cls, name, root, deep=deep)
        gc.collect()
        gc.disable()
        try:
            timings[cls.__name__] = [run_case(cls, name, root, deep=deep) for name, root, deep in big]
        finally:
            gc.enable()

    worst = max(max(t) for t in timings.values())
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases) + len(big)} 组用例; "
          f"3×10^4 个节点最慢 {worst * 1000:.1f} ms)")
