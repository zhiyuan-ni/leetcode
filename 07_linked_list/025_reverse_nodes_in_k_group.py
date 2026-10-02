"""
Pattern: 链表分组原地反转

Core:
- List: 用 list 攒节点，满 k 个就 pop() 倒着接到 tail 后面；最后剩下不足 k 个的本来就按原顺序连着，tail.next = nodes[0] 一行接上（没有剩余时接 None）。
- Solution: 一边走一边就地反转（206 的写法），每满 k 个：第一组记下 new_head，之后把上一组的尾巴 prev_tail 接到这一组的新头 pre 上；
  这一组原来的第一个节点 group_head 变成它的尾巴，成为新的 prev_tail。走完后不足 k 个的剩余部分也被反转了，
  从 back = None 开始再反转 count % k 个节点恢复原顺序，接到 prev_tail 后面。

Time: O(n)，剩余部分多反转一次，最多 k - 1 个节点
Space: List O(k)；Solution O(1)
实测 5000 个节点（k = 1 / 2 / 70 / 5000）：List 0.7 / 0.6 / 0.4 / 0.4 ms，k = n 时额外内存 41 KB；
Solution 0.4 / 0.3 / 0.3 / 0.3 ms，额外内存 0.1 KB。

Mistake:
- List 第一版用 nodes.remove(nodes[l-1]) 取最后一个：remove 按值从头逐个比较，每次 O(k)，一组 O(k^2)。
  k = 5000 时一组比较约 1250 万次，70 ms，超过 50 ms 预算；改成 nodes.pop() 后 0.9 ms。剩余部分 remove(nodes[0]) 每次也要整体前移。
- Solution 第一版：调试 print 没删，没有剩余时 pre 为 None，pre.val 崩溃；剩余部分 pre.next = None 后才 pre = pre.next，
  拿到 None（改指针前没存下一个，206 的要点）；cur 既当哨兵又当尾巴，最后 cur.next 不是哨兵的 next；尾插法不会把倒序恢复成正序。
- Solution 第二版：再反转的起点写成 tail = dummy，5 的 next 指向了哨兵；结尾用 dummy.next，但 dummy.next 从没赋值，剩余部分整段丢失。
  这里不需要哨兵，从 None 开始反转、最后接上反转后的头即可。

易错点:
- 每组结束后不重置 pre = None 也能过：组首节点暂时指回上一组的头，但会被下一组的 prev_tail.next = pre 或结尾那一行覆盖；
  剩余部分的再反转按 count % k 计数，不会顺着这些临时连接走到前面的组。
- 剩余不足 k 个时不能反转，包括只差 1 个（剩 k - 1 个）。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class SolutionList:
    def reverseKGroup(self, head: ListNode | None, k: int) -> ListNode | None:
        cur = head
        tail = dummy = ListNode()
        nodes = []
        while cur is not None:
            nodes.append(cur)
            cur = cur.next
            if len(nodes) == k:
                while nodes:
                    tail.next = nodes.pop()
                    tail = tail.next
        tail.next = nodes[0] if nodes else None
        return dummy.next


class Solution:
    def reverseKGroup(self, head: ListNode | None, k: int) -> ListNode | None:
        cur = group_head = prev_tail = head
        pre = None
        count = 0
        new_head = None
        while cur is not None:
            rest = cur.next
            cur.next = pre
            pre = cur
            cur = rest
            count += 1
            if count % k == 0:
                if count == k:
                    new_head = pre
                else:
                    prev_tail.next = pre
                prev_tail = group_head
                group_head = cur

        back = None
        while count % k != 0:
            rest = pre.next
            pre.next = back
            back = pre
            pre = rest
            count -= 1
        prev_tail.next = back
        return new_head


if __name__ == "__main__":
    import random
    import signal
    import sys
    import time
    import tracemalloc

    if "ListNode" not in globals():
        class ListNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, next=None):
                self.val = val
                self.next = next

    # 按组递归的写法深度是 n / k，k = 1 时 5000 层；本地默认上限 1000 会 RecursionError，
    # LeetCode 上限更高能过。和 206 一样放宽到 1 万（206 实测 5000 层不会段错误）
    sys.setrecursionlimit(10_000)

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「忘了 return 得到 None」区分开

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

    def call_with_limit(cls, head, k, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().reverseKGroup(head, k)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(size, k):
        """期望的节点下标顺序：每满 k 个整组倒过来，最后不足 k 个的保持原样。"""
        order = []
        full = size - size % k
        for start in range(0, full, k):
            order += list(range(start + k - 1, start - 1, -1))
        return order + list(range(full, size))

    def check(cls, name, vals, k, seconds=1.0, hint="可能死循环（改指针的顺序不对，形成了小环？）"):
        head, nodes = build(vals)
        tag = f"{cls.__name__} {name}: 输入 {vals if len(vals) <= 12 else f'{len(vals)} 个节点'}，k={k}"
        try:
            got, elapsed = call_with_limit(cls, head, k, seconds)
        except Exception as e:  # 访问 None.next、递归太深等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        # 多给一个名额：末尾多挂了哨兵节点时能看到多出来的「新节点」，而不是误报成环
        order = walk(got, len(nodes) + 1)
        assert order is not None, f"{tag}，从返回的头走了 {len(nodes) + 1} 个节点还没到 None，链表成环了"
        # 题目要求不能改 val，只能改节点之间的连接
        assert [n.val for n in nodes] == vals, f"{tag}，节点的 val 被改了——题目要求只改连接，不能交换值"
        # 按对象比较：把返回的节点翻译成原来的下标，值重复时也能看出错在哪
        index = {id(n): i for i, n in enumerate(nodes)}
        got_idx = [index.get(id(n), "新节点") for n in order]
        expected = reference(len(nodes), k)
        if got_idx != expected:
            if len(expected) <= 20:
                detail = f"期望节点下标顺序 {expected}，得到 {got_idx}"
            else:
                i = next((i for i, (x, y) in enumerate(zip(got_idx, expected)) if x != y), min(len(got_idx), len(expected)))
                detail = (f"共 {len(expected)} 个节点，得到 {len(got_idx)} 个；第一处不同在位置 {i}："
                          f"期望 {expected[i:i + 6]}，得到 {got_idx[i:i + 6]}")
            raise AssertionError(f"{tag}，{detail}")
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [1, 2, 3, 4, 5], 2),
        ("题目示例 2", [1, 2, 3, 4, 5], 3),
        # k = 1：什么都不变
        ("k=1", [1, 2, 3], 1),
        # k = n：整条反转
        ("k=n", [1, 2, 3, 4], 4),
        ("单节点", [1], 1),
        # 正好整除：没有剩余
        ("整除，两组", [1, 2, 3, 4, 5, 6], 3),
        # 剩余 k-1 个：差一个就够一组，也不能反转
        ("剩余 k-1 个", [1, 2, 3, 4, 5], 3),
        ("剩余 k-1 个，长", [1, 2, 3, 4, 5, 6, 7, 8, 9], 5),
        # 只有剩余没有整组的情况不存在（题目保证 k <= n），但 n = k + 1 时只剩 1 个
        ("剩余 1 个", [1, 2, 3, 4, 5], 4),
        # 值重复：只比 val 看不出节点有没有反转
        ("值全相同", [7] * 7, 3),
        # 值域边界
        ("值域边界", [0, 1000, 0, 1000], 2),
    ]

    # 穷举：长度 1~40 × 每一个合法的 k（1 <= k <= n），共 820 组；值 i % 3 带重复
    for size in range(1, 41):
        for k in range(1, size + 1):
            cases.append((f"穷举 n={size} k={k}", [i % 3 for i in range(size)], k))

    rng = random.Random(25)
    for i in range(100):  # 随机：长度 1~200，值域 0~1000
        size = rng.randint(1, 200)
        cases.append((f"随机 #{i}", [rng.randint(0, 1000) for _ in range(size)], rng.randint(1, size)))

    # 节点数上限 5000：所有解法都要过，递归写法在 k=1 时检查递归深度
    for k in (1, 2, 4999, 5000):
        cases.append((f"上限 5000 个节点 k={k}", [i % 1001 for i in range(5000)], k))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals, k in cases:
            check(cls, name, vals, k)

    # 性能：只测 Solution，5000 个节点。本地实测（k=1 / 2 / 70 / 5000）：
    #   迭代 0.8 / 0.5 / 0.3 / 0.5 ms，按组递归 1.4 / 0.8 / 0.3 / 0.5 ms，每组用栈存 k 个节点 0.9 / 0.8 / 0.5 / 0.6 ms；
    #   每组都从 dummy 重新走到组的起点 O(n^2 / k)：222 / 112 / 3.6 / 0.5 ms。预算给 50 ms，k 小时能拦住
    big = [i % 1001 for i in range(5000)]
    timings = []
    for k in (1, 2, 70, 5000):
        timings.append((k, check(Solution, f"性能：5000 个节点 k={k}", big, k, seconds=0.05,
                                 hint="可能是 O(n^2)，例如每组都从头重新走到组的起点")))

    # 进阶要求 O(1) 额外空间：只打印峰值额外内存，不作为失败条件。
    # 分别测 k=1 和 k=n：递归的调用栈是 O(n / k)，k=1 最深（实测 2.4 MB）；用栈存一组节点是 O(k)，k=n 最大
    peaks = []
    for k in (1, len(big)):
        head, _ = build(big)
        tracemalloc.start()
        Solution().reverseKGroup(head, k)
        peaks.append(tracemalloc.get_traced_memory()[1])
        tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 5000 个节点 "
          f"{' / '.join(f'k={k} {t * 1000:.1f}' for k, t in timings)} ms; 额外内存峰值 k=1 {peaks[0] / 1024:.1f} KB / k=n {peaks[1] / 1024:.1f} KB)")
