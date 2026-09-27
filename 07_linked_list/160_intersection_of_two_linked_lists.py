"""
Pattern: 链表双指针

Core:
- Length: 各走一遍求长度和尾节点。尾节点不同则无交点；否则长的那条先走长度差，再并排前进，第一个相同的节点（比对象，不是比值）就是交点。
- Solution: 两个指针分别从 A、B 出发，走到尽头就跳到另一条链的头。两人走过的总长度都是 m + n，所以会在交点相遇；没有交点时同时变成 None 而退出。不用算长度，也没有分支。

Time: O(m + n)
Space: O(1)

Mistake:
- 对齐时写 while lenA - lenB >= 0：相等时还会多走一步（lenA=3、lenB=3 应走 0 步却走了 1 步），走过链尾后 None.next 崩溃。条件应为 while lenA > lenB。
- 节点比较用 ==：这题 ListNode 没有自定义 __eq__，默认就是比对象身份，所以碰巧等价；题意要的是「同一个节点」，应该用 is / is not。

易错点:
- 不能按 val 判断：A = [1,2,9]、B = [2,9] 的交点是尾部的 9，按值比较会提前命中 2。
- 求长度时从 1 开始并用 node.next 做条件，隐含假设链表非空；从 0 开始、条件写 while node is not None 更稳。
- 双指针换头在无交点时也会终止：两人各走完 m + n 步后同时为 None。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None


class SolutionLength:
    def getIntersectionNode(self, headA: ListNode, headB: ListNode) -> ListNode | None:
        if headA is headB:
            return headA
        rootA = headA
        rootB = headB
        lenA = 1
        while rootA.next is not None:
            rootA = rootA.next
            lenA += 1
        lenB = 1
        while rootB.next is not None:
            rootB = rootB.next
            lenB += 1

        if rootA is not rootB:
            return None

        if lenA >= lenB:
            long = headA
            short = headB
            diff = lenA - lenB
        else:
            long = headB
            short = headA
            diff = lenB - lenA

        while diff > 0:
            long = long.next
            diff -= 1

        while long is not None:
            if long is short:
                return short
            long = long.next
            short = short.next
        return None


class Solution:
    def getIntersectionNode(self, headA: ListNode, headB: ListNode) -> ListNode | None:
        a, b = headA, headB
        while a is not b:
            a = a.next if a is not None else headB
            b = b.next if b is not None else headA
        return a


if __name__ == "__main__":
    import signal
    import time

    if "ListNode" not in globals():
        class ListNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, x):
                self.val = x
                self.next = None

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 和「没有交点时返回 None」区分开

    def build(vals, tail=None):
        """按 vals 建链表，末尾接上 tail（可以是另一条链的某个节点）。"""
        head = None
        for v in reversed(vals):
            node = ListNode(v)
            node.next = head
            head = node
        if tail is not None:
            if head is None:
                return tail
            cur = head
            while cur.next:
                cur = cur.next
            cur.next = tail
        return head

    def snapshot(*heads):
        # 记录每个节点的 next，用来检查解法没有改动链表结构
        seen = {}
        for h in heads:
            cur = h
            while cur is not None and id(cur) not in seen:
                seen[id(cur)] = cur.next
                cur = cur.next
        return seen

    def call_with_limit(cls, a, b, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().getIntersectionNode(a, b)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def make_case(a_vals, b_vals, shared_vals):
        """返回 (headA, headB, 交点节点或 None)。shared_vals 为空表示不相交。"""
        tail = build(shared_vals) if shared_vals else None
        a = build(a_vals, tail)
        b = build(b_vals, tail)
        return a, b, tail

    cases = [
        # 题目示例：相交于 8
        ("题目示例 A", [4, 1], [5, 6, 1], [8, 4, 5]),
        ("题目示例 B", [1, 9, 1], [3], [2, 4]),
        # 不相交
        ("无交点", [2, 6, 4], [1, 5], []),
        ("两条都只有一个节点且不相交", [1], [2], []),
        # 交点就是某条链的头（另一条链的公共部分从头开始）
        ("A 整条都是公共部分", [], [3], [1, 2]),
        ("B 整条都是公共部分", [3], [], [1, 2]),
        ("两条完全相同", [], [], [7, 8]),
        # 公共部分只有一个节点
        ("公共尾只有一个节点", [1, 2, 3], [9], [5]),
        # 长度差很大
        ("A 远长于 B", list(range(20)), [99], [1, 2, 3]),
        ("B 远长于 A", [99], list(range(20)), [1, 2, 3]),
        # 值重复：不能靠比较 val 判断（会提前命中）
        ("值重复但交点在后面", [1, 2], [2], [9]),
        ("所有值都相同且不相交", [7, 7, 7], [7, 7], []),
        ("所有值都相同且相交", [7, 7], [7], [7, 7]),
    ]

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, a_vals, b_vals, shared in cases:
            a, b, expected = make_case(a_vals, b_vals, shared)
            before = snapshot(a, b)
            got, _ = call_with_limit(cls, a, b, 1.0)
            assert got is not TIMED_OUT, f"{cls.__name__} {name}: 超过 1s，可能死循环"
            if expected is None:
                assert got is None, f"{cls.__name__} {name}: 期望 None，得到值为 {getattr(got, 'val', got)} 的节点"
            else:
                assert got is expected, (
                    f"{cls.__name__} {name}: 期望交点节点（val={expected.val}，要求是同一个对象），"
                    f"得到 {getattr(got, 'val', got)}")
            after = snapshot(a, b)
            assert before == after, f"{cls.__name__} {name}: 解法修改了链表的 next 指针"

    # 空链表：题目保证 headA、headB 非空，但顺手测一下不崩
    for cls in classes:
        got, _ = call_with_limit(cls, None, None, 1.0)
        assert got is None or got is TIMED_OUT, f"{cls.__name__}: 两个 None 输入应返回 None"

    # 题目 m, n <= 3 * 10^4。只对最终解 Solution 计时，超过 1s 直接中断。
    # 本地实测：双指针换头 1ms，先算长度再对齐 3ms，用 set 记节点 6ms（空间 O(m)）；
    # 两层循环逐个比对（O(mn)）3s 以上
    n = 30_000
    tail = build(list(range(1, n + 1)))
    big_a = build(list(range(-n, 0)), tail)
    big_b = build(list(range(-2 * n, -n)), tail)
    got, elapsed = call_with_limit(Solution, big_a, big_b, 1.0)
    assert got is not TIMED_OUT, "Solution 大数据（各 3 万节点）超过 1s 被中断，可能是 O(mn)"
    assert got is tail, f"Solution 大数据（各 3 万节点）: 期望公共段的第一个节点，得到 {getattr(got, 'val', got)}"

    no_tail_a = build(list(range(n)))
    no_tail_b = build(list(range(n)))
    got2, elapsed2 = call_with_limit(Solution, no_tail_a, no_tail_b, 1.0)
    assert got2 is not TIMED_OUT, "Solution 大数据（不相交）超过 1s 被中断"
    assert got2 is None, "Solution 大数据（不相交，但值完全相同）: 期望 None"

    print(f"ok ({', '.join(c.__name__ for c in classes)}; 相交 {elapsed * 1000:.0f} ms, 不相交 {elapsed2 * 1000:.0f} ms)")
