"""
Pattern: 二叉树递归（前序：先处理自己，再处理子树）

Core:
- 空树返回 None；否则交换当前节点的左右孩子，再分别翻转两棵子树，返回 root。原地修改，节点对象不变。
- 交换用一行 root.left, root.right = root.right, root.left：右边两个值先全部读出来再赋值，不会读到被覆盖的 root.left。

Time: O(n)
Space: O(h) 递归栈

Mistake:
- （本题一次通过，未出错）写法上多了 elif root.left or root.right 的条件：两个孩子都是 None 时交换也无害，
  去掉后 937 组照样全过。交换两个指针不需要先判断它们是否为空。

易错点:
- 不一定是完全二叉树，示例碰巧都是满二叉树。「左右都有才交换」在 [1, 2] 上失败（只有一个孩子也要换）。
- 分两行写 root.left = invert(root.right)、root.right = invert(root.left)，第二行用的是已经被覆盖的 root.left，
  同一个节点会挂在两个位置。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def invertTree(self, root: TreeNode | None) -> TreeNode | None:
        if not root:
            return None
        root.left, root.right = root.right, root.left
        self.invertTree(root.left)
        self.invertTree(root.right)
        return root


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
    TIMED_OUT = object()  # 空树的正确答案就是 None，不能拿 None 当超时标记

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

    def mirror(shape):
        """在形状（元组）上做镜像，不碰任何节点：期望值和「在节点上交换左右」是两套逻辑。"""
        if shape is None:
            return None
        idx, left, right = shape
        return (idx, mirror(right), mirror(left))

    def match(got, shape, by_idx):
        """逐个节点核对：结构要等于镜像后的形状，且每个位置上是原来的那个节点对象。
        返回 (结构对不对, 节点是不是原来的)。用显式栈，不递归。"""
        same_nodes = True
        stack = [(got, shape)]
        while stack:
            node, s = stack.pop()
            if s is None or node is None:
                if (s is None) != (node is None):
                    return False, same_nodes
                continue
            idx, left, right = s
            if node.val != by_idx[idx].val:
                return False, same_nodes
            if node is not by_idx[idx]:
                same_nodes = False
            stack.append((node.left, left))
            stack.append((node.right, right))
        return True, same_nodes

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

    def from_level_shape(vals):
        """层序格式 → 形状元组，编号按层序给。只用于手写用例。"""
        if not vals or vals[0] is None:
            return None, []
        nodes = [[0, None, None]]
        values = [vals[0]]
        queue, i, k = [nodes[0]], 0, 1
        while i < len(queue) and k < len(vals):
            node = queue[i]
            i += 1
            for side in (1, 2):
                if k >= len(vals):
                    break
                if vals[k] is not None:
                    child = [len(values), None, None]
                    values.append(vals[k])
                    node[side] = child
                    queue.append(child)
                k += 1

        def freeze(n):
            return None if n is None else (n[0], freeze(n[1]), freeze(n[2]))

        return freeze(nodes[0]), values

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().invertTree(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    rebuilt = set()  # 结构对、但返回的不是原来的节点（新建了一棵树）：LeetCode 不检查，只提示

    def check(cls, name, shape, vals, seconds=1.0):
        root, by_idx = from_shape(shape, vals)
        before = to_level(root)
        expected_root, _ = from_shape(mirror(shape), vals)
        expected = to_level(expected_root)
        tag = f"{cls.__name__} {name}: 输入 {before if len(by_idx) <= 15 else f'{len(by_idx)} 个节点'}"
        try:
            got, _ = call_with_limit(cls, root, seconds)
        except Exception as e:  # 访问 None.left 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        if shape is not None:
            assert got is not None, f"{tag}，返回了 None（忘了 return root？）"
        ok, same_nodes = match(got, mirror(shape), by_idx)
        if not ok:
            got_level = to_level(got)
            seen, queue, repeated = set(), [got], False
            while queue and len(seen) <= 2 * len(by_idx) + 5:
                node = queue.pop()
                if node is None:
                    continue
                if id(node) in seen:
                    repeated = True
                    break
                seen.add(id(node))
                queue += [node.left, node.right]
            mask = lambda level: [v is None for v in level]
            m = mirror(shape)
            node_at = lambda s: None if s is None else by_idx[s[0]]
            root_level_ok = got is by_idx[shape[0]] and got.left is node_at(m[1]) and got.right is node_at(m[2])
            hint = ""
            if got_level == before:
                hint = "（和输入一模一样：一个节点都没换？）"
            elif repeated:
                hint = "（同一个节点同时挂在两个位置：先把 root.left 覆盖了，再拿覆盖后的 root.left 去翻转右边？）"
            elif root_level_ok:
                hint = "（根的左右已经换对了，下面的子树没有翻转：没有递归下去？）"
            elif mask(got_level) == mask(before):
                hint = "（形状和输入一样、只是值变了：交换的是值，不是子树？）"
            raise AssertionError(f"{tag}，期望 {expected if len(by_idx) <= 15 else '镜像'}，"
                                 f"得到 {got_level if len(by_idx) <= 15 else '不是镜像'}{hint}")
        if not same_nodes or (shape is not None and got is not by_idx[shape[0]]):
            rebuilt.add(cls.__name__)

    cases = [
        # 题目示例
        ("题目示例 1", [4, 2, 7, 1, 3, 6, 9]),
        ("题目示例 2", [2, 1, 3]),
        ("题目示例 3：空树", []),
        ("单节点", [1]),
        ("只有左孩子", [1, 2]),
        ("只有右孩子", [1, None, 2]),
        # 左右子树形状不同：只交换值、不交换结构的写法会露馅
        ("左右形状不同", [1, 2, 3, 4, None, None, 5, 6]),
        ("值全相同", [1, 1, 1, 1, None, None, 1]),
        ("值域边界", [-100, 100, -100, None, 0]),
    ]
    cases = [(name, *from_level_shape(vals)) for name, vals in cases]

    # 穷举：0~7 个节点的所有形状（626 种），值 i % 3（有重复，只比值看不出节点是否换对）
    for n in range(8):
        for shape in all_shapes(0, n):
            cases.append((f"穷举 {n} 个节点", shape, [i % 3 for i in range(n)]))

    # 题目上限 100 个节点：链状
    for side in ("left", "right"):
        cases.append((f"100 个节点的链（全往{'左' if side == 'left' else '右'}）", chain(100, side), list(range(100))))

    rng = random.Random(226)
    for i in range(300):  # 随机形状：0~100 个节点
        n = rng.randint(0, 100)
        cases.append((f"随机 #{i}", random_shape(n, rng), [rng.randint(-100, 100) for _ in range(n)]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, shape, vals in cases:
            check(cls, name, shape, vals)
        # 翻转两次应该回到原样（结构和节点都不变）
        shape, vals = from_level_shape([4, 2, 7, 1, 3, 6, 9])
        root, by_idx = from_shape(shape, vals)
        twice = cls().invertTree(cls().invertTree(root))
        assert match(twice, shape, by_idx)[0], f"{cls.__name__}：示例 1 翻转两次应回到原样，得到 {to_level(twice)}"

    # 题目节点数最多 100，规模太小，不做性能用例
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
    if rebuilt:
        print(f"注意：{', '.join(sorted(rebuilt))} 返回的是新建的树，LeetCode 不检查，但题目的意思是原地翻转（额外空间 O(n)）")
