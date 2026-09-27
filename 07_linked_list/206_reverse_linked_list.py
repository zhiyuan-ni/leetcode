"""
Pattern: 链表原地反转

Core:
- Recursion: 先递归反转 head.next 之后的部分，拿到新头；原来的 head.next 此时是子链的尾巴，用 head.next.next = head 把 head 接上，再 head.next = None 断开，否则成环。出口是空链表或单节点。
- Solution: prev 是已反转部分的头，cur 是待处理部分的头。每步先存 nxt = cur.next，再让 cur.next 指向 prev，然后 prev、cur 各前进一步。cur 为 None 时 prev 就是新头。

Time: O(n)
Space: 迭代 O(1)；递归 O(n) 调用栈
实测 5000 个节点：迭代 0.25 ms，递归 0.8 ms。本地默认递归上限 1000，不放宽时递归解在 5000 个节点直接 RecursionError（LeetCode 上限更高，能过）。

Mistake:
- 迭代解一次通过。递归解四处错误，用 [1,2,3] 逐个修复：
  1. 只有出口有 return，其他层隐式返回 None，上一层执行 None.next = head 报 AttributeError。
  2. 把 head 接到新头上（new_head.next = head）：新头始终是 3，每层都覆盖 3.next，最后 1→2→3→1 成环。应接到子链的尾巴，也就是原来的 head.next。
  3. 接上后没有 head.next = None：1→2、2→1 成环。
  4. 出口只判断 head.next is None，空链表时 None.next 报错。应为 head is None or head.next is None。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class SolutionRecursion:
    def reverseList(self, head: ListNode | None) -> ListNode | None:
        if head is None or head.next is None:
            return head
        new_head = self.reverseList(head.next)
        head.next.next = head
        head.next = None
        return new_head


class Solution:
    def reverseList(self, head: ListNode | None) -> ListNode | None:
        cur = head
        prev = None
        while cur is not None:
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        return prev


if __name__ == "__main__":
    import random
    import signal
    import sys
    import time

    if "ListNode" not in globals():
        class ListNode:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, val=0, next=None):
                self.val = val
                self.next = next

    # 本地 Python 默认递归上限 1000，5000 个节点的递归写法会 RecursionError；
    # LeetCode 上限更高，同样的递归解能过。这里放宽到 1 万，和 LeetCode 行为一致
    sys.setrecursionlimit(10_000)

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
        return str(vals) if len(vals) <= 12 else f"长度 {len(vals)}，前 5 个 {vals[:5]}"

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().reverseList(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(vals):
        return vals[::-1]

    def check(cls, name, vals, seconds=1.0):
        head, nodes = build(vals)
        tag = f"{cls.__name__} {name}"
        try:
            got, elapsed = call_with_limit(cls, head, seconds)
        except Exception as e:  # 空链表访问 None.next、递归太深等，带上用例名再抛
            raise AssertionError(f"{tag}: 抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}: 超过 {seconds}s 被中断"
        order = walk(got, len(nodes))
        assert order is not None, (
            f"{tag}: 从返回的头走了 {len(nodes)} 个节点还没到 None，链表成环了（原来的头节点 next 没清空？）")
        got_vals = [n.val for n in order]
        expected = reference(vals)
        assert got_vals == expected, f"{tag}: 期望 {show(expected)}，得到 {show(got_vals)}"
        assert [n.val for n in nodes] == vals, f"{tag}: 值对了，但原节点的 val 被改了——这是交换 val，不是反转链表"
        assert all(a is b for a, b in zip(order, reversed(nodes))), (
            f"{tag}: 值对了，但返回的不是原来那些节点——新建了节点，空间变成 O(n)")
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [1, 2, 3, 4, 5]),
        ("题目示例 2", [1, 2]),
        ("题目示例 3：空链表", []),
        # 最短
        ("单节点", [7]),
        # 奇偶长度
        ("奇数长度", [1, 2, 3]),
        ("偶数长度", [1, 2, 3, 4]),
        # 值重复：只比 val 看不出节点有没有排对，靠 is 检查
        ("值全相同", [5, 5, 5, 5]),
        ("回文", [1, 2, 1]),
        # 值域边界
        ("值域边界", [-5000, 0, 5000]),
    ]

    rng = random.Random(206)
    for i in range(500):
        n = rng.randint(0, 12)
        cases.append((f"随机 #{i}", [rng.randint(-3, 3) for _ in range(n)]))

    # 节点数上限 5000：所有解法都要过，递归写法在这里检查递归深度
    cases.append(("上限 5000 个节点", list(range(5000))))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals in cases:
            check(cls, name, vals)

    # 性能：只测 Solution。本地实测 5000 个节点：迭代 0.25 ms，递归 0.8 ms；
    # 每轮走到尾巴再摘下来接到新链表的 O(n^2) 写法 250 ms。预算给 50 ms
    elapsed = check(Solution, "性能：5000 个节点", list(range(5000)), seconds=0.05)

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 5000 个节点 {elapsed * 1000:.1f} ms)")
