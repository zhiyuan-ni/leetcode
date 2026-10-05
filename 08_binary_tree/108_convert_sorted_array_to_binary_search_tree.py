"""
Pattern: 分治建树（取中点为根）

Core:
- 取中间的数作为根，左半边递归建左子树、右半边递归建右子树。左右两半长度最多差 1，所以每个节点高度平衡；
  左边都比根小、右边都比根大，所以是二叉搜索树。答案不唯一，取左中点或右中点都对。

Time: O(n log n)（每层切片共复制约 n 个数，log n 层）；传下标 (lo, hi) 不复制是 O(n)
Space: O(n)（递归路径上同时存在的切片 n + n/2 + ... ≈ 2n）；传下标只要 O(log n) 递归栈
实测 1 万个数：切片 3.1 ms，传下标 2.8 ms，树高 14。

Mistake:
- （本题一次通过，未出错）写法上 mid+1 改为 mid + 1；只用一次的 n = len(nums) 并进下一行。

易错点:
- 区间端点差一：build(lo, mid) 又包含了 mid，递归不缩小；或者把 mid 也放进子树，多出重复的数。
- 切片会复制：这里只多一个 log n，但放进循环里就可能变成 O(n²)。
"""


from __future__ import annotations

# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right


class Solution:
    def sortedArrayToBST(self, nums: list[int]) -> TreeNode | None:
        if not nums:
            return None
        mid = len(nums) // 2
        return TreeNode(nums[mid], self.sortedArrayToBST(nums[:mid]), self.sortedArrayToBST(nums[mid + 1:]))


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

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return 得到 None」区分开

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

    def inspect(root, limit):
        """一次后序遍历（显式栈）：返回 (中序值列表, 第一个不平衡的节点及其左右高度, 树高)。
        节点超过 limit 个（成环或多出节点）时返回 None。"""
        order, heights, bad = [], {}, None
        stack, cur, seen = [], root, 0
        while cur or stack:  # 中序
            while cur:
                stack.append(cur)
                cur = cur.left
                seen += 1
                if seen > limit:
                    return None
            cur = stack.pop()
            order.append(cur.val)
            cur = cur.right
        post = [(root, False)] if root else []  # 后序算高度
        while post:
            node, ready = post.pop()
            if ready:
                lh, rh = heights.get(id(node.left), 0), heights.get(id(node.right), 0)
                heights[id(node)] = max(lh, rh) + 1
                if abs(lh - rh) > 1 and bad is None:
                    bad = (node.val, lh, rh)
            else:
                post.append((node, True))
                post += [(c, False) for c in (node.left, node.right) if c is not None]
        return order, bad, heights.get(id(root), 0)

    def call_with_limit(cls, nums, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().sortedArrayToBST(nums)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def show(nums):
        return str(nums) if len(nums) <= 12 else f"{len(nums)} 个数"

    def run_case(cls, name, nums, seconds=1.0):
        """答案不唯一，所以不比固定的树，只验证性质：中序遍历等于 nums（strictly increasing，所以就是 BST），
        并且每个节点左右子树高度差不超过 1。"""
        tag = f"{cls.__name__} {name}: 输入 {show(nums)}"
        arg = list(nums)
        try:
            got, elapsed = call_with_limit(cls, arg, seconds)
        except RecursionError as e:
            raise AssertionError(f"{tag}，RecursionError：递归没有缩小（区间端点差一，lo..mid 又包含了 mid？）") from e
        except Exception as e:  # 下标越界等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        assert got is None or isinstance(got, TreeNode), f"{tag}，应返回 TreeNode，得到 {got!r}"
        assert arg == nums, f"{tag}，传进来的 nums 被改了"
        assert got is not None, f"{tag}，返回了 None（忘了 return？）"
        # 上限放宽到 3 倍：多出几个节点（区间端点差一）时还能报出多了几个；超过 3 倍才当成环
        info = inspect(got, 3 * len(nums) + 10)
        assert info is not None, f"{tag}，返回的树节点数超过输入的 3 倍，可能成环了"
        order, bad, height = info
        shape = to_level(got) if len(nums) <= 12 else None
        detail = f"（得到的树 {shape}）" if shape is not None else ""
        if order != nums:
            if sorted(order) == nums:
                why = "节点都在但位置不对：中序不是升序，不是二叉搜索树（比根小的要在左子树、大的在右子树；比如按下标一层层填满就不行）"
            elif len(order) < len(nums):
                why = f"少了 {len(nums) - len(order)} 个数：某一侧的区间漏掉了（或者区间端点差一）"
            elif len(order) > len(nums):
                why = f"多了 {len(order) - len(nums)} 个数：中间那个数被放进了子树（区间端点差一）"
            else:
                why = "中序遍历不等于输入"
            raise AssertionError(f"{tag}，{why}；中序得到 {show(order)}{detail}")
        assert bad is None, (
            f"{tag}，不是高度平衡的：值为 {bad[0]} 的节点左子树高 {bad[1]}、右子树高 {bad[2]}，相差超过 1"
            f"（根没有取中间？或者是按顺序逐个插入的）{detail}")
        return elapsed, height

    cases = [
        # 题目示例
        ("题目示例 1", [-10, -3, 0, 5, 9]),
        ("题目示例 2", [1, 3]),
        ("单个数", [0]),
        ("三个数", [1, 2, 3]),
        ("四个数（中间有两个）", [1, 2, 3, 4]),
        ("值域边界", [-10000, 0, 10000]),
    ]
    # 长度 1~200 全部测一遍（各种奇偶、各种 2 的幂附近），值从负数开始、间隔不等
    for n in range(1, 201):
        cases.append((f"长度 {n}", [3 * i - 300 for i in range(n)]))
    rng = random.Random(108)
    for i in range(100):  # 随机：长度 1~10^4，严格递增
        n = rng.randint(1, 10_000)
        cases.append((f"随机 #{i}", sorted(rng.sample(range(-10_000, 10_001), n))))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, nums in cases:
            run_case(cls, name, nums)

    # 题目上限 10^4 个数。本地实测：传下标 2.8 ms；每层切片 nums[:mid] 复制数组 3.1 ms（O(n log n)，仍然很快），不设性能失败条件
    big = list(range(-5000, 5000))
    elapsed, height = run_case(Solution, "1 万个数", big)
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 1 万个数 {elapsed * 1000:.1f} ms，树高 {height}）")
