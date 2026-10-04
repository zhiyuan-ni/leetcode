"""
Pattern: 二叉树后序递归，返回值同时带两种信息

Core:
- 经过某个节点的最长路径 = 左子树深度 + 右子树深度（按边数）。直径是所有节点上这个值的最大值。
- 递归返回 (深度, 子树里的最大直径)：空节点 (0, 0)；当前节点的深度 = max(左, 右) + 1，
  最大直径 = max(左子树的, 右子树的, 左深度 + 右深度)。每个节点只访问一次，不需要共享变量。

Time: O(n)
Space: O(h) 递归栈
实测 1 万个节点的链 2.5 ms。

Mistake:
- 第一版在每个节点上都调用 getDepth(左)、getDepth(右)，每个节点的深度被它的每个祖先重算一遍：
  链上 getDepth 调用次数是节点数的 n 倍（1000 / 2000 / 4000 个节点：100 万 / 400 万 / 1600 万次，138 / 581 / 2288 ms），
  1 万个节点超时；完全二叉树上只有 25 倍，31.6 ms，平衡的树测不出来。
- 第二版把最大值当参数 max_depth 往下传：参数只能往下传，int 不可变，子节点的结果传不回来，每次调用收到的都是 0；
  而且只算了深度，没有算 左深度 + 右深度。示例 1 深度碰巧等于直径（都是 3）才没被发现。
- 第三版改成返回 (深度, 最大直径)：空节点只 return 0，拆包 TypeError；最大直径只在左右子树的值里取，没加入经过当前节点的路径，全为 0。
  两处都由用户自己改好。

易错点:
- 直径按边数算，不是节点数。
- 最长路径不一定经过根。
- 共享的最大值放在 nonlocal / self 上时，每次调用都要重置，否则会带上上一次的结果；返回元组则没有这个问题。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def diameterOfBinaryTree(self, root: TreeNode | None) -> int:
        return self.depth_and_diameter(root)[1]

    def depth_and_diameter(self, root: TreeNode | None) -> tuple[int, int]:
        if not root:
            return 0, 0
        left_depth, left_best = self.depth_and_diameter(root.left)
        right_depth, right_best = self.depth_and_diameter(root.right)
        current_depth = max(left_depth, right_depth) + 1
        best = max(left_best, right_best, left_depth + right_depth)
        return current_depth, best


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

    # 节点数上限 1 万，链状树深 1 万。递归写法在本地默认上限 1000 下会 RecursionError，LeetCode 上能过；
    # 和 104 一样放宽到 2 万（104 实测 1 万层不会段错误）
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

    def all_nodes(root):
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            if node is not None:
                out.append(node)
                stack += [node.left, node.right]
        return out

    def reference(root):
        """把树当成无向图，做两次 BFS：从任意点出发找到最远点 u，再从 u 出发的最远距离就是直径。
        和「后序遍历、在每个节点用左右深度之和更新答案」是两套逻辑。"""
        nodes = all_nodes(root)
        adj = {id(n): [] for n in nodes}
        for n in nodes:
            for c in (n.left, n.right):
                if c is not None:
                    adj[id(n)].append(c)
                    adj[id(c)].append(n)

        def farthest(start):
            dist = {id(start): 0}
            queue, i = [start], 0
            while i < len(queue):
                cur = queue[i]
                i += 1
                for nxt in adj[id(cur)]:
                    if id(nxt) not in dist:
                        dist[id(nxt)] = dist[id(cur)] + 1
                        queue.append(nxt)
            far = queue[-1]
            return far, dist[id(far)]

        u, _ = farthest(root)
        _, d = farthest(u)
        return d

    def depth(root):
        """层数，显式栈。只用来给「只算了经过根的路径」这种错误做诊断。"""
        best, stack = 0, [(root, 1)] if root else []
        while stack:
            node, d = stack.pop()
            best = max(best, d)
            stack += [(c, d + 1) for c in (node.left, node.right) if c is not None]
        return best

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().diameterOfBinaryTree(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_case(cls, name, root, n, seconds=1.0, hint="可能死循环，或者复杂度太高（O(n^2) 在 1 万个节点上要几秒）"):
        before = to_level(root) if n <= 15 else None
        expected = reference(root)
        tag = f"{cls.__name__} {name}: 输入 {before if before is not None else f'{n} 个节点'}"
        try:
            got, elapsed = call_with_limit(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:  # 访问 None.left 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}"
        if got != expected:
            guesses = []
            if got == expected + 1:
                guesses.append("多了 1：数的是路径上的节点数？直径按边数算")
            if got == depth(root.left) + depth(root.right) != expected:
                guesses.append("只算了经过根的那条路径？最长路径不一定经过根")
            hint_text = "（" + "；或者".join(guesses) + "）" if guesses else ""
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}{hint_text}")
        return elapsed

    cases = []
    for name, vals in [
        # 题目示例
        ("题目示例 1", [1, 2, 3, 4, 5]),
        ("题目示例 2", [1, 2]),
        ("单节点", [1]),
        # 最长路径不经过根：根只有左子树，左子树里左右两条都很长
        ("最长路径不经过根", [1, 2, None, 3, 4, 5, None, None, 6, 7, None, None, 8]),
        # 最长路径在一侧子树内部，且比经过根的更长
        ("一侧内部更长", [1, 2, 3, 4, 5, None, None, 6, None, None, 7, 8, None, None, 9]),
        # 经过根的路径最长
        ("经过根最长", [1, 2, 3, 4, None, None, 5, 6, None, None, 7]),
        ("满二叉树", [1, 2, 3, 4, 5, 6, 7]),
        ("值域边界", [-100, 100, -100]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举：1~7 个节点的所有形状（625 种）
    for n in range(1, 8):
        for shape in all_shapes(0, n):
            root, by_idx = from_shape(shape, [0] * n)
            cases.append((f"穷举 {to_level(root)}", root, n))

    # 题目上限 1 万个节点的链：直径 9999，递归写法检查递归深度
    for side in ("left", "right"):
        root, by_idx = from_shape(chain(10_000, side), [0] * 10_000)
        cases.append((f"1 万个节点的链（全往{'左' if side == 'left' else '右'}）", root, 10_000))

    rng = random.Random(543)
    for i in range(200):  # 随机形状：1~1000 个节点
        n = rng.randint(1, 1000)
        root, by_idx = from_shape(random_shape(n, rng), [rng.randint(-100, 100) for _ in range(n)])
        cases.append((f"随机 #{i}", root, n))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 先跑题目示例，再查「先算长的、再算短的」：答案存在类属性或可变默认参数里时，第二次会带着上一次的结果
        run_case(cls, *cases[0])
        long_root, _ = from_shape(chain(6, "left"), [0] * 6)
        short_root, _ = from_level([1])
        first, second = cls().diameterOfBinaryTree(long_root), cls().diameterOfBinaryTree(short_root)
        assert (first, second) == (5, 0), (
            f"{cls.__name__}：先算 6 个节点的链（期望 5）得 {first}，再算单节点（期望 0）得 {second}"
            + ("——第二次等于第一次：最大值存在了类属性或可变默认参数里？" if second == first and first != 0 else ""))
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 性能：只测 Solution，1 万个节点的链。本地实测：后序一遍 2.6 ms（递归）/ 3.4 ms（迭代）；
    # 每个节点都重新算一遍深度 O(n^2)：1000 个节点 70 ms、2000 个 289 ms，1 万个约 7 s。预算给 100 ms
    timings = []
    for side in ("left", "right"):
        root, _ = from_shape(chain(10_000, side), [0] * 10_000)
        timings.append(run_case(Solution, f"性能：1 万个节点的链（全往{'左' if side == 'left' else '右'}）", root, 10_000,
                                seconds=0.1, hint="可能是 O(n^2)，例如在每个节点上都重新递归算一遍深度"))

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1 万个节点的链 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms)")
