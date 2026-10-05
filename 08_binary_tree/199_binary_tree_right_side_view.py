"""
Pattern: 二叉树按层 BFS / 先右后左 DFS

Core:
- Solution（BFS）: 整层替换（102），每层孩子按先左后右收集，取每层最后一个就是从右边看到的；它可能挂在左子树下面。
- DFS: 先递归右子树、再递归左子树，每个深度第一次到达的节点就是这一层最右边的。depth == len(res) 表示第一次到达这个深度。
  res 在每次调用 rightSideView 时新建、传给 dfs（list 是原地 append，外面看得到；543 的 int 参数做不到）。

Time: O(n)
Space: BFS O(w) 最宽一层；DFS O(h) 递归栈

Mistake:
- BFS 一次通过，写法上把 res, level = [], [root] if root else [] 拆成两行（条件表达式只属于第二项，读的人要停下来想），推导式里的 n 改为 node。
- DFS 第一版把 res 存在 self 上、只在 __init__ 里创建：同一个实例先算 [1, 2, 3] 再算 [9, None, 8, 7]，第二次得到 [1, 3, 7]（期望 [9, 8, 7]）；
  另外还留了一个类属性 res = []，现在被实例属性遮住，删掉 __init__ 后所有实例会共用它。dfs 标注返回 None 却 return []。
  测试原来每次都新建实例，没测出来，已补上「同一个实例连调两次」的检查。

易错点:
- 只沿右孩子（或「有右走右、没右走左」）往下走：右边短时左边更深的节点也看得到，某层最右的节点不一定在上一层最右节点下面。
- 每层取第一个、或 DFS 先左后右记第一次到达的，得到的是左视图。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class SolutionDFS:
    def rightSideView(self, root: TreeNode | None) -> list[int]:
        res = []
        self.dfs(root, 0, res)
        return res

    def dfs(self, root: TreeNode | None, depth: int, res: list[int]) -> None:
        if not root:
            return
        if depth == len(res):
            res.append(root.val)
        self.dfs(root.right, depth + 1, res)
        self.dfs(root.left, depth + 1, res)


class Solution:
    def rightSideView(self, root: TreeNode | None) -> list[int]:
        res = []
        level = [root] if root else []
        while level:
            res.append(level[-1].val)
            level = [c for node in level for c in (node.left, node.right) if c]
        return res


if __name__ == "__main__":
    import random
    import signal
    import time

    if "TreeNode" not in globals():
        class TreeNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, left=None, right=None):
                self.val = val
                self.left = left
                self.right = right

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

    def views(root):
        """前序 DFS（先左后右、显式栈），每到一个深度就覆盖该深度的值：最后留下的是每层最右边的（右视图），
        第一次写入的是每层最左边的（左视图，只用来诊断）。和「按层 BFS 取最后一个」是两套逻辑。"""
        right, left = [], []
        stack = [(root, 0)] if root else []
        while stack:
            node, d = stack.pop()
            if d == len(right):
                right.append(node.val)
                left.append(node.val)
            else:
                right[d] = node.val
            for child in (node.right, node.left):
                if child is not None:
                    stack.append((child, d + 1))
        return right, left

    def one_path(root, fallback_left):
        """只沿着一条路往下走能看到的值：有右走右，没右时停下（或者改走左）。错误写法的结果，只用来诊断。"""
        out = []
        while root:
            out.append(root.val)
            root = root.right if root.right or not fallback_left else root.left
        return out

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().rightSideView(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_case(cls, name, root, n, seconds=1.0):
        before = to_level(root)
        expected, left_view = views(root)
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}"
        try:
            got, _ = call_with_limit(cls, root, seconds)
        except Exception as e:  # 访问 None.val 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert isinstance(got, list), f"{tag}，应返回 list，得到 {got!r}" + ("（空树要返回 []）" if root is None else "（忘了 return？）")
        if got != expected:
            hint = ""
            if got == left_view:
                hint = "（这是左视图：每层取了最左边的。BFS 要取每层最后一个；DFS 先右后左时，每个深度只记第一次到达的）"
            elif got in (one_path(root, False), one_path(root, True)):
                hint = ("（只沿着一条路往下走了：右边比左边短时，左边更深的节点从右边也看得到；"
                        "而且某一层最右的节点，不一定在上一层最右节点的下面）")
            elif len(got) == len(expected) - 1 or len(got) < len(expected):
                hint = "（层数少了：最深的几层没有记进去？）"
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}{hint}")
        assert to_level(root) == before, f"{tag}，调用后树被改了"

    cases = []
    for name, vals in [
        # 题目示例
        ("题目示例 1", [1, 2, 3, None, 5, None, 4]),
        ("题目示例 2", [1, 2, 3, 4, None, None, None, 5]),
        ("题目示例 3", [1, None, 3]),
        ("题目示例 4：空树", []),
        # 右边短、左边长：左边更深的节点也能看到
        ("左边更深", [1, 2, 3, 4]),
        ("只有左子树", [1, 2, None, 3]),
        # 最右边的节点挂在左子树里
        ("最右的在左子树", [1, 2, 3, None, 5, None, None, 6]),
        ("值域边界", [-100, 100, -100]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举：0~7 个节点的所有形状（626 种），值各不相同，才能看出取的是哪个节点
    for n in range(8):
        for shape in all_shapes(0, n):
            root, _ = from_shape(shape, list(range(n)))
            cases.append((f"穷举 {to_level(root)}", root, n))

    # 题目上限 100 个节点：链状
    for side in ("left", "right"):
        root, _ = from_shape(chain(100, side), list(range(100)))
        cases.append((f"100 个节点的链（全往{'左' if side == 'left' else '右'}）", root, 100))

    rng = random.Random(199)
    for i in range(300):  # 随机形状：0~100 个节点，值各不相同
        n = rng.randint(0, 100)
        root, _ = from_shape(random_shape(n, rng), rng.sample(range(-100, 101), n))
        cases.append((f"随机 #{i}", root, n))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        # 同一个实例先后算两棵不同的树：结果存在 self 上、调用开头没有清空时，第二次会带着第一次的结果
        # （LeetCode 是否每个用例都新建实例无法确认，稳妥的写法是每次调用都新建结果）
        sol = cls()
        a, _ = from_level([1, 2, 3])
        b, _ = from_level([9, None, 8, 7])
        first, second = sol.rightSideView(a), sol.rightSideView(b)
        assert (first, second) == ([1, 3], [9, 8, 7]), (
            f"{cls.__name__}：同一个实例先算 [1, 2, 3]（期望 [1, 3]）得 {first}，再算 [9, None, 8, 7]（期望 [9, 8, 7]）得 {second}"
            "——结果存在了 self 或类属性上、每次调用开头没有新建？")
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 题目节点数最多 100，规模太小，不做性能用例
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
