"""
Pattern: 二叉树原地改指针（找左子树最右节点）

Core:
- 对每个有左子树的节点 cur：从 cur.left 一路往右走到底得到 pre，pre.right = cur.right（先把原右子树接到左子树最右边），
  再 cur.right = cur.left、cur.left = None；然后 cur = cur.right 继续。顺序不能反：先接好原右子树，才能覆盖 cur.right。
  pre 不一定是左子树前序的最后一个节点，但之后处理到左子树内部时会继续调整，最终顺序正确。
- Recursion: 同样的搬动，然后只对 root.right 递归（left 已经清空）。这是尾递归，改成 while 循环就是 Solution，O(1) 额外空间。

Time: O(n)（每条边在找 pre 时最多被走一次）
Space: Solution O(1)；Recursion O(n) 递归栈
实测 2000 个节点的左链：Solution 0.2 ms、额外内存 0 KB；Recursion 0.5 ms、774 KB。

Mistake:
- 第一版（递归）三处：原右子树接到了左孩子本身（root.right.right = temp），覆盖了左孩子自己的右子树，示例 1 丢了 4；
  条件写成 root.left and root.right，只有左子树时什么都不做，[1, 2] 原样不动；返回了 root（题目要求原地修改、不返回）。
- 改成循环版一次写对。

易错点:
- 给 root 重新赋值不会改到调用方的树，要改的是节点的 .left / .right。
- 串成中序、先右后左、left 没清空、新建节点都不对。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class SolutionRecursion:
    def flatten(self, root: TreeNode | None) -> None:
        if not root:
            return
        if root.left:
            right_subtree = root.right
            root.right = root.left
            tail = root.right
            while tail.right:
                tail = tail.right
            tail.right = right_subtree
            root.left = None
        self.flatten(root.right)


class Solution:
    def flatten(self, root: TreeNode | None) -> None:
        cur = root
        while cur:
            if cur.left:
                pre = cur.left
                while pre.right:
                    pre = pre.right
                pre.right = cur.right
                cur.right = cur.left
                cur.left = None
            cur = cur.right


if __name__ == "__main__":
    import gc
    import random
    import signal
    import sys
    import time
    import tracemalloc

    if "TreeNode" not in globals():
        class TreeNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, left=None, right=None):
                self.val = val
                self.left = left
                self.right = right

    # 节点数上限 2000，链状树深 2000；递归写法在本地默认上限 1000 下会 RecursionError，放宽到 2 万
    sys.setrecursionlimit(20_000)

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()

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

    def preorder_nodes(root):
        """前序（显式栈，先压右再压左）的节点对象列表，在调用之前算好。"""
        out, stack = [], [root] if root else []
        while stack:
            node = stack.pop()
            out.append(node)
            stack += [c for c in (node.right, node.left) if c is not None]
        return out

    def inorder_nodes(root):
        out, stack, cur = [], [], root
        while cur or stack:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            out.append(cur)
            cur = cur.right
        return out

    def walk_ids(start, n):
        out, cur = [], start
        while cur is not None and len(out) <= n:
            out.append(id(cur))
            cur = cur.right
        return out

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().flatten(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    returned_value = set()  # 返回了非 None 的值：题目要求不返回，LeetCode 不看返回值，只提示

    def run_case(cls, name, root, n, seconds=1.0):
        """原地修改：调用后从原来的 root 出发沿 right 走，经过的必须正好是原来的节点对象、按前序排列，
        并且每个节点的 left 都是 None。"""
        before = to_level(root)
        expected = preorder_nodes(root)
        index = {id(node): i for i, node in enumerate(expected)}
        old_inorder_nodes = inorder_nodes(root)
        old_inorder = [id(x) for x in old_inorder_nodes]
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}"
        try:
            got, elapsed = call_with_limit(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:  # 访问 None.right 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环（right 指针成环了？）"
        if got is not None:
            returned_value.add(cls.__name__)
        if root is None:
            return elapsed
        walked, cur = [], root
        while cur is not None and len(walked) <= n:
            walked.append(cur)
            cur = cur.right
        assert len(walked) <= n, f"{tag}，从 root 沿 right 走了 {n + 1} 步还没到 None：right 指针成环了"
        got_idx = [index.get(id(x), "新节点") for x in walked]
        want_idx = list(range(n))
        if got_idx != want_idx:
            hint = ""
            if to_level(root) == before:
                hint = ("（树一点没变：还没写？某种情况下（比如只有左孩子）什么都没做？"
                        "或者只给 root 重新赋值了——那不会改到调用方的树，要改的是节点的 .left / .right）")
            elif "新节点" in got_idx:
                hint = "（链上出现了新建的节点：题目要求原地展开，用原来的节点）"
            elif old_inorder_nodes and walk_ids(old_inorder_nodes[0], n) == old_inorder:
                hint = "（节点被串成了中序（从最左的节点开始）：要的是前序，根 → 左子树 → 右子树）"
            elif len(walked) < n:
                hint = f"（只走到 {len(walked)} 个节点：把 right 改成左子树之前，原来的右子树没有接到左子树的末尾？）"
            elif sorted(got_idx, key=str) == sorted(want_idx, key=str):
                hint = "（节点都在但顺序不对：要的是前序，先左子树后右子树）"
            vals = [x.val for x in walked]
            shown = vals if n <= 15 else f"前 10 个 {vals[:10]}"
            raise AssertionError(f"{tag}，沿 right 走得到的值 {shown}，期望 {[x.val for x in expected][:15]}"
                                 f"（按节点对象比较，第一个不对的位置 "
                                 f"{next((i for i, (a, b) in enumerate(zip(got_idx, want_idx)) if a != b), min(len(got_idx), n))}）{hint}")
        lefts = [x.val for x in walked if x.left is not None]
        assert not lefts, f"{tag}，顺序对了，但值为 {lefts[:5]} 的节点 left 还没清空（要设成 None）"
        assert [x.val for x in walked] == [x.val for x in expected], f"{tag}，节点的 val 被改了"
        return elapsed

    cases = []
    for name, vals in [
        # 题目示例
        ("题目示例 1", [1, 2, 5, 3, 4, None, 6]),
        ("题目示例 2：空树", []),
        ("题目示例 3", [0]),
        ("只有左孩子", [1, 2]),
        ("只有右孩子", [1, None, 2]),
        # 左子树的末尾不是左子树的根：右子树要接到左子树前序的最后一个节点后面
        ("左子树末尾很深", [1, 2, 6, 3, None, None, None, None, 4, 5]),
        ("值全相同", [7, 7, 7, 7, None, None, 7]),
        ("值域边界", [-100, 100, -100]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举：0~7 个节点的所有形状（626 种），值各不相同
    for n in range(8):
        for shape in all_shapes(0, n):
            root, _ = from_shape(shape, list(range(n)))
            cases.append((f"穷举 {to_level(root)}", root, n))

    # 题目上限 2000 个节点：链状
    for side in ("left", "right"):
        root, _ = from_shape(chain(2000, side), list(range(2000)))
        cases.append((f"2000 个节点的链（全往{'左' if side == 'left' else '右'}）", root, 2000))

    rng = random.Random(114)
    for i in range(300):  # 随机形状：0~2000 个节点
        n = rng.randint(0, 2000)
        root, _ = from_shape(random_shape(n, rng), [rng.randint(-100, 100) for _ in range(n)])
        cases.append((f"随机 #{i}", root, n))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 题目最多 2000 个节点，O(n^2) 也只要几十毫秒、LeetCode 能过，所以不设性能失败条件，只打印。
    # 本地实测 2000 个节点的左链：递归 0.5 ms，找前驱（进阶 O(1) 空间）0.2 ms，存前序列表再重连 0.3 ms；
    # 递归展开后再从左子树的头走到尾 O(n^2)：45 ms（4000 个节点 179 ms）
    # 计时时关掉垃圾回收：前面建了几十万个节点，深递归分配栈帧时可能触发一次全量 GC，
    # 把正确的递归写法也拖到几十毫秒（实测 74 ms），误报成 O(n^2)
    root, _ = from_shape(chain(2000, "left"), list(range(2000)))
    gc.collect()
    gc.disable()
    try:
        elapsed = run_case(Solution, "计时：2000 个节点的左链", root, 2000)
    finally:
        gc.enable()
    root, _ = from_shape(chain(2000, "left"), list(range(2000)))
    tracemalloc.start()
    Solution().flatten(root)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"2000 个节点的左链 {elapsed * 1000:.1f} ms，额外内存峰值 {peak / 1024:.1f} KB)")
    if elapsed > 0.01:
        print("提示：左链上超过 10 ms，可能是 O(n^2)（比如每次都从左子树的头走到尾）")
    if peak > 50 * 1024:
        print("提示：进阶要求 O(1) 额外空间：递归栈或前序列表都是 O(n)。可以用「找左子树的最右节点」的写法；"
              "如果已经是这么做的、只是对 root.right 递归，把递归改成 while 循环就是 O(1)")
    if returned_value:
        print(f"注意：{', '.join(sorted(returned_value))} 返回了非 None 的值，题目要求原地修改、不返回（LeetCode 不看返回值）")
