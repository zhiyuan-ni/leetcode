"""
Pattern: 二叉树递归，往下传祖先链给出的上下界

Core:
- 每个节点只检查自己是否严格在 (min_val, max_val) 之内，然后把收紧后的范围传给孩子：左孩子 (min_val, val)，右孩子 (val, max_val)。
  初始范围用 ±inf，节点值可以正好等于 -2^31 或 2^31-1。空节点直接返回 True，不用判断孩子在不在。

Time: O(n)
Space: O(h) 递归栈
实测 1 万个节点的链 1.7 ms（迭代中序 0.9 ms）。

Mistake:
- （本题一次通过，未出错）第一版在每个节点上检查的是孩子：if root.left / if root.right 两个分支、new_max / new_min 两个临时变量、
  同一个比较写两遍。改成检查节点自己后，方法体从 11 行缩到 5 行（和 226 一样，「孩子为空」交给递归出口）。
  类型标注 int 改为 float（传进来的是 ±inf）。

易错点:
- 只和父节点比不够：[5, 4, 6, null, null, 3, 7] 每对父子都对，但 3 在 5 的右子树里。
- 相等不算：[2, 2]、[2, null, 2] 都不是二叉搜索树。
- 上下界初始值用 ±2^31 会把 [-2147483648] 判错。
- 中序写法的 prev 不能存在类属性里，否则多次调用会互相影响。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isValidBST(self, root: TreeNode | None) -> bool:
        return self.is_valid(root, float('-inf'), float('inf'))

    def is_valid(self, root: TreeNode | None, min_val: float, max_val: float) -> bool:
        if not root:
            return True
        if not min_val < root.val < max_val:
            return False
        return self.is_valid(root.left, min_val, root.val) and self.is_valid(root.right, root.val, max_val)


if __name__ == "__main__":
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

    # 节点数上限 1 万，链状树深 1 万；和 104 一样把递归上限放宽到 2 万（104 实测 1 万层不会段错误）
    sys.setrecursionlimit(20_000)

    INT_MIN, INT_MAX = -2**31, 2**31 - 1

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

    def subtree_values(node):
        return [n.val for n in all_nodes(node)]

    def inorder(root):
        out, stack, cur = [], [], root
        while cur or stack:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            out.append(cur.val)
            cur = cur.right
        return out

    def reference(root, n):
        """小树直接按定义：每个节点都大于左子树所有值、小于右子树所有值（O(n²)）。
        大树用中序严格递增。两种都和「递归传上下界」不是同一套写法。"""
        if n <= 200:
            for node in all_nodes(root):
                if any(v >= node.val for v in subtree_values(node.left)):
                    return False
                if any(v <= node.val for v in subtree_values(node.right)):
                    return False
            return True
        vals = inorder(root)
        return all(a < b for a, b in zip(vals, vals[1:]))

    def parents_ok(root):
        """只看父子关系是否满足（不看祖先）：给「只比了父子」的错误做诊断。"""
        for node in all_nodes(root):
            if node.left is not None and not node.left.val < node.val:
                return False
            if node.right is not None and not node.right.val > node.val:
                return False
        return True

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().isValidBST(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_case(cls, name, root, n, seconds=1.0, hint="可能死循环，或者复杂度太高（O(n^2) 在 1 万个节点上要好几秒）"):
        before = to_level(root) if n <= 15 else None
        expected = reference(root, n)
        tag = f"{cls.__name__} {name}: 输入 {before if before is not None else f'{n} 个节点'}"
        try:
            got, elapsed = call_with_limit(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:  # 访问 None.val 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        assert got is True or got is False, f"{tag}，应返回 bool，得到 {got!r}"
        if got != expected:
            hint_text = ""
            vals = inorder(root)
            if got and not expected:
                if len(set(vals)) < len(vals) and all(a <= b for a, b in zip(vals, vals[1:])):
                    hint_text = "（树里有相等的值：二叉搜索树要求严格小于、严格大于，相等不算）"
                elif parents_ok(root):
                    hint_text = "（每对父子都满足大小关系，但某个节点越过了祖先的界限：只和父节点比不够，要和整条祖先链给出的上下界比）"
            elif expected and not got:
                if INT_MIN in vals or INT_MAX in vals:
                    hint_text = f"（树里有 {INT_MIN} 或 {INT_MAX}：上下界的初始值用了 ±2^31？节点值可以正好等于它，要用 None 或 ±inf）"
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}{hint_text}")
        return elapsed

    cases = []
    for name, vals in [
        # 题目示例
        ("题目示例 1", [2, 1, 3]),
        ("题目示例 2", [5, 1, 4, None, None, 3, 6]),
        ("单节点", [1]),
        # 只比父子会漏：3 是 5 右子树里的节点，比 5 小
        ("父子都对、越过祖先（右子树里有更小的）", [5, 4, 6, None, None, 3, 7]),
        ("父子都对、越过祖先（左子树里有更大的）", [5, 3, 8, 1, 6]),
        # 相等不算
        ("左孩子相等", [2, 2]),
        ("右孩子相等", [2, None, 2]),
        ("全部相同", [1, 1, 1]),
        # 边界值：节点可以正好是 -2^31 或 2^31-1
        ("最小值单节点", [INT_MIN]),
        ("最大值单节点", [INT_MAX]),
        ("最小值和最大值", [INT_MIN, None, INT_MAX]),
        ("最大值和最小值", [INT_MAX, INT_MIN]),
        ("两个最大值", [INT_MAX, INT_MAX]),
        ("两个最小值", [INT_MIN, None, INT_MIN]),
        ("中序递增但结构不对", [3, 1, 5, 0, 2, 4, 6]),
        ("合法的满二叉搜索树", [4, 2, 6, 1, 3, 5, 7]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举：1~5 个节点的所有形状 × 每个节点取值 0~2 的所有组合（11496 种），合法、不合法、有相等的都有
    for n in range(1, 6):
        for shape in all_shapes(0, n):
            for vals in itertools.product(range(3), repeat=n):
                root, _ = from_shape(shape, list(vals))
                cases.append((f"穷举 {to_level(root)}", root, n))

    rng = random.Random(98)
    def valid_bst(shape, vals):
        """先按形状建树，再按中序把严格递增的值依次填进去。
        （random_shape 的编号是建树顺序、不是中序下标，不能直接按编号填值）"""
        root, by_idx = from_shape(shape, [0] * len(vals))
        stack, cur, i = [], root, 0
        while cur or stack:
            while cur:
                stack.append(cur)
                cur = cur.left
            cur = stack.pop()
            cur.val = vals[i]
            i += 1
            cur = cur.right
        return root, by_idx

    for i in range(150):  # 随机合法 BST（形状随机，按中序填严格递增的值），以及改动一处后的版本
        n = rng.randint(1, 2000)
        vals = sorted(rng.sample(range(-10**6, 10**6), n))
        shape = random_shape(n, rng)
        root, by_idx = valid_bst(shape, vals)
        assert reference(root, n), "测试自身的问题：随机生成的 BST 不合法"
        cases.append((f"随机合法 #{i}", root, n))
        root, by_idx = valid_bst(shape, vals)
        victim = by_idx[rng.randrange(n)]
        kind = rng.random()
        if kind < 0.4:
            victim.val = rng.choice(vals)        # 可能和别的节点相等
        elif kind < 0.8:
            victim.val += rng.choice([-1, 1]) * rng.randint(1, 10**6)  # 可能越过祖先的界限
        else:
            victim.val = rng.choice([INT_MIN, INT_MAX])
        cases.append((f"随机改一处 #{i}", root, n))

    # 题目上限 1 万个节点的链：合法（往左的链值递减），递归写法检查递归深度
    for side in ("left", "right"):
        values = list(range(10_000))
        root, _ = from_shape(chain(10_000, side), values)
        cases.append((f"1 万个节点的链（全往{'左' if side == 'left' else '右'}）", root, 10_000))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 先跑题目示例，再查「先判一棵值大的树、再判一棵值小的树」：中序的 prev 存在类属性或可变默认参数里时，
        # 第二次会拿上一次的最后一个值来比
        run_case(cls, *cases[0])
        big, _ = from_level([100, 50, 150])
        small, _ = from_level([2, 1, 3])
        first, second = cls().isValidBST(big), cls().isValidBST(small)
        assert (first, second) == (True, True), (
            f"{cls.__name__}：先判 [100, 50, 150] 得 {first}，再判 [2, 1, 3] 得 {second}"
            + ("——第二次被上一次的结果影响：中序的 prev 存在了类属性或可变默认参数里？" if first and not second else ""))
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 性能：只测 Solution，1 万个节点的链。本地实测：递归传上下界 2.1 ms，迭代中序 0.9 ms；
    # 每个节点都重新求左子树最大值、右子树最小值 O(n^2)：1000 个节点 91 ms、2000 个 368 ms，1 万个约 9 s。预算给 100 ms
    timings = []
    for side in ("left", "right"):
        root, _ = from_shape(chain(10_000, side), list(range(10_000)))
        timings.append(run_case(Solution, f"性能：1 万个节点的链（全往{'左' if side == 'left' else '右'}）", root, 10_000,
                                seconds=0.1, hint="可能是 O(n^2)，例如在每个节点上都重新求子树的最大值 / 最小值"))

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1 万个节点的链 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms)")
