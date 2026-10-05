"""
Pattern: BST 中序遍历（栈 + cur），数到第 k 个就停

Core:
- 二叉搜索树的中序遍历严格递增，第 k 小就是中序访问到的第 k 个节点。
- 用 94 的迭代写法：cur 非空就压栈往左；为空就弹出——每弹出一个就是中序的下一个，k 减 1，减到 0 直接返回。
  不需要存遍历结果，也不用考虑「怎么从递归里跳出来」。题目保证 1 <= k <= n，循环里一定会返回。

Time: O(h + k)
Space: O(h)
实测：平衡的 1 万个节点找第 1 小只读 13 次子节点指针（把整棵树中序存下来要读 2 万次）；1 万个节点的链 0.3 ms。

Mistake:
- （本题一次通过，未出错）写法上：用 res 列表存下走过的所有值，只为了 len(res) == k 和 res[-1]，换成把 k 递减到 0 的计数；
  循环后的 return -1 在所有合法的 k 下都执行不到（1~59 个节点、全部 1770 种 k，执行 0 次），删掉。

易错点:
- 下标差一：排序后第 k 小在下标 k - 1。
- 递归计数不能用 int 参数往下传（加 1 带不回来），也不能存在类属性里（多次调用会接着上一次数）。
- 进阶：频繁插入删除时，给每个节点记录子树大小，按大小决定往左还是往右，单次查询 O(h)。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def kthSmallest(self, root: TreeNode | None, k: int) -> int:
        stack = []
        cur = root
        while cur or stack:
            if cur:
                stack.append(cur)
                cur = cur.left
            else:
                cur = stack.pop()
                k -= 1
                if k == 0:
                    return cur.val
                cur = cur.right


if __name__ == "__main__":
    import random
    import signal
    import sys
    import time

    if "TreeNode" not in globals():
        class TreeNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, left=None, right=None):
                self.val = val
                self.left = left
                self.right = right

    # 节点数上限 1 万，链状树深 1 万；和 104 一样把递归上限放宽到 2 万
    sys.setrecursionlimit(20_000)

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return 得到 None」区分开

    def from_level(vals):
        """LeetCode 的层序格式（None 表示空位）→ (root, nodes)。"""
        if not vals or vals[0] is None:
            return None, []
        it = iter(vals)
        root = TreeNode(next(it))
        nodes, queue, i = [root], [root], 0
        while i < len(queue):
            node = queue[i]
            i += 1
            for side in ("left", "right"):
                v = next(it, StopIteration)
                if v is StopIteration:
                    return root, nodes
                if v is not None:
                    child = TreeNode(v)
                    setattr(node, side, child)
                    queue.append(child)
                    nodes.append(child)
        return root, nodes

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
        holder = TreeNode()
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

    def call_with_limit(cls, root, k, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().kthSmallest(root, k)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_case(cls, name, root, vals, k, seconds=1.0, hint="可能死循环，或者复杂度太高（O(n^2) 在 1 万个节点上要好几秒）"):
        """vals 是树里所有的值；期望值直接取 sorted(vals)[k-1]，不走树。"""
        n = len(vals)
        before = to_level(root) if n <= 15 else None
        ordered = sorted(vals)
        expected = ordered[k - 1]
        tag = f"{cls.__name__} {name}: 输入 {before if before is not None else f'{n} 个节点'}，k={k}"
        try:
            got, elapsed = call_with_limit(cls, root, k, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:  # 下标越界、访问 None.val 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        if isinstance(got, TreeNode):
            raise AssertionError(f"{tag}，返回的是节点对象，要返回节点的值 .val")
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}"
        if got != expected:
            guess = ""
            if k < n and got == ordered[k]:
                guess = "（这是第 k+1 小：下标差一，第 k 小是排序后的下标 k-1）"
            elif k > 1 and got == ordered[k - 2]:
                guess = "（这是第 k-1 小：计数差一）"
            elif got == ordered[0] and k > 1:
                guess = "（得到的是最小值：计数没有在递归的各层之间共享？用 int 参数往下传，加 1 传不回来）"
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}{guess}")
        assert to_level(root) == before or before is None, f"{tag}，调用后树被改了"
        return elapsed

    def bst_from_shape(shape, n, rng=None, spread=1):
        """先按形状建树，再按中序把严格递增的值依次填进去，得到一棵合法 BST。
        （random_shape 的编号是建树顺序、不是中序下标，所以不能直接按编号填值）"""
        if rng is None:
            vals = [i * spread for i in range(n)]
        else:
            vals = sorted(rng.sample(range(0, 10_001), n))
        root, _ = from_shape(shape, [0] * n)
        stack, cur, i = [], root, 0
        while cur or stack:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            cur.val = vals[i]
            i += 1
            cur = cur.right
        return root, vals

    cases = []
    for name, level, k in [
        # 题目示例：期望值由 sorted(值)[k-1] 直接算出
        ("题目示例 1", [3, 1, 4, None, 2], 1),
        ("题目示例 2", [5, 3, 6, 2, 4, None, None, 1], 3),
        ("单节点", [7], 1),
        ("k 等于节点数（最大值）", [5, 3, 6, 2, 4, None, None, 1], 6),
        ("最小值在很深的左边", [10, 5, None, 3, None, 1], 1),
        ("值包含 0", [2, 0, 3, None, 1], 2),
    ]:
        root, nodes = from_level(level)
        cases.append((name, root, [nd.val for nd in nodes], k))

    # 穷举：1~6 个节点的所有形状 × 所有 k（共 1+4+15+56+210+792 = 1078 组）
    for n in range(1, 7):
        for shape in all_shapes(0, n):
            for k in range(1, n + 1):
                root, vals = bst_from_shape(shape, n, spread=3)
                cases.append((f"穷举 {to_level(root)}", root, vals, k))

    rng = random.Random(230)
    for i in range(200):  # 随机 BST：1~2000 个节点，值 0~10^4 互不相同，k 随机（偏向两端）
        n = rng.randint(1, 2000)
        root, vals = bst_from_shape(random_shape(n, rng), n, rng)
        k = rng.choice([1, n, rng.randint(1, n)])
        cases.append((f"随机 #{i}", root, vals, k))

    # 题目上限 1 万个节点的链：k=1 和 k=n
    for side in ("left", "right"):
        for k in (1, 10_000):
            root, vals = bst_from_shape(chain(10_000, side), 10_000)
            cases.append((f"1 万个节点的链（全往{'左' if side == 'left' else '右'}）", root, vals, k))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 先跑题目示例，再查「连调两次」：计数存在类属性或可变默认参数里时，第二次从上一次的计数接着数
        run_case(cls, *cases[0])
        root, _ = from_level([2, 1, 3])
        first, second = cls().kthSmallest(root, 2), cls().kthSmallest(root, 2)
        assert first == second == 2, (
            f"{cls.__name__}：同一棵树 [2, 1, 3] 连问两次第 2 小，得到 {first} 和 {second}"
            + ("——第二次和第一次不同：计数存在了类属性或可变默认参数里？" if first != second
               else "——返回了 None：计数存在类属性里，上一次调用后没有清零，这次一直数不到 k？" if first is None else ""))
        for name, root, vals, k in cases:
            run_case(cls, name, root, vals, k)

    # 性能：只测 Solution，1 万个节点的链。本地实测（链 k=1 / 链 k=n）：先中序存成 list 再取 1.9 / 1.5 ms，
    # 用栈中序、数到第 k 个就停 0.3 / 0.7 ms；每走一步都重新递归数一遍左子树大小 O(n^2)：
    # 1000 个节点 56 ms、2000 个 238 ms、1 万个 6.4 s。预算给 100 ms
    timings = []
    for side in ("left", "right"):
        root, vals = bst_from_shape(chain(10_000, side), 10_000)
        timings.append(run_case(Solution, f"性能：1 万个节点的链（全往{'左' if side == 'left' else '右'}）", root, vals, 1,
                                seconds=0.1, hint="可能是 O(n^2)，例如每走一步都重新数一遍子树大小"))

    # 能不能提前结束（不计入失败）：在 1 万个节点的平衡 BST 上找第 1 小，数一数读了多少次 .left / .right。
    # 数到第 k 个就停的写法只走从根到最左叶子的一条路（约 log n 次）；先把整棵树中序存下来再取的写法要读约 2n 次
    class CountingNode:
        reads = 0
        __slots__ = ("val", "_left", "_right")

        def __init__(self, val):
            self.val, self._left, self._right = val, None, None

        @property
        def left(self):
            CountingNode.reads += 1
            return self._left

        @property
        def right(self):
            CountingNode.reads += 1
            return self._right

    def balanced(lo, hi):
        if lo > hi:
            return None
        mid = (lo + hi) // 2
        node = CountingNode(mid)
        node._left, node._right = balanced(lo, mid - 1), balanced(mid + 1, hi)
        return node

    big = balanced(0, 9_999)
    CountingNode.reads = 0
    assert Solution().kthSmallest(big, 1) == 0
    reads = CountingNode.reads

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1 万个节点的链 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms; "
          f"平衡树找第 1 小读了 {reads} 次子节点指针（共 1 万个节点）)")
    if reads > 1000:
        print("提示：找第 1 小也把整棵树走了一遍。进阶可以数到第 k 个就停（用栈中序遍历），只走需要的那部分")
