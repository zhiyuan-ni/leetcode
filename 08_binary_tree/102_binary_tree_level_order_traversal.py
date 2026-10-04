"""
Pattern: 二叉树按层 BFS（整层替换）

Core:
- level 是当前层的节点列表。每一轮先记录这一层的值，再按从左到右收集所有孩子作为 next_level，然后整层替换。
  不用数「这一层有几个节点」，也不用从队列头弹出，相邻两层不会混在一起；空树时 level 一开始就是空的，直接返回 []。

Time: O(n)
Space: O(w)，w 是最宽一层的节点数

Mistake:
- （本题一次通过，未出错）写法上：导入了 deque 却用 list.pop(0)，每次 O(当前长度)，一层 O(宽度²)：
  完全二叉树 10 万 / 40 万个节点 138 / 2385 ms，整层替换 6.7 / 26 ms（题目最多 2000 个节点，0.3 ms 没有影响）。
  每轮都会处理完整层，根本不需要弹出。另外 if node: 多余（只有非空孩子会入列）；
  第一层的值单独放进 res、其他层在上一层收集孩子时才记录，还要 if layer: 防空层，改成「处理当前层时记录当前层」就都不需要了。

易错点:
- 空树返回 []，不是 [[]]。
- 用一个队列时，每层的节点数要在开始处理这一层之前记下来，循环里 len(队列) 会随入队变大。
- 用栈 pop() 而不是队列 popleft()，层和顺序都会乱。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def levelOrder(self, root: TreeNode | None) -> list[list[int]]:
        res = []
        level = [root] if root else []
        while level:
            res.append([node.val for node in level])
            next_level = []
            for node in level:
                if node.left:
                    next_level.append(node.left)
                if node.right:
                    next_level.append(node.right)
            level = next_level
        return res


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

    # 节点数上限 2000，链状树深 2000。用递归 DFS 按深度收集的写法，本地默认上限 1000 会 RecursionError，
    # LeetCode 上能过；和 104 一样放宽到 2 万
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

    def reference(root):
        """前序 DFS（先左后右）按深度把值追加到对应的层：同一层里先访问到的一定在左边。
        和「用队列按层 BFS」是两套逻辑。用显式栈，先压右孩子再压左孩子。"""
        levels = []
        stack = [(root, 0)] if root else []
        while stack:
            node, d = stack.pop()
            if d == len(levels):
                levels.append([])
            levels[d].append(node.val)
            for child in (node.right, node.left):
                if child is not None:
                    stack.append((child, d + 1))
        return levels

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().levelOrder(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def show(levels):
        return str(levels) if sum(map(len, levels)) <= 15 else f"共 {len(levels)} 层"

    def run_case(cls, name, root, n, seconds=1.0):
        before = to_level(root)
        expected = reference(root)
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}"
        try:
            got, _ = call_with_limit(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万）") from e
        except Exception as e:  # 访问 None.left 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert isinstance(got, list) and all(isinstance(level, list) for level in got), (
            f"{tag}，应返回 list[list[int]]，得到 {got!r}")
        if got != expected:
            hint = ""
            flat = [v for level in expected for v in level]
            got_flat = [v for level in got for v in level]
            if got == [[]] and not expected:
                hint = "（空树要返回 []，不是 [[]]）"
            elif got == [flat] and len(expected) > 1:
                hint = "（所有值都进了同一层：每层的节点数要在开始处理这一层之前记下来，循环里 len(队列) 会随着入队变大）"
            elif got[:-1] == expected and got[-1:] == [[]]:
                hint = "（最后多了一个空层：把 None 放进了队列，或者最后一层处理完又多进了一次循环？）"
            elif got == [level[::-1] for level in expected]:
                hint = "（每一层都是从右到左：先放了右孩子？）"
            elif len(got) == len(expected) and all(sorted(a) == sorted(b) for a, b in zip(got, expected)):
                hint = "（每层的值对，但层内顺序不对：同一层要从左到右）"
            elif sorted(got_flat) == sorted(flat):
                hint = "（值都在，但分到的层不对：用的是栈 pop()（后进先出），而不是队列 popleft()（先进先出）？）"
            elif got_flat == flat:
                hint = "（顺序对、但分层的位置不对）"
            raise AssertionError(f"{tag}，期望 {show(expected)}，得到 {show(got)}{hint}")
        assert to_level(root) == before, f"{tag}，调用后树被改了"

    cases = []
    for name, vals in [
        # 题目示例
        ("题目示例 1", [3, 9, 20, None, None, 15, 7]),
        ("题目示例 2", [1]),
        ("题目示例 3：空树", []),
        ("只有左孩子", [1, 2]),
        ("只有右孩子", [1, None, 2]),
        # 同一层的节点分布在不同父节点下，有的父节点缺孩子
        ("层里有空位", [1, 2, 3, 4, None, None, 5, 6, None, None, 7]),
        ("满二叉树", [1, 2, 3, 4, 5, 6, 7]),
        # 值重复：只比值看不出同层顺序，靠值不重复的用例拦
        ("值全相同", [0, 0, 0, 0, None, 0]),
        ("值域边界", [-1000, 1000, -1000, None, 1000]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举：0~7 个节点的所有形状（626 种），值各不相同，才能看出同层顺序和分层是否正确
    for n in range(8):
        for shape in all_shapes(0, n):
            root, _ = from_shape(shape, list(range(n)))
            cases.append((f"穷举 {to_level(root)}", root, n))

    # 题目上限 2000 个节点：链状最深
    for side in ("left", "right"):
        root, _ = from_shape(chain(2000, side), list(range(2000)))
        cases.append((f"2000 个节点的链（全往{'左' if side == 'left' else '右'}）", root, 2000))

    rng = random.Random(102)
    for i in range(200):  # 随机形状：0~2000 个节点，值各不相同
        n = rng.randint(0, 2000)
        vals = rng.sample(range(-1000, 1001), min(n, 2001))
        root, _ = from_shape(random_shape(n, rng), vals)
        cases.append((f"随机 #{i}", root, n))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 节点数最多 2000，规模太小，不做性能用例（list.pop(0) 在 2000 个节点上也只要几毫秒）
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
