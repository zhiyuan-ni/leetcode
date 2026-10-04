"""
Pattern: 二叉树成对递归 / 成对迭代（镜像比较）

Core:
- Recursion: is_mirror(a, b)：两边都有节点时值相等，且 a.左 与 b.右、a.右 与 b.左 互为镜像；否则只有两边都为空才算镜像。
- Solution: 栈里放待比较的节点对 (a, b)，从 (root.left, root.right) 开始。两边都空跳过；有一边空或值不同返回 False；
  否则压入 (a.left, b.right) 和 (a.right, b.left)。配对用元组固定，不靠「一次压两个、一次弹两个」。

Time: O(n)
Space: O(h) 递归栈 / O(n) 显式栈

Mistake:
- 递归第一版四处：调用 check 没写 self.（LeetCode 上 NameError；本地撞上测试块里同名的 check 函数，报「缺少参数」）；
  第一对比成 左.左 ↔ 右.左（同侧，是在判断两棵子树相同）；第二对 check(right.right, right.right) 复制后没改，自己和自己比；
  只有一边为空时落到 return True。第 4 次「对称分支复制后没换变量」（11、15、239、101）。
- 递归第二版：只有一边为空时返回 False 写成两行 and/or 混用，依赖优先级；剩下只有「都空」和「一边空」两种情况，一行 return left is None and right is None。
- 迭代版一次通过，写法上：栈里放扁平的节点、一次弹两个，pop 出来的 left/right 实际来自反的一侧（镜像关系不分先后所以碰巧对）；
  改成元组配对。三个判断改成「都空跳过 → 一边空或值不同返回 False」，不依赖 and/or 优先级。

易错点:
- 中序遍历是回文不代表对称：[1, 2, 2, 2, null, 2]。
- 按层比较值时要保留空位：[1, 2, 2, null, 3, null, 3] 每层去掉 None 后是回文，但不对称。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class SolutionRecursion:
    def isSymmetric(self, root: TreeNode | None) -> bool:
        if not root:
            return True
        return self.is_mirror(root.left, root.right)

    def is_mirror(self, left: TreeNode | None, right: TreeNode | None) -> bool:
        if left and right:
            if left.val != right.val:
                return False
            return self.is_mirror(left.left, right.right) and self.is_mirror(left.right, right.left)
        return left is None and right is None


class Solution:
    def isSymmetric(self, root: TreeNode | None) -> bool:
        if not root:
            return True
        stack = [(root.left, root.right)]
        while stack:
            a, b = stack.pop()
            if a is None and b is None:
                continue
            if a is None or b is None or a.val != b.val:
                return False
            stack.append((a.left, b.right))
            stack.append((a.right, b.left))
        return True


if __name__ == "__main__":
    import itertools
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

    def canon(root):
        """把树变成嵌套元组 (val, 左, 右)；镜像版把左右对调。用显式栈，不递归。"""
        def build(root, mirrored):
            done = {}
            stack = [(root, False)]
            while stack:
                node, ready = stack.pop()
                if node is None:
                    continue
                if ready:
                    a, b = done.get(id(node.left)), done.get(id(node.right))
                    done[id(node)] = (node.val, b, a) if mirrored else (node.val, a, b)
                else:
                    stack += [(node, True), (node.left, False), (node.right, False)]
            return done.get(id(root))
        return build(root, False), build(root, True)

    def reference(root):
        # 「整棵树等于它的镜像」：先各自整体变成元组再比较，和「两两比较镜像位置」的解法是两套逻辑
        plain, mirrored = canon(root)
        return plain == mirrored

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

    def levels_without_none(root):
        out, level = [], [root] if root else []
        while level:
            out.append([n.val for n in level])
            level = [c for n in level for c in (n.left, n.right) if c is not None]
        return out

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().isSymmetric(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def run_case(cls, name, root, n, seconds=1.0):
        before = to_level(root)
        expected = reference(root)
        tag = f"{cls.__name__} {name}: 输入 {before if n <= 15 else f'{n} 个节点'}"
        try:
            got, _ = call_with_limit(cls, root, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深") from e
        except Exception as e:  # 访问 None.left 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert got is True or got is False, f"{tag}，应返回 bool，得到 {got!r}"
        if got != expected:
            hint = ""
            if got and not expected:
                ino = inorder(root)
                lv = levels_without_none(root)
                if ino == ino[::-1]:
                    hint = "（这棵树的中序遍历是回文：如果是靠中序判断的，中序丢了结构信息，不能用来判断对称）"
                elif all(row == row[::-1] for row in lv):
                    hint = "（这棵树每层去掉空位后是回文：如果是按层比较值，空位的位置也要对称，要保留 None）"
            elif expected and not got and root.left is not None:
                hint = ("（这棵树对称，但左右两棵子树并不相同：镜像要比 左.左↔右.右、左.右↔右.左，"
                        "比成 左.左↔右.左 就成了判断两棵子树是否相同）")
            raise AssertionError(f"{tag}，期望 {expected}，得到 {got}{hint}")
        assert to_level(root) == before, f"{tag}，调用后树被改了（判断对称不应修改树）"

    def symmetric_tree(half_shape, vals, root_val):
        """左边按 half_shape 建，右边建它的镜像（新节点、同样的值），拼成一棵对称树。"""
        left, by_idx = from_shape(half_shape, vals)
        right, _ = from_shape(half_shape, vals)
        # 把右边整棵子树原地镜像：用显式栈交换左右
        stack = [right]
        while stack:
            node = stack.pop()
            if node is not None:
                node.left, node.right = node.right, node.left
                stack += [node.left, node.right]
        return TreeNode(root_val, left, right), 1 + 2 * len(by_idx)

    cases = []
    for name, vals in [
        # 题目示例
        ("题目示例 1", [1, 2, 2, 3, 4, 4, 3]),
        ("题目示例 2", [1, 2, 2, None, 3, None, 3]),
        ("单节点", [1]),
        ("两个孩子值相同", [1, 2, 2]),
        ("两个孩子值不同", [1, 2, 3]),
        ("只有左孩子", [1, 2]),
        ("只有右孩子", [1, None, 2]),
        # 中序遍历是回文、但不对称（经典反例）
        ("中序是回文但不对称", [1, 2, 2, 2, None, 2]),
        # 两棵子树完全相同（不是镜像）
        ("左右子树相同而不是镜像", [1, 2, 2, 3, 4, 3, 4]),
        # 结构对称、值不对称；值对称、结构不对称
        ("结构对称值不对称", [1, 2, 2, 3, 4, 3, 4]),
        ("值相同结构不对称", [1, 2, 2, None, 3, 3]),
        ("值域边界", [0, -100, -100, 100, None, None, 100]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举一：1~7 个节点的所有形状、值全为 0，只看结构是否对称（625 种）
    for n in range(1, 8):
        for shape in all_shapes(0, n):
            root, by_idx = from_shape(shape, [0] * n)
            cases.append((f"穷举形状 {to_level(root)}", root, n))
    # 穷举二：1~5 个节点的所有形状 × 所有 0/1 赋值（1618 种），结构和值都要对称
    for n in range(1, 6):
        for shape in all_shapes(0, n):
            for vals in itertools.product([0, 1], repeat=n):
                root, _ = from_shape(shape, list(vals))
                cases.append((f"穷举值 {to_level(root)}", root, n))

    rng = random.Random(101)
    for i in range(200):  # 随机对称树（左右各 0~499 个节点），以及改动一处后的「几乎对称」
        k = rng.randint(0, 499)
        vals = [rng.randint(-100, 100) for _ in range(k)]
        half = random_shape(k, rng)
        root, n = symmetric_tree(half, vals, rng.randint(-100, 100))
        cases.append((f"随机对称 #{i}", root, n))
        if k:
            root, n = symmetric_tree(half, vals, 0)
            # 随机改右边子树里的一个节点：改值、或者删掉它的一个孩子
            nodes, stack = [], [root.right]
            while stack:
                node = stack.pop()
                if node is not None:
                    nodes.append(node)
                    stack += [node.left, node.right]
            victim = rng.choice(nodes)
            if rng.random() < 0.5 or (victim.left is None and victim.right is None):
                victim.val += 1
            else:
                if victim.left is not None:
                    victim.left = None
                else:
                    victim.right = None
            cases.append((f"随机几乎对称 #{i}", root, n))

    # V 形：根下面左边一条往左的链、右边一条往右的链，各 499 个节点，深 500，对称
    def v_shape(k, bad=False):
        root = TreeNode(0)
        a, b = root, root
        for i in range(k):
            a.left = TreeNode(i)
            b.right = TreeNode(i + (1 if bad and i == k - 1 else 0))
            a, b = a.left, b.right
        return root
    cases.append(("V 形 999 个节点（对称）", v_shape(499), 999))
    cases.append(("V 形 999 个节点（最底下差 1）", v_shape(499, bad=True), 999))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 节点数最多 1000，规模太小，不做性能用例；进阶要求递归、迭代各写一遍
    sym = sum(reference(root) for _, root, _ in cases)
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例，其中对称 {sym} 组)")
