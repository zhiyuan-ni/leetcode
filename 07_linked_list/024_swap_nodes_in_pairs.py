"""
Pattern: 虚拟头节点 + 尾插法

Core:
- 每轮取出一对 first、second，记下下一对的开头 nxt；按 second、first 的顺序接到新链表尾巴上，tail 移到 first。
  循环后把落单的节点（或 None）接上。每个接上去的节点，它的 next 之后一定会被下一次接入或最后一行覆盖，所以不用提前断开。

Time: O(n)
Space: O(1)，只改连接，不改 val、不新建节点

Mistake:
- （本题一次通过，未出错）写法上：多了 cur.next.next = None、cur.next = None 两行「断开」，删掉任一行或两行都删，311 组全过；
  from collections import deque 导入了没用；cur.next 在循环里出现 3 次，改成 first、second 更好读；temp 改成 nxt（206 之后第 2 次用 temp）。

易错点:
- 改指针的顺序：先 b.next = a 再 a.next = b.next，a、b 互相指向，死循环。
- 奇数长度时最后一个落单，循环条件要同时判 cur 和 cur.next。
- 题目要求不能交换 val，只能改连接。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def swapPairs(self, head: ListNode | None) -> ListNode | None:
        cur = head
        dummy = ListNode()
        tail = dummy
        while cur is not None and cur.next is not None:
            first, second = cur, cur.next
            nxt = second.next
            tail.next = second
            second.next = first
            tail = first
            cur = nxt
        tail.next = cur
        return dummy.next


if __name__ == "__main__":
    import random
    import signal
    import time

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

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().swapPairs(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(size):
        """期望的节点下标顺序：[1, 0, 3, 2, ...]，奇数长度时最后一个不动。"""
        order = []
        for i in range(0, size, 2):
            order += [i + 1, i] if i + 1 < size else [i]
        return order

    def check(cls, name, vals, seconds=1.0):
        head, nodes = build(vals)
        tag = f"{cls.__name__} {name}: 输入 {vals if len(vals) <= 12 else f'{len(vals)} 个节点'}"
        try:
            got, _ = call_with_limit(cls, head, seconds)
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环（改指针的顺序不对，一对节点互相指向了？）"
        order = walk(got, len(nodes))
        assert order is not None, f"{tag}，从返回的头走了 {len(nodes)} 个节点还没到 None，链表成环了"
        # 题目要求不能改 val，只能改节点之间的连接
        assert [n.val for n in nodes] == vals, f"{tag}，节点的 val 被改了——题目要求只交换节点，不能交换值"
        # 按对象比较：把返回的节点翻译成原来的下标，值重复时也能看出错在哪
        index = {id(n): i for i, n in enumerate(nodes)}
        got_idx = [index.get(id(n), "新节点") for n in order]
        expected = reference(len(nodes))
        assert got_idx == expected, (
            f"{tag}，期望节点下标顺序 {expected[:12]}，得到 {got_idx[:12]}"
            + ("（只显示前 12 个）" if len(nodes) > 12 else ""))

    cases = [
        # 题目示例
        ("题目示例 1", [1, 2, 3, 4]),
        ("题目示例 2", []),
        ("题目示例 3", [1]),
        ("题目示例 4", [1, 2, 3]),
        # 只有一对：头节点被换掉
        ("两个节点", [1, 2]),
        # 奇数长度：最后一个落单，不动
        ("五个节点", [1, 2, 3, 4, 5]),
        ("六个节点", [1, 2, 3, 4, 5, 6]),
        # 值重复：只比 val 看不出节点有没有换
        ("值全相同", [7, 7, 7, 7]),
        ("值全相同，奇数长度", [7, 7, 7]),
        # 值域边界
        ("值域边界", [0, 100, 0, 100]),
    ]

    # 穷举：长度 0~100（题目上限）全部测一遍，值 i % 3 带重复
    for size in range(101):
        cases.append((f"长度 {size}", [i % 3 for i in range(size)]))

    rng = random.Random(24)
    for i in range(200):  # 随机值
        cases.append((f"随机 #{i}", [rng.randint(0, 100) for _ in range(rng.randint(0, 100))]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals in cases:
            check(cls, name, vals)

    # 链表最多 100 个节点，规模太小，不做性能用例；递归写法最深 50 层，本地默认上限 1000 够用
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
