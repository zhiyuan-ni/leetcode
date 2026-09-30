"""
Pattern: 虚拟头节点 + 快慢指针（间隔 n）

Core:
- fast、slow 都从 dummy 出发，fast 先走 n 步，然后一起走到 fast.next 为 None。这时 fast 在尾节点，slow 在倒数第 n + 1 个，
  也就是要删节点的前一个，slow.next = slow.next.next。删头节点时 slow 停在 dummy，所以不用特判。返回 dummy.next。

Time: O(L)，只遍历一遍
Space: O(1)

Mistake:
- 第一版没有虚拟头节点，slow 从 head 出发停在要删节点的前一个，但头节点没有前一个：长度 1~30 × 所有 n 共 465 组里，
  失败的 30 组全部是 n == 长度（删头）。[1] n=1 崩溃，[1,2] n=2 和 [1..5] n=5 都删成了下标 1。
  用户以为是 n = 1 的边界问题，实际 n = 1 且长度 >= 2（删尾）全部正确。
- 加了 if fast is None: return head 防 n 超过长度，题目保证 1 <= n <= 长度，465 组里执行 0 次，是死代码（真执行了返回 head 也不对）。

易错点:
- 用了虚拟头节点后，fast 从 dummy 出发先走 n 步，循环条件缩成 fast.next is not None；最后返回 dummy.next，删头时原来的 head 已被删掉。
- 把后一个节点的值复制过来再跳过它，删尾节点时没有后一个节点，而且删掉的不是那个节点本身。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeNthFromEnd(self, head: ListNode | None, n: int) -> ListNode | None:
        dummy = ListNode(0, head)
        fast = slow = dummy
        for _ in range(n):
            fast = fast.next
        while fast.next is not None:
            fast = fast.next
            slow = slow.next
        slow.next = slow.next.next
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
    TIMED_OUT = object()  # 只有一个节点时正确答案就是 None，不能拿 None 当超时标记

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

    def call_with_limit(cls, head, n, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().removeNthFromEnd(head, n)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(vals, n):
        # 直接按下标删，不走链表
        i = len(vals) - n
        return vals[:i] + vals[i + 1:]

    def check(cls, name, vals, n, seconds=1.0):
        head, nodes = build(vals)
        tag = f"{cls.__name__} {name}: 输入 {vals}，n={n}"
        try:
            got, _ = call_with_limit(cls, head, n, seconds)
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        order = walk(got, len(nodes))
        assert order is not None, f"{tag}，从返回的头走了 {len(nodes)} 个节点还没到 None，链表成环了"
        target = len(vals) - n
        expected_nodes = nodes[:target] + nodes[target + 1:]
        # 按对象比较：值重复时只比 val 看不出删的是哪一个
        if len(order) == len(expected_nodes) and all(a is b for a, b in zip(order, expected_nodes)):
            assert [x.val for x in nodes] == vals, f"{tag}，节点对了，但有节点的 val 被改了"
            return
        got_vals = [x.val for x in order]
        expected = reference(vals, n)
        missing = [i for i, x in enumerate(nodes) if not any(x is y for y in order)]
        if got_vals != expected:
            detail = f"期望 {expected}，得到 {got_vals}"
            if len(missing) == 1 and len(order) == len(nodes) - 1:
                detail += f"（应删下标 {target}，实际删了下标 {missing[0]}）"
            elif not order and target != 0:
                detail += "（返回了 None）"
            elif order and order[0] is nodes[target]:
                detail += "（删的是头节点时，返回的还是被删掉的那个旧头）"
        else:
            detail = "值对了，但节点不对——新建了节点，或者把后一个节点的 val 复制过来再跳过它，题目要删的是那个节点本身"
        raise AssertionError(f"{tag}，{detail}")

    cases = [
        # 题目示例
        ("题目示例 1", [1, 2, 3, 4, 5], 2),
        ("题目示例 2", [1], 1),
        ("题目示例 3", [1, 2], 1),
        # 删头节点：没有前驱，要特殊处理（或用虚拟头节点）
        ("两个节点删头", [1, 2], 2),
        ("删头", [1, 2, 3, 4, 5], 5),
        # 删尾节点：「把后一个节点的值复制过来」的写法在这里没有后一个节点
        ("删尾", [1, 2, 3, 4, 5], 1),
        # 删正中间
        ("删中间", [1, 2, 3, 4, 5], 3),
        # 值重复：只比 val 看不出删的是哪一个
        ("值全相同删头", [7, 7, 7], 3),
        ("值全相同删中间", [7, 7, 7], 2),
        ("值全相同删尾", [7, 7, 7], 1),
        # 值域边界
        ("值域边界", [0, 100, 0, 100], 2),
    ]

    # 穷举：长度 1~30（题目上限）× 每一个合法的 n，共 465 组；值 i % 3 带重复
    for size in range(1, 31):
        for n in range(1, size + 1):
            cases.append((f"穷举 size={size} n={n}", [i % 3 for i in range(size)], n))

    rng = random.Random(19)
    for i in range(200):  # 随机值
        size = rng.randint(1, 30)
        cases.append((f"随机 #{i}", [rng.randint(0, 100) for _ in range(size)], rng.randint(1, size)))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals, n in cases:
            check(cls, name, vals, n)

    # 链表最多 30 个节点，规模太小，不做性能用例。
    # 进阶要求「只遍历一次」测不出来：先求长度再走 L - n 步，和双指针读 next 的总次数都约 2L - n，只能看代码
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
