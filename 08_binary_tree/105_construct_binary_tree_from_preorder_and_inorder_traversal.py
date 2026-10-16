"""
Pattern: 分治建树（前序定根，中序分左右）+ 哈希表定位

Core:
- 前序的第一个是根；在中序里找到根，左边是左子树、右边是右子树。左子树节点数 left_size = 根在中序的下标 - 这一段中序的起点，
  于是前序里根后面的 left_size 个是左子树、剩下的是右子树。值互不相同，所以先建一次「值 → 中序下标」的字典，每层 O(1) 找根。
- 递归只传下标：前序这一段的起点、终点和中序这一段的起点；左子树中序起点不变，右子树中序起点是根的下标 + 1。

Time: O(n)
Space: O(n)（字典）+ O(h) 递归栈
实测 3000 个节点的左链 1.3 ms（每层 inorder.index + 切片 33 ms）。

Mistake:
- 第一版把字典里的绝对下标当成左子树节点数：只有中序起点为 0 的最上层才对，示例 1 的右子树 [20, 15, 7]（中序 [15, 20, 7]，起点 2）
  里 20 的下标是 3、左子树却只有 1 个，越界 IndexError。递归只传了前序的 (start, end)，没有中序起点就算不出 left_size。
- 右子树的前序终点写成 end - start（把长度和位置混在一起），应为 end（用户随后自己改了）。
- 状态放在 self 上（又有同名类属性），self.index 每次调用都往里加、不清空，同一个实例建两棵树后留着上一棵的键；改成 buildTree 的局部变量 + 内部函数。
- 写法上：index.get 换成 index[]（键一定存在，出错时报在正确位置）；删掉注释掉的旧代码和多余的 if not inorder。

易错点:
- 左右子树建反、切分区间差一（在中序这一段里找不到根，ValueError）。
- 用全局指针按前序取根时，必须先建左子树、再建右子树。
"""


from __future__ import annotations

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def buildTree(self, preorder: list[int], inorder: list[int]) -> TreeNode | None:
        index = {v: i for i, v in enumerate(inorder)}

        def build(pre_start: int, pre_end: int, in_start: int) -> TreeNode | None:
            if pre_start == pre_end:
                return None
            root_val = preorder[pre_start]
            root_idx = index[root_val]
            left_size = root_idx - in_start
            left = build(pre_start + 1, pre_start + 1 + left_size, in_start)
            right = build(pre_start + 1 + left_size, pre_end, root_idx + 1)
            return TreeNode(root_val, left, right)

        return build(0, len(preorder), 0)


if __name__ == "__main__":
    import gc
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

    # 节点数上限 3000，链状树深 3000；递归写法在本地默认上限 1000 下会 RecursionError，放宽到 2 万
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

    def mirror_level(root):
        """镜像后的层序（不改原树），只用来诊断「左右建反了」。"""
        out, queue, i = [], [root], 0
        while i < len(queue):
            node = queue[i]
            i += 1
            out.append(None if node is None else node.val)
            if node is not None:
                queue += [node.right, node.left]
        while out and out[-1] is None:
            out.pop()
        return out

    def call_with_limit(cls, pre, ino, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().buildTree(pre, ino)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    changed_input = set()  # 调用后传进来的 preorder / inorder 被改了：LeetCode 不检查，只提示

    def run_case(cls, name, root, n, seconds=1.0):
        """从一棵值互不相同的树算出前序和中序作为输入；值互不相同时这两个序列唯一确定一棵树，
        所以期望的就是原来那棵树的形状（按层序比较）。"""
        expected = to_level(root)
        pre = [x.val for x in preorder_nodes(root)]
        ino = [x.val for x in inorder_nodes(root)]
        pre_arg, ino_arg = list(pre), list(ino)
        tag = (f"{cls.__name__} {name}: preorder={pre if n <= 10 else f'{n} 个数'}"
               + (f", inorder={ino}" if n <= 10 else ""))
        try:
            got, elapsed = call_with_limit(cls, pre_arg, ino_arg, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归太深（测试已把上限放宽到 2 万），或者区间没有缩小") from e
        except Exception as e:  # 下标越界、找不到值等，带上用例名再抛
            hint = ""
            if isinstance(e, ValueError) and "not in list" in str(e):
                hint = "（在这一段中序里找不到根：前序 / 中序的切分区间差一，两边对不上了）"
            elif isinstance(e, (StopIteration, IndexError)):
                hint = "（前序被用完了：用全局指针按前序依次取根时，必须先建左子树、再建右子树；或者区间端点差一）"
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}{hint}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert got is not None, f"{tag}，返回了 None（忘了 return？）"
        assert isinstance(got, TreeNode), f"{tag}，应返回 TreeNode，得到 {got!r}"
        got_level = to_level(got)
        if got_level != expected:
            hint = ""
            got_pre = [x.val for x in preorder_nodes(got)]
            got_ino = [x.val for x in inorder_nodes(got)]
            if got_level == mirror_level(root):
                hint = "（左右子树建反了：前序里根后面紧跟的是左子树）"
            elif sorted(got_pre) != sorted(pre):
                hint = "（节点的值和输入不一致：有的值丢了或重复了，切分区间差一？）"
            elif got_pre != pre:
                hint = "（建出来的树前序和输入不一致：左子树的长度要用「根在中序里的下标 - 左边界」算；用全局指针按前序取根时，必须先建左子树）"
            elif got_ino != ino:
                hint = "（建出来的树中序和输入不一致：左右子树在中序里的切分位置不对）"
            shown_got = got_level if n <= 10 else f"前 10 个 {got_level[:10]}"
            shown_exp = expected if n <= 10 else f"前 10 个 {expected[:10]}"
            raise AssertionError(f"{tag}，期望（层序）{shown_exp}，得到 {shown_got}{hint}")
        if pre_arg != pre or ino_arg != ino:
            changed_input.add(cls.__name__)
        return elapsed

    cases = []
    for name, vals in [
        # 题目示例（以层序给出树，前序 / 中序由测试算出）
        ("题目示例 1", [3, 9, 20, None, None, 15, 7]),
        ("题目示例 2", [-1]),
        ("只有左孩子", [1, 2]),
        ("只有右孩子", [1, None, 2]),
        ("左右都有", [2, 1, 3]),
        ("根的左子树为空、右子树很深", [1, None, 2, None, 3, 4]),
        ("值域边界", [0, -3000, 3000]),
    ]:
        root, nodes = from_level(vals)
        cases.append((name, root, len(nodes)))

    # 穷举：1~7 个节点的所有形状（625 种），值各不相同
    for n in range(1, 8):
        for shape in all_shapes(0, n):
            root, _ = from_shape(shape, [10 * i - 30 for i in range(n)])
            cases.append((f"穷举 {to_level(root)}", root, n))

    # 题目上限 3000 个节点：链状
    for side in ("left", "right"):
        root, _ = from_shape(chain(3000, side), list(range(-1500, 1500)))
        cases.append((f"3000 个节点的链（全往{'左' if side == 'left' else '右'}）", root, 3000))

    rng = random.Random(105)
    for i in range(200):  # 随机形状：1~3000 个节点，值互不相同
        n = rng.randint(1, 3000)
        root, _ = from_shape(random_shape(n, rng), rng.sample(range(-3000, 3001), n))
        cases.append((f"随机 #{i}", root, n))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, root, n in cases:
            run_case(cls, name, root, n)

    # 题目最多 3000 个节点，O(n^2) 也只要几十毫秒、LeetCode 能过，所以只打印、不判失败。
    # 本地实测 3000 个节点的左链 / 右链：中序下标存进字典 + 传区间 1.3 / 1.0 ms，迭代（栈）0.7 / 0.7 ms；
    # 每层 inorder.index(根) + 切片 33 / 10 ms；每次 preorder.pop(0) + index 24 / 5 ms（还会改掉输入）
    root, _ = from_shape(chain(3000, "left"), list(range(-1500, 1500)))
    gc.collect()
    gc.disable()
    try:
        elapsed = run_case(Solution, "计时：3000 个节点的左链", root, 3000)
    finally:
        gc.enable()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 3000 个节点的左链 {elapsed * 1000:.1f} ms)")
    if elapsed > 0.01:
        print("提示：左链上超过 10 ms，可能是 O(n^2)：每层用 inorder.index 找根（线性）、或者每层切片复制。"
              "把中序的「值 → 下标」先存进字典、递归时传区间端点，就是 O(n)")
    if changed_input:
        print(f"注意：{', '.join(sorted(changed_input))} 调用后传进来的 preorder / inorder 被改了（比如 pop(0)），LeetCode 不检查，但调用方会受影响")
