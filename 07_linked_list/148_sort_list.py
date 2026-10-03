"""
Pattern: 链表归并排序（自顶向下 / 自底向上）

Core:
- TopDown: fast 从 head.next 出发，slow 停在前半段最后一个；先存 mid = slow.next 再断开，两半分别递归，再用 21 的方法合并。
- Solution（自底向上）: 先求长度 n，dummy 挂在 head 前面。段长 step 从 1 开始每轮翻倍，直到 step >= n。每轮 prev 从 dummy 出发：
  从 cur 切下 left、right 两段（split 走 step - 1 步、断开、返回剩余部分的开头），合并后接到 prev 后面，prev 走到合并结果的尾巴。
  right 为空时合并直接接上 left，不用特判。

Time: O(n log n)
Space: TopDown O(log n) 递归栈；Solution O(1)
实测 5 万个节点（随机 / 已排序 / 逆序 / 全相同）：TopDown 80 / 54 / 52 / 51 ms，额外内存 8 KB；
Solution 113 / 79 / 75 / 74 ms，额外内存 0.4 KB。存进 list 用内置 sort 再重连 8 / 4 / 6 / 4 ms，但额外内存 1.2 MB。

Mistake:
- TopDown 第一版：slow 停在后半段开头，却断开 slow.next 并递归 slow，slow 同时在两半里，n=2 时规模不缩小，无限递归；
  合并 while not left or not right 条件写反；small = small.next 以为能移动 left / right（只是让 small 指向别的节点）；dummy.next = small 应为 tail.next。
- TopDown 第二版：fast 改从 head.next 出发后，slow 变成前半段最后一个，但仍是 slow.next = None 再递归 slow，左右两半是同一个节点，成环。
- TopDown 第三版：建议把两行合成 fast = fast.next.next，新行加了、旧行没删，快指针一轮走 3 步，崩溃。
- Solution 第一版七处：Solution 缩进到了 TopDown 里面；split / merge 少 self；prev、cur 的初始化写在内层循环里且内层循环用的是数长度后为 None 的 cur；
  dummy 没挂到 head 前面；merge(right, cur) 合并错了两段；prev = prev.next 只走一步；split 走 step 步、切下 step + 1 个。
- Solution 第二版：prev 走到尾巴写成 while prev，走到 None，下一组 None.next 崩溃，应为 while prev.next。

易错点:
- 找中点时 slow 停在哪由 fast 的起点决定：fast 从 head 出发，slow 是后半段开头；从 head.next 出发，slow 是前半段末尾。改了起点，断开方式要跟着改。
- 合并写成递归（21 的递归版）深度是 n，5 万个节点 RecursionError。
"""


from __future__ import annotations

# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next


class SolutionTopDown:
    def sortList(self, head: ListNode | None) -> ListNode | None:
        if head is None or head.next is None:
            return head

        slow = head
        fast = head.next
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next

        mid = slow.next
        slow.next = None
        left = self.sortList(head)
        right = self.sortList(mid)

        tail = dummy = ListNode(-1)
        while left and right:
            if left.val < right.val:
                small, left = left, left.next
            else:
                small, right = right, right.next
            tail.next = small
            tail = tail.next

        tail.next = left or right
        return dummy.next


class Solution:
    def sortList(self, head: ListNode | None) -> ListNode | None:
        cur = head
        n = 0
        while cur:
            cur = cur.next
            n += 1
        step = 1
        dummy = ListNode(-1, head)
        while step < n:
            prev = dummy
            cur = dummy.next
            while cur:
                left = cur
                right = self.split(left, step)
                cur = self.split(right, step)
                prev.next = self.merge(left, right)
                while prev.next:
                    prev = prev.next
            step *= 2
        return dummy.next

    def split(self, head, step) -> ListNode | None:
        cur = head
        count = 0
        while cur and count < step - 1:
            cur = cur.next
            count += 1
        if cur:
            rest = cur.next
            cur.next = None
            return rest
        return None

    def merge(self, left, right) -> ListNode | None:
        tail = dummy = ListNode(-1)
        while left and right:
            if left.val < right.val:
                small, left = left, left.next
            else:
                small, right = right, right.next
            tail.next = small
            tail = tail.next
        tail.next = left or right
        return dummy.next


if __name__ == "__main__":
    import itertools
    import random
    import signal
    import time
    import tracemalloc

    if "ListNode" not in globals():
        class ListNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, next=None):
                self.val = val
                self.next = next

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 空链表的正确答案就是 None，不能拿 None 当超时标记

    def build(vals):
        """返回 (head, nodes)，nodes 按原顺序保存每个节点对象。"""
        nodes = [ListNode(v) for v in vals]
        for a, b in zip(nodes, nodes[1:]):
            a.next = b
        return (nodes[0] if nodes else None), nodes

    def walk(head, limit):
        """沿 next 走，最多 limit 个节点；还没到 None 就返回 None（说明成环）。"""
        out = []
        cur = head
        while cur is not None:
            if len(out) == limit:
                return None
            out.append(cur)
            cur = cur.next
        return out

    def show(vals):
        return str(vals) if len(vals) <= 12 else f"{len(vals)} 个节点"

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().sortList(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    # 改了 val 或新建了节点的类：题目没禁止、LeetCode 也不检查，只提示（进阶要求 O(1) 空间时只能改连接）
    rewrote_vals, new_nodes = set(), set()

    def check(cls, name, vals, seconds=1.0, hint="可能死循环（找中点或断开前半段出错，递归没有缩小？）"):
        head, nodes = build(vals)
        tag = f"{cls.__name__} {name}: 输入 {show(vals)}"
        try:
            got, elapsed = call_with_limit(cls, head, seconds)
        except RecursionError as e:
            raise AssertionError(
                f"{tag}，RecursionError：递归太深。小输入就出现，多半是找中点或断开前半段出错，"
                f"两个节点时递归没有缩小（无限递归）；大输入才出现，多半是合并（21）写成了递归、"
                f"或快排在有序输入上退化，深度变成 n。归并排序的递归深度应该是 log n") from e
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        # 多给一个名额：多挂了节点时能看到，而不是误报成环
        order = walk(got, len(nodes) + 1)
        assert order is not None, f"{tag}，从返回的头走了 {len(nodes) + 1} 个节点还没到 None，链表成环了"
        got_vals = [n.val for n in order]
        expected = sorted(vals)
        if got_vals != expected:
            if len(expected) <= 12:
                detail = f"期望 {expected}，得到 {got_vals}"
            elif len(got_vals) != len(expected):
                detail = f"期望 {len(expected)} 个节点，得到 {len(got_vals)} 个（丢了节点或多了节点）"
            else:
                i = next(i for i, (x, y) in enumerate(zip(got_vals, expected)) if x != y)
                detail = f"第一处不同在位置 {i}：期望 {expected[i:i + 5]}，得到 {got_vals[i:i + 5]}"
            raise AssertionError(f"{tag}，{detail}")
        originals = {id(n) for n in nodes}
        if any(id(n) not in originals for n in order):
            new_nodes.add(cls.__name__)
        elif [n.val for n in nodes] != vals:
            rewrote_vals.add(cls.__name__)
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [4, 2, 1, 3]),
        ("题目示例 2", [-1, 5, 3, 4, 0]),
        ("题目示例 3", []),
        # 最短
        ("单节点", [1]),
        ("两个，已排序", [1, 2]),
        ("两个，逆序", [2, 1]),
        ("三个", [3, 1, 2]),
        # 已排序 / 逆序 / 全相同：快排取头做基准时会退化
        ("已排序", [1, 2, 3, 4, 5, 6]),
        ("逆序", [6, 5, 4, 3, 2, 1]),
        ("全相同", [7] * 7),
        # 重复值、负数
        ("重复值交错", [2, 1, 2, 1, 2, 1]),
        ("值域边界", [100000, -100000, 0, -100000, 100000]),
    ]

    # 穷举：长度 0~7 的所有排列（5914 组），再加长度 0~6、值取 0~2 的所有序列（1093 组，有大量重复值）
    for size in range(8):
        for perm in itertools.permutations(range(size)):
            cases.append((f"排列 {list(perm)}", list(perm)))
    for size in range(7):
        for seq in itertools.product(range(3), repeat=size):
            cases.append((f"重复值 {list(seq)}", list(seq)))

    rng = random.Random(148)
    for i in range(100):  # 随机：长度 0~1000，值域 -10^5~10^5
        cases.append((f"随机 #{i}", [rng.randint(-100000, 100000) for _ in range(rng.randint(0, 1000))]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals in cases:
            check(cls, name, vals)

    # 性能：只测 Solution，5 万个节点（题目上限）。本地实测（随机 / 已排序 / 逆序 / 全相同）：
    #   自顶向下归并 95 / 63 / 54 / 53 ms，自底向上归并 87 / 63 / 64 / 70 ms，存进 list 用内置 sort 再重连 8 / 4 / 6 / 4 ms；
    #   插入排序 O(n^2)：随机、已排序都超过 3 s；取头做基准的快排：有序和全相同时退化，RecursionError；
    #   合并写成递归（21 的递归版）：深度 n，全部 RecursionError。预算给 1 s
    n = 50_000
    big = {
        "随机": [rng.randint(-100000, 100000) for _ in range(n)],
        "已排序": list(range(n)),
        "逆序": list(range(n, 0, -1)),
        "全相同": [7] * n,
    }
    timings = []
    for name, vals in big.items():
        timings.append(check(Solution, f"性能：5 万个节点，{name}", vals, seconds=1.0,
                             hint="可能是 O(n^2)，例如插入排序，或者快排在这种输入上退化"))

    # 进阶要求 O(1) 额外空间：只打印峰值额外内存，不作为失败条件
    head, _ = build(big["随机"])
    tracemalloc.start()
    Solution().sortList(head)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 5 万个节点 "
          f"{' / '.join(f'{t * 1000:.0f}' for t in timings)} ms; 额外内存峰值 {peak / 1024:.1f} KB)")
    if new_nodes:
        print(f"注意：{', '.join(sorted(new_nodes))} 返回的是新建的节点，LeetCode 不检查，但空间是 O(n)")
    if rewrote_vals:
        print(f"注意：{', '.join(sorted(rewrote_vals))} 是把排好的值写回原节点，没有改连接，LeetCode 不检查，但空间是 O(n)")
