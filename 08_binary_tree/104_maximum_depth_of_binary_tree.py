"""
Pattern: 二叉树递归（后序：先算子树，再算自己）

Core:
- 空树深度 0；否则深度 = 左右子树里更深的那个 + 1（加上当前这一层）。

Time: O(n)
Space: O(h) 递归栈，h 是树高，最坏 O(n)
实测 1 万个节点的链：递归 2.0 ms，按层 BFS 1.3 ms。本地默认递归上限 1000，链状 1 万层要放宽上限（测试块放宽到 2 万）。

Mistake:
- （本题一次通过，未出错）写法上 + 1 写了两次（left = ... + 1、right = ... + 1 再取 max），改成 max(左, 右) + 1；
  变量 left / right 存的是深度，和子节点同名容易看混，改成 left_depth / right_depth。

易错点:
- 根节点本身算第 1 层：数边数会少 1。
- 取 min 得到的是到最近叶子的深度（111 题），不是最大深度。
- 「目前最深」不能存在类属性或可变默认参数里，否则多次调用会带上上一次的结果。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def maxDepth(self, root: TreeNode | None) -> int:
        if not root:
            return 0
        left_depth = self.maxDepth(root.left)
        right_depth = self.maxDepth(root.right)
        return max(left_depth, right_depth) + 1


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

    # 节点数上限 1 万，链状树深 1 万。本地默认递归上限 1000，递归写法会 RecursionError；
    # LeetCode 上限更高能过。放宽到 2 万（实测 1 万层不会段错误；234 放宽到 20 万跑 10 万层段错误过）
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
        """shape 是 (根的中序下标, 左子树 shape, 右子树 shape)。返回 (root, nodes, 深度)。
        深度在建树时自顶向下记录「到过的最深一层」，和自底向上取 max 的解法是两套逻辑。用显式栈建树，1 万层也不递归。"""
        nodes, deepest = [], 0
        holder = TreeNode()
        stack = [(shape, holder, "left", 1)]
        while stack:
            s, parent, side, depth = stack.pop()
            if s is None:
                continue
            idx, left, right = s
            node = TreeNode(vals[idx])
            setattr(parent, side, node)
            nodes.append(node)
            deepest = max(deepest, depth)
            stack.append((left, node, "left", depth + 1))
            stack.append((right, node, "right", depth + 1))
        return holder.left, nodes, deepest

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

    def min_leaf_depth(root):
        """根到最近叶子的层数，只用来诊断「用了 min」的错误。"""
        if root is None:
            return 0
        level, queue = 1, [root]
        while queue:
            if any(n.left is None and n.right is None for n in queue):
                return level
            queue = [c for n in queue for c in (n.left, n.right) if c is not None]
            level += 1

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().maxDepth(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    modified = set()  # 调用后树被改了：LeetCode 不检查，只提示

    def check(cls, name, root, nodes, expected, seconds=1.0):
        before = [(n.val, n.left, n.right) for n in nodes]
        shape = to_level(root) if len(nodes) <= 15 else None
        tag = f"{cls.__name__} {name}: 输入 {shape if shape is not None else f'{len(nodes)} 个节点'}"
        try:
            got, elapsed = call_with_limit(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:  # 访问 None.left 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}"
        detail = ""
        if got == len(nodes) != expected:
            detail = "（这是节点总数，不是深度）"
        else:
            guesses = []
            if got == min_leaf_depth(root) != expected:
                guesses.append("这是到最近叶子的深度：取了 min？")
            if got == expected - 1:
                guesses.append("少了 1：数的是边数？根节点本身算第 1 层")
            if guesses:
                detail = "（" + "；或者".join(guesses) + "）"
        assert got == expected, f"{tag}，期望 {expected}，得到 {got}{detail}"
        if before != [(n.val, n.left, n.right) for n in nodes]:
            modified.add(cls.__name__)
        return elapsed

    cases = []
    for name, vals, expected in [
        # 题目示例：期望值离线算好写死
        ("题目示例 1", [3, 9, 20, None, None, 15, 7], 3),
        ("题目示例 2", [1, None, 2], 2),
        ("空树", [], 0),
        ("单节点", [1], 1),
        # 最深的叶子在左边 / 右边 / 不在最后一层的最左
        ("最深在左", [1, 2, 3, 4], 3),
        ("最深在右", [1, 2, 3, None, None, None, 4], 3),
        ("左右深度不同", [1, 2, None, 3, None, 4], 4),
        ("满二叉树", [1, 2, 3, 4, 5, 6, 7], 3),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, nodes, expected))

    # 穷举：0~7 个节点的所有形状（626 种），值 i % 3
    for n in range(8):
        for shape in all_shapes(0, n):
            cases.append((f"穷举 {n} 个节点", *from_shape(shape, [i % 3 for i in range(n)])))

    # 题目上限 1 万个节点：链状最深，递归写法在这里检查递归深度
    for side in ("left", "right"):
        cases.append((f"1 万个节点的链（全往{'左' if side == 'left' else '右'}）",
                      *from_shape(chain(10_000, side), [0] * 10_000)))

    rng = random.Random(104)
    for i in range(200):  # 随机形状：0~1000 个节点
        n = rng.randint(0, 1000)
        cases.append((f"随机 #{i}", *from_shape(random_shape(n, rng), [rng.randint(-100, 100) for _ in range(n)])))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 先跑题目示例确认基本功能，再查「先算深树、再算浅树」：用类属性或可变默认参数记「目前最深」时，
        # 第二次会带着上一次的结果。放在其他用例之前，否则会被前面用例的残留抢先报在不相干的地方
        check(cls, *cases[0])
        deep, _, _ = from_shape(chain(5, "left"), [0] * 5)
        shallow, _ = from_level([1])
        first, second = cls().maxDepth(deep), cls().maxDepth(shallow)
        assert (first, second) == (5, 1), (
            f"{cls.__name__}：先算 5 层的树得 {first}，再算 1 层的树得 {second}——「目前最深」存在了类属性或可变默认参数里？")
        for name, root, nodes, expected in cases:
            check(cls, name, root, nodes, expected)

    # 规模只有 1 万，O(n) 的写法都在毫秒级；打印 1 万个节点的耗时，不设性能失败条件
    timings = []
    for name, root, nodes, expected in cases:
        if name.startswith("1 万个节点"):
            timings.append(check(Solution, name, root, nodes, expected))

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1 万个节点的链 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms)")
    if modified:
        print(f"注意：{', '.join(sorted(modified))} 调用后树被改了，LeetCode 不检查，但最好不要改输入")
