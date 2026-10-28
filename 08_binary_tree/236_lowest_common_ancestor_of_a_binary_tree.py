"""
Pattern: 后序遍历，子树把「找到的 p / q / 答案」往上传

Core:
- lowestCommonAncestor(node) 返回：子树里 p、q 都有 → 它们的最近公共祖先；只有一个 → 那个节点；都没有 → None。
- 遇到 None、p 或 q 直接返回自己：另一个若在它下面，答案就是它；若不在，上层会从别的分支找到。
- 后序位置合并：左右都非空，说明 p、q 分在两边，当前节点就是答案；否则把非空的那个原样往上传（left or right）。
  上层不需要区分传上来的是「答案」还是「p / q 之一」：一旦找到答案，另一边一定是 None，答案会一路原样传到根。

Time: O(n)
Space: O(h) 递归栈
实测 10^5 个节点（链和随机树）最慢 23.6 ms。

Mistake:
- （本题一次通过，未出错）写法上：开头 None / p / q 三个分支返回的都是 root，合成一行；
  结尾三个 elif 合成 if left and right: return root / return left or right（节点对象恒为真，不会被值为 0 误判）。

易错点:
- 必须返回树里原来的节点，用 is 比较节点、不要比 .val 的真假（值为 0 的节点）。
- 链深可达 10^5：本地 Python 3.9 主线程递归 3~6 万层会段错误，测试把深链放在大栈线程里跑。
"""


from __future__ import annotations

# class TreeNode:
#     def __init__(self, x):
#         self.val = x
#         self.left = None
#         self.right = None


class Solution:
    def lowestCommonAncestor(self, root: "TreeNode", p: "TreeNode", q: "TreeNode") -> "TreeNode":
        if root is None or root is p or root is q:
            return root
        left = self.lowestCommonAncestor(root.left, p, q)
        right = self.lowestCommonAncestor(root.right, p, q)
        if left and right:
            return root
        return left or right


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
            def __init__(self, x):
                self.val = x
                self.left = None
                self.right = None

    # 节点数上限 10^5，链状树深 10^5。Python 3.9 主线程递归到 3~6 万层就会段错误，
    # 所以深链放到 512 MB 栈的线程里跑（见 run_deep），递归上限放宽到 30 万
    sys.setrecursionlimit(300_000)

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()

    def from_level(vals):
        """LeetCode 的层序格式（None 表示空位）→ (root, 值 -> 节点)。"""
        if not vals or vals[0] is None:
            return None, {}
        it = iter(vals)
        root = TreeNode(next(it))
        by_val, queue, i = {root.val: root}, [root], 0
        while i < len(queue):
            node = queue[i]
            i += 1
            for side in ("left", "right"):
                v = next(it, StopIteration)
                if v is StopIteration:
                    return root, by_val
                if v is not None:
                    child = TreeNode(v)
                    setattr(node, side, child)
                    queue.append(child)
                    by_val[v] = child
        return root, by_val

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
        """shape 是 (编号, 左子树 shape, 右子树 shape)。返回 (root, 编号 -> 节点)。用显式栈建树。"""
        by_idx = {}
        holder = TreeNode(None)
        stack = [(shape, holder, "left")]
        while stack:
            s, parent, side = stack.pop()
            if s is None:
                continue
            idx, left, right = s
            node = TreeNode(vals[idx])
            setattr(parent, side, node)
            by_idx[idx] = node
            stack.append((left, node, "left"))
            stack.append((right, node, "right"))
        return holder.left, by_idx

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
        if n == 0:
            return None
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

    def parents_of(root):
        """节点 → 父节点（根的父节点是 None），显式栈。"""
        parent, stack = {root: None}, [root]
        while stack:
            node = stack.pop()
            for child in (node.left, node.right):
                if child is not None:
                    parent[child] = node
                    stack.append(child)
        return parent

    def ancestors(node, parent):
        """node 自己加上它的所有祖先，从下往上。"""
        out = []
        while node is not None:
            out.append(node)
            node = parent[node]
        return out

    def reference(root, p, q):
        """用父指针往上走：p 的祖先集合里，q 往上第一个碰到的就是答案。和递归写法是两套逻辑。"""
        parent = parents_of(root)
        up_p = set(ancestors(p, parent))
        return next(x for x in ancestors(q, parent) if x in up_p)

    def call_with_limit(cls, root, p, q, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().lowestCommonAncestor(root, p, q)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_deep(cls, root, p, q, seconds):
        """深链在大栈线程里跑。线程里收不到 SIGALRM，超时用 join(timeout) 判断（超时线程收不回来，只能报错退出）。"""
        box = {}

        def work():
            try:
                start = time.perf_counter()
                box["got"] = cls().lowestCommonAncestor(root, p, q)
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

    def run_case(cls, name, root, p, q, seconds=2.0, deep=False):
        parent = parents_of(root)
        n = len(parent)
        before = to_level(root)
        expected = reference(root, p, q)
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}，p={p.val}，q={q.val}"
        try:
            got, elapsed = (run_deep if deep else call_with_limit)(cls, root, p, q, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 30 万）") from e
        except Exception as e:
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, (
            f"{tag}，超过 {seconds}s 被中断：死循环？或者对每个节点都重新搜一遍子树（O(n^2)）？")
        assert got is not None, f"{tag}，期望值为 {expected.val} 的节点，得到 None（忘了 return，或者某一层的返回值没接住？）"
        assert isinstance(got, TreeNode), f"{tag}，应返回树里的节点（TreeNode），得到 {got!r}（返回了 val？）"
        if got is not expected:
            guesses = []
            if got not in parent:
                guesses.append(f"返回的节点不在这棵树里（值 {got.val}）：新建了一个节点？应该返回树里原来的那个")
            elif got is root:
                guesses.append("直接返回了根：只有 p、q 分在根的两边（或其中一个就是根）时才对")
            elif got is p or got is q:
                guesses.append(f"返回了 {'p' if got is p else 'q'} 本身：只有它是另一个的祖先时才对")
            elif got in ancestors(expected, parent):
                guesses.append(f"返回的值 {got.val} 是公共祖先，但不是最近的那个")
            else:
                guesses.append(f"返回的值 {got.val} 不是 p、q 的公共祖先")
            raise AssertionError(f"{tag}，期望值为 {expected.val} 的节点，得到值为 {got.val} 的节点（" + "；".join(guesses) + "）")
        assert to_level(root) == before, f"{tag}，调用后树被改了"
        return elapsed

    cases = []  # (名字, root, p, q, deep)
    for name, level, pv, qv in [
        # 题目示例
        ("题目示例 1", [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1),
        ("题目示例 2", [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4),
        ("题目示例 3", [1, 2], 1, 2),
        ("q 是 p 的祖先（顺序反过来）", [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 4, 5),
        ("两个都在左子树深处", [3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 7, 6),
        ("最近公共祖先是值为 0 的节点", [1, 0, 2, -1, 3], -1, 3),
        ("p 是值为 0 的根", [0, -1, 2], 0, 2),
        ("值很大", [-1000000000, 1000000000, 7, 999999999, 5], 999999999, 5),
    ]:
        root, by_val = from_level(level)
        cases.append((name, root, by_val[pv], by_val[qv], False))

    # 穷举：2~7 个节点的所有形状 × 所有无序节点对（p、q 两种顺序都测）。值里故意有 0 和负数
    for n in range(2, 8):
        vals = [i - n // 2 for i in range(n)]
        for shape in all_shapes(0, n):
            root, by_idx = from_shape(shape, vals)
            for i, j in itertools.combinations(range(n), 2):
                cases.append((f"穷举 {to_level(root)}", root, by_idx[i], by_idx[j], False))
                cases.append((f"穷举 {to_level(root)}", root, by_idx[j], by_idx[i], False))

    rng = random.Random(236)
    for i in range(80):  # 随机：值互不相同，在 ±10^9 里取
        n = rng.choice([rng.randint(2, 50), rng.randint(2, 3000)])
        vals = rng.sample(range(-10**9, 10**9 + 1), n)
        root, by_idx = from_shape(random_shape(n, rng), vals)
        a, b = rng.sample(range(n), 2)
        cases.append((f"随机 #{i}", root, by_idx[a], by_idx[b], False))

    big = []  # 题目上限 10^5 个节点
    for side in ("left", "right"):
        n = 100_000
        root, by_idx = from_shape(chain(n, side), list(range(n)))
        # chain 的编号是中序：全往左时最深的是 0、根是 n-1；全往右时根是 0、最深的是 n-1
        deepest, above = (0, 1) if side == "left" else (n - 1, n - 2)
        tag = "左" if side == "left" else "右"
        big.append((f"10^5 的链（全往{tag}），p、q 是最深的两个", root, by_idx[deepest], by_idx[above], True))
        big.append((f"10^5 的链（全往{tag}），p 是根、q 最深", root, root, by_idx[deepest], True))
    n = 100_000
    root, by_idx = from_shape(random_shape(n, rng), rng.sample(range(-10**9, 10**9 + 1), n))
    a, b = rng.sample(range(n), 2)
    big.append(("10^5 个节点的随机树", root, by_idx[a], by_idx[b], True))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    timings = {}
    for cls in classes:
        # 同一个实例连调两次：答案或中间状态存在 self 上、没有在每次调用时清空，第二次会带着上一次的结果
        # 只在「各用一个新实例都算对」时才查，否则算法本身有错，交给下面的用例报
        a_root, a_by = from_level([3, 5, 1])
        b_root, b_by = from_level([7, 8, None, 9])
        if (cls().lowestCommonAncestor(a_root, a_by[5], a_by[1]) is a_root
                and cls().lowestCommonAncestor(b_root, b_by[8], b_by[9]) is b_by[8]):
            sol = cls()
            first = sol.lowestCommonAncestor(a_root, a_by[5], a_by[1])
            second = sol.lowestCommonAncestor(b_root, b_by[8], b_by[9])
            assert first is a_root and second is b_by[8], (
                f"{cls.__name__}：同一个实例先算 [3, 5, 1] 的 (5, 1)（期望 3）得 {getattr(first, 'val', first)}，"
                f"再算 [7, 8, None, 9] 的 (8, 9)（期望 8）得 {getattr(second, 'val', second)}"
                "（各用一个新实例时都对）——状态存在了 self 或类属性上、每次调用没有清空？")
        for name, root, p, q, deep in cases:
            run_case(cls, name, root, p, q, deep=deep)
        gc.collect()
        gc.disable()
        try:
            timings[cls.__name__] = [run_case(cls, name, root, p, q, deep=deep) for name, root, p, q, deep in big]
        finally:
            gc.enable()

    worst = max(max(t) for t in timings.values())
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases) + len(big)} 组用例; "
          f"10^5 个节点最慢 {worst * 1000:.1f} ms)")
