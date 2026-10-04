"""
Pattern: 二叉树遍历（递归 / 栈模拟递归）

Core:
- Recursion: 左子树的结果 + [根] + 右子树的结果。
- Solution: 栈里放「左子树还没处理完、自己还没被记录」的节点，cur 指向接下来要钻进去的子树。
  cur 非空就压栈、往左走；cur 为空就弹出一个节点——能弹出说明它的左边已经处理完，记录它，cur 转向它的右子树。
  循环条件 cur or stack：刚出发时栈是空的，但 cur 不是。每个节点都由同一行压栈，栈一开始为空。

Time: O(n)
Space: O(h)，h 是树高，最坏 O(n)
Recursion 每层都新建 list 并复制子树结果，链状树上是 O(n^2)：放宽递归上限实测 2000 / 4000 个节点的链 2.8 / 12.0 ms，
共用一个 res 只要 0.29 / 0.63 ms。题目最多 100 个节点，没有影响。

Mistake:
- 迭代第一版只看栈顶、不弹出，分不清「第一次到这个节点」和「从左子树回来」：记录完叶子就 break，示例 1 得到 [1, 3]；
  把 break 改成弹出又会在回到 2 时再次往左走，死循环。加 came_back 标记、空树时栈为空才能过。
- 迭代第二版（换成 cur + 弹出的思路）四处：判断的是 cur.left 而不是 cur，没有左孩子的根节点卡住不动，死循环；
  先 cur = cur.left 再压栈，压进去的是左孩子（可能是 None），根节点靠 nodes = [root] 预先放入；res.add（list 没有 add）；忘了 return res。
- 迭代第三版其他都改对了，只剩 nodes = [root]：根节点在初始化和循环里各压一次，整棵树遍历两遍，示例 1 得到 [1, 3, 2, 1, 3, 2]；空树时弹出 None 崩溃。

易错点:
- 空树要返回 []，不是 None。
- 结果列表不能用可变默认参数 res=[]，否则多次调用会带上上一次的残留。
- Morris 遍历做到 O(1) 空间，但必须把线索恢复，否则树被改坏。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class SolutionRecursion:
    def inorderTraversal(self, root: TreeNode | None) -> list[int]:
        if not root:
            return []
        return self.inorderTraversal(root.left) + [root.val] + self.inorderTraversal(root.right)


class Solution:
    def inorderTraversal(self, root: TreeNode | None) -> list[int]:
        res = []
        stack = []
        cur = root
        while cur or stack:
            if cur:
                stack.append(cur)
                cur = cur.left
            else:
                cur = stack.pop()
                res.append(cur.val)
                cur = cur.right
        return res


if __name__ == "__main__":
    import random
    import signal
    import sys
    import time
    import traceback

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
        """shape 是 (根的中序下标, 左子树 shape, 右子树 shape)，vals 按中序给值。中序结果按构造就是 vals。"""
        nodes = []

        def make(s):
            if s is None:
                return None
            idx, left, right = s
            node = TreeNode(vals[idx], make(left), make(right))
            nodes.append(node)
            return node

        return make(shape), nodes

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

    def random_shape(lo, hi, rng):
        if lo == hi:
            return None
        r = rng.randrange(lo, hi)
        return (r, random_shape(lo, r, rng), random_shape(r + 1, hi, rng))

    def call_with_limit(cls, root, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().inorderTraversal(root)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    modified = set()  # 调用后树的结构或值被改了（Morris 没有恢复线索等）：LeetCode 不检查，只提示

    def check(cls, name, root, nodes, expected, seconds=1.0):
        before = [(n.val, n.left, n.right) for n in nodes]
        shape = to_level(root)
        tag = f"{cls.__name__} {name}: 输入 {shape if len(shape) <= 15 else f'{len(nodes)} 个节点'}"
        try:
            got, _ = call_with_limit(cls, root, seconds)
        except Exception as e:  # 访问 None.left 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环（回到上层节点时又往左走了一遍？或者 Morris 的线索没处理好？）"
        assert isinstance(got, list), f"{tag}，应返回 list，得到 {got!r}（空树要返回 []，不是 None）"
        leftover = len(got) > len(expected) and got[len(got) - len(expected):] == expected
        assert got == expected, f"{tag}，期望 {expected}，得到 {got}" + (
            "（前面多出来了一段：可能是上一次调用的残留——结果列表用了可变默认参数 res=[] 或类属性；"
            "也可能是有节点被压栈两次、整段又遍历了一遍）" if leftover else "")
        if before != [(n.val, n.left, n.right) for n in nodes]:
            modified.add(cls.__name__)

    cases = []
    # 题目示例和手写用例：期望值离线算好写死
    for name, vals, expected in [
        ("题目示例 1", [1, None, 2, 3], [1, 3, 2]),
        ("题目示例 2", [1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [4, 2, 6, 5, 7, 1, 3, 9, 8]),
        ("题目示例 3：空树", [], []),
        ("题目示例 4：单节点", [1], [1]),
        ("只有左孩子", [1, 2], [2, 1]),
        ("只有右孩子", [1, None, 2], [1, 2]),
        ("三个节点", [2, 1, 3], [1, 2, 3]),
        ("满二叉搜索树：中序有序", [5, 3, 7, 2, 4, 6, 8], [2, 3, 4, 5, 6, 7, 8]),
        ("值全相同", [1, 1, 1, 1, None, None, 1], [1, 1, 1, 1, 1]),
        ("值域边界", [-100, 100, None, None, -100], [100, -100, -100]),
    ]:
        cases.append((name, *from_level(vals), expected))

    # 穷举：0~7 个节点的所有形状（1+1+2+5+14+42+132+429 = 626 种）。按中序给值 i % 3（有重复），
    # 期望值就是这个值序列本身——由构造保证，不依赖任何遍历写法
    for n in range(8):
        vals = [i % 3 for i in range(n)]
        for shape in all_shapes(0, n):
            cases.append((f"穷举 {n} 个节点", *from_shape(shape, vals), vals))

    # 链状：题目上限 100 个节点，全往左 / 全往右是最深的情况
    for n, side in [(100, "全往左"), (100, "全往右")]:
        vals = list(range(n))
        shape = None
        if side == "全往左":
            for i in range(n):
                shape = (i, shape, None)
        else:
            for i in range(n - 1, -1, -1):
                shape = (i, None, shape)
        cases.append((f"{n} 个节点{side}", *from_shape(shape, vals), vals))

    rng = random.Random(94)
    for i in range(300):  # 随机形状，0~100 个节点，值域 -100~100
        n = rng.randint(0, 100)
        vals = [rng.randint(-100, 100) for _ in range(n)]
        cases.append((f"随机 #{i}", *from_shape(random_shape(0, n, rng), vals), vals))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, root, nodes, expected in cases:
            check(cls, name, root, nodes, expected)
        # 同一棵树连调两次，两次都要对：
        #   第一次之后树被改了 → Morris 的线索没恢复，或者遍历时拆了树；
        #   树没变但第二次多出东西 → 结果列表用了可变默认参数 res=[] 或类属性
        root, nodes = from_level([2, 1, 3])
        before = [(n.val, n.left, n.right) for n in nodes]
        first = cls().inorderTraversal(root)
        tree_changed = before != [(n.val, n.left, n.right) for n in nodes]
        second = cls().inorderTraversal(root)
        assert first == second == [1, 2, 3], (
            f"{cls.__name__}：同一棵树 [2, 1, 3] 连调两次，得到 {first} 和 {second}——"
            + ("第一次调用后树被改了（Morris 的线索没恢复？），第二次遍历的已经不是原来的树"
               if tree_changed else "树没变，结果列表用了可变默认参数或类属性？"))

    # 进阶要求迭代：把递归上限压到「当前调用深度 + 50」，在 100 个节点的链上跑，会 RecursionError 的就是递归写法。只提示，不判失败
    styles = {}
    for cls in classes:
        depth = len(traceback.extract_stack())
        old_limit = sys.getrecursionlimit()
        shape = None
        for i in range(100):
            shape = (i, shape, None)
        root, _ = from_shape(shape, list(range(100)))
        sys.setrecursionlimit(depth + 50)
        try:
            cls().inorderTraversal(root)
            styles[cls.__name__] = "迭代"
        except RecursionError:
            styles[cls.__name__] = "递归"
        finally:
            sys.setrecursionlimit(old_limit)

    # 题目节点数最多 100，规模太小，不做性能用例
    print(f"ok ({', '.join(f'{c.__name__}（{styles[c.__name__]}）' for c in classes)}; {len(cases)} 组用例)")
    if "递归" in styles.values():
        print("提示：进阶要求用迭代写法，标「递归」的类是递归实现")
    if modified:
        print(f"注意：{', '.join(sorted(modified))} 调用后树被改了（Morris 的线索没恢复？），LeetCode 不检查，但最好恢复原样")
