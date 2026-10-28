"""
Pattern: 前缀和 + 哈希（560 的树上版本）+ 回溯

Core:
- SolutionBruteForce：以每个节点为起点，一路往下数和为 targetSum 的路径。O(n^2)。
- Solution：根到当前节点是一个「数组」，向下的路径就是它的一段连续子数组。cur 是根到当前节点的前缀和，
  某个祖先处的前缀和等于 cur - targetSum，就有一条以当前节点结尾的路径。字典 seen 记「前缀和 → 次数」，初始 {0: 1}
  对应从根开始的路径；到达节点时先查、再把 cur 加进去；左右子树都走完（后序位置）再把 cur 的次数减回去，
  这样进入兄弟子树时字典里只剩根到父节点这条路径上的前缀和。

Time: 暴力 O(n^2)；前缀和 O(n)
Space: O(n)（字典）+ O(h) 递归栈
实测 1000 个 0 的链（目标 0，共 500500 条路径）：前缀和 0.2 ms，暴力 94 ms。

Mistake:
- seen[cur] = seen[cur] + 1：右边是在读，cur 第一次出现时键不存在，第一个节点就 KeyError；改成 seen.get(cur, 0) + 1。
- 递归时没有把 dfs(node.left) / dfs(node.right) 的返回值加进结果，只数了在根结尾的路径，示例 1 期望 3 得 0（用户随后自己改了）。
- 暴力版写法：内部函数名拼错（path_sum_interal），参数 root 和外层同名，方法体多缩进一层；
  改成 count_from(node, rest)。前缀和版命名：cnt → seen、prev → parent_sum、res → paths。

易错点:
- 先查 cur - targetSum、再加 cur：反过来在 targetSum = 0 时，每个节点都会和自己配成一条空路径。
- 减回去要放在两个递归调用之后；字典初始必须有 {0: 1}，否则从根开始的路径全漏。
"""


from __future__ import annotations

# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right


class SolutionBruteForce:
    def pathSum(self, root: TreeNode | None, targetSum: int) -> int:
        def count_from(node: TreeNode | None, rest: int) -> int:
            """从 node 出发一路往下，和为 rest 的路径条数。"""
            if not node:
                return 0
            rest -= node.val
            return (rest == 0) + count_from(node.left, rest) + count_from(node.right, rest)

        if not root:
            return 0
        return count_from(root, targetSum) + self.pathSum(root.left, targetSum) + self.pathSum(root.right, targetSum)


class Solution:
    def pathSum(self, root: TreeNode | None, targetSum: int) -> int:
        seen = {0: 1}

        def dfs(node: TreeNode | None, parent_sum: int) -> int:
            if not node:
                return 0
            cur = parent_sum + node.val
            paths = seen.get(cur - targetSum, 0)
            seen[cur] = seen.get(cur, 0) + 1
            paths += dfs(node.left, cur)
            paths += dfs(node.right, cur)
            seen[cur] -= 1
            return paths

        return dfs(root, 0)


if __name__ == "__main__":
    import gc
    import itertools
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

    # 节点数上限 1000，链状树深 1000；递归写法在本地默认上限 1000 下会 RecursionError，放宽到 2 万
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

    def all_nodes(root):
        out, stack = [], [root]
        while stack:
            node = stack.pop()
            if node is not None:
                out.append(node)
                stack += [node.left, node.right]
        return out

    def count_down(start, target, leaf_only=False):
        """从 start 出发、一路往下的路径里，和为 target 的条数（显式栈）。"""
        count, stack = 0, [(start, start.val)]
        while stack:
            node, s = stack.pop()
            is_leaf = node.left is None and node.right is None
            if s == target and (is_leaf or not leaf_only):
                count += 1
            for child in (node.left, node.right):
                if child is not None:
                    stack.append((child, s + child.val))
        return count

    def count_down_stop(start, target):
        """错误写法「每条往下的支路上找到第一条就不再往下」的结果，只用来诊断。"""
        count, stack = 0, [(start, start.val)]
        while stack:
            node, s = stack.pop()
            if s == target:
                count += 1
                continue
            for child in (node.left, node.right):
                if child is not None:
                    stack.append((child, s + child.val))
        return count

    def reference(root, target):
        """按定义暴力数：以每个节点为起点往下走，和为 target 就算一条。O(n^2)，和前缀和是两套逻辑。"""
        return sum(count_down(node, target) for node in all_nodes(root))

    def call_with_limit(cls, root, target, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().pathSum(root, target)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_case(cls, name, root, target, seconds=2.0):
        nodes = all_nodes(root)
        n = len(nodes)
        before = to_level(root)
        expected = reference(root, target)
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}，targetSum={target}"
        try:
            got, elapsed = call_with_limit(cls, root, target, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert type(got) is int, f"{tag}，应返回 int，得到 {got!r}"
        if got != expected:
            guesses = []
            if root is not None and got == sum(count_down_stop(x, target) for x in nodes):
                guesses.append("找到一条之后就不再往下走了：后面还可能有 0 或正负抵消，凑出更长的路径")
            elif root is not None and got == count_down(root, target):
                guesses.append("只数了从根出发的路径：路径可以从任意节点开始")
            if root is not None and got == sum(count_down(x, target, leaf_only=True) for x in nodes):
                guesses.append("只数了在叶子结束的路径：路径可以在任意节点结束")
            if target == 0 and got == expected + n:
                guesses.append("每个节点多算了一条：把长度为 0 的空路径也算进去了（前缀和要先查、再把当前前缀和加进计数）")
            if not guesses and got < expected:
                guesses.append("少算了：前缀和的计数一开始要有 {0: 1}（对应从根开始的路径）？或者找到一条后就不再往下走了（后面还可能有 0 或正负抵消）？")
            if not guesses and got > expected:
                guesses.append("多算了：前缀和的计数在离开节点时没有减回去（不同分支的前缀被拼在一起）？或者在递归里又重复调用了 pathSum？")
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}（" + "；或者".join(guesses) + "）")
        assert to_level(root) == before, f"{tag}，调用后树被改了"
        return elapsed

    cases = []
    for name, level, target in [
        # 题目示例
        ("题目示例 1", [10, 5, -3, 3, 2, None, 11, 3, -2, None, 1], 8),
        ("题目示例 2", [5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1], 22),
        ("空树", [], 0),
        ("单节点等于目标", [5], 5),
        ("单节点不等于目标", [5], 3),
        # 路径从中间开始、在中间结束
        ("从中间开始到中间结束", [1, 2, None, 3, None, 4], 5),
        # 0 和正负抵消：找到一条后还要继续往下
        ("全是 0，目标 0", [0, 0, 0, 0, None, None, 0], 0),
        ("正负抵消", [1, -1, None, 1, None, -1], 0),
        # 大数：节点值 ±10^9
        ("值很大", [1000000000, 1000000000, None, 294967296, None, 1000000000], 0),
        ("值很大且抵消", [1000000000, -1000000000, None, 1000000000], 1000000000),
    ]:
        root, _ = from_level(level)
        cases.append((name, root, target))

    # 穷举：1~5 个节点的所有形状 × 每个节点取 -1/0/1 × 目标取 0 和 1（共约 2.3 万组）
    for n in range(1, 6):
        for shape in all_shapes(0, n):
            for vals in itertools.product((-1, 0, 1), repeat=n):
                root, _ = from_shape(shape, list(vals))
                for target in (0, 1):
                    cases.append((f"穷举 {to_level(root)}", root, target))

    rng = random.Random(437)
    for i in range(150):  # 随机：1~1000 个节点，值取小范围制造大量路径；也混一些大值
        n = rng.randint(1, 1000)
        small = rng.random() < 0.8
        vals = [rng.randint(-3, 3) if small else rng.randint(-10**9, 10**9) for _ in range(n)]
        root, _ = from_shape(random_shape(n, rng), vals)
        target = rng.randint(-5, 5) if small else vals[0]
        cases.append((f"随机 #{i}", root, target))

    # 题目上限 1000 个节点的链：全 0 目标 0 一共 500500 条路径
    for side in ("left", "right"):
        root, _ = from_shape(chain(1000, side), [0] * 1000)
        cases.append((f"1000 个 0 的链（全往{'左' if side == 'left' else '右'}）", root, 0))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 同一个实例连调两次：计数（例如前缀和的字典、答案）存在 self 上、没有在每次调用时新建，第二次会带着上一次的结果
        # 只在「各用一个新实例都算对」时才查，否则算法本身有错，交给下面的用例报
        a, _ = from_level([1, 2, 3])
        b, _ = from_level([5])
        if cls().pathSum(a, 3) == 2 and cls().pathSum(b, 5) == 1:
            sol = cls()
            first, second = sol.pathSum(a, 3), sol.pathSum(b, 5)
            assert (first, second) == (2, 1), (
                f"{cls.__name__}：同一个实例先算 [1, 2, 3] 目标 3（期望 2）得 {first}，再算 [5] 目标 5（期望 1）得 {second}"
                "（各用一个新实例时都对）——状态存在了 self 或类属性上、每次调用没有新建？")
        for name, root, target in cases:
            run_case(cls, name, root, target)

    # 题目最多 1000 个节点，暴力 O(n^2) 也只要几十毫秒、LeetCode 能过，所以只打印、不判失败。
    # 本地实测 1000 个 0 的链（目标 0）：前缀和 + 哈希 0.3 ms；每个节点为起点往下暴力数 65 ms
    root, _ = from_shape(chain(1000, "left"), [0] * 1000)
    gc.collect()
    gc.disable()
    try:
        elapsed = run_case(Solution, "计时：1000 个 0 的左链", root, 0)
    finally:
        gc.enable()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 1000 个节点的链 {elapsed * 1000:.1f} ms)")
    if elapsed > 0.02:
        print("提示：超过 20 ms，可能是以每个节点为起点暴力往下数（O(n^2)）。进阶：前缀和 + 哈希（560 的树上版本）是 O(n)")
