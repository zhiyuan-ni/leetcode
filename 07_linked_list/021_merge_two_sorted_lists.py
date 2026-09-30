"""
Pattern: 虚拟头节点 + 双指针归并

Core:
- 先放一个不存数据的 dummy，tail 从它开始，「第一个节点接在哪」和「之后的节点接在哪」变成同一件事，不用单独选头。
- 两边都非空时比较，把小的接到 tail 后面并前进；循环结束后把没用完的那一边整段接上（两边都空时接的是 None）。返回 dummy.next。

Time: O(m + n)
Space: O(1)，用原节点拼接，不新建

Mistake:
- （本题第一版就通过全部用例，问题在写法）第一版特判过多，方法体 36 行：开头 3 个分支处理空链表，再用 2 个分支选头节点（和循环体重复），
  循环条件写成 while list1 or list2，循环里再用 2 个分支处理「一边用完」。一边用完时循环里就 return，所以最后的 return head 是死代码：
  1525 次调用里执行 0 次。改用 dummy 后 14 行，所有特判都被「循环后接上剩余部分」覆盖。

易错点:
- 循环条件要写 and：只在两边都有节点时比较，剩下的交给循环后的一行。
- 忘了接剩余部分会丢尾巴，只接 list1 的剩余也会丢（示例 1 少了最后一个 4）。
- 两个分支对称，复制后逐项检查：接的是谁、移动的是谁。写成 list2 = list1.next 会成环。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeTwoLists(self, list1: ListNode | None, list2: ListNode | None) -> ListNode | None:
        tail = dummy = ListNode()
        while list1 is not None and list2 is not None:
            if list1.val <= list2.val:
                tail.next = list1
                list1 = list1.next
            else:
                tail.next = list2
                list2 = list2.next
            tail = tail.next
        tail.next = list1 if list1 else list2
        return dummy.next


if __name__ == "__main__":
    import itertools
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
    TIMED_OUT = object()  # 两条都空时正确答案就是 None，不能拿 None 当超时标记

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

    def call_with_limit(cls, a, b, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().mergeTwoLists(a, b)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(vals1, vals2):
        return sorted(vals1 + vals2)

    def check(cls, name, vals1, vals2, seconds=1.0):
        a, nodes1 = build(vals1)
        b, nodes2 = build(vals2)
        nodes = nodes1 + nodes2
        tag = f"{cls.__name__} {name}: 输入 {vals1} 和 {vals2}"
        try:
            got, elapsed = call_with_limit(cls, a, b, seconds)
        except Exception as e:  # 访问 None.next / None.val 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        # 多给一个名额：返回了哨兵节点时能看到多出来的那个值，而不是误报成环
        order = walk(got, len(nodes) + 1)
        assert order is not None, f"{tag}，从返回的头走了 {len(nodes) + 1} 个节点还没到 None，链表成环了"
        got_vals = [n.val for n in order]
        expected = reference(vals1, vals2)
        assert got_vals == expected, f"{tag}，期望 {expected}，得到 {got_vals}"
        assert [n.val for n in nodes] == vals1 + vals2, f"{tag}，值对了，但原节点的 val 被改了——要改 next 拼接，不是改值"
        assert {id(n) for n in order} == {id(n) for n in nodes}, (
            f"{tag}，值对了，但返回的不是原来那些节点——题目要求用原节点拼接，不要新建")
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [1, 2, 4], [1, 3, 4]),
        ("题目示例 2", [], []),
        ("题目示例 3", [], [0]),
        # 一条为空
        ("list2 为空", [0], []),
        ("list1 为空，list2 多个", [], [1, 2, 3]),
        # 单节点
        ("各一个，list1 小", [1], [2]),
        ("各一个，list2 小", [2], [1]),
        ("各一个，相等", [1], [1]),
        # 一条整体在另一条前面：循环结束后另一条剩下的整段要接上
        ("list1 全部更小", [1, 2, 3], [4, 5, 6]),
        ("list2 全部更小", [4, 5, 6], [1, 2, 3]),
        # 长短差很多：剩下的尾巴很长
        ("list1 很短", [5], [1, 2, 3, 4, 6, 7, 8]),
        ("list2 很短", [1, 2, 3, 4, 6, 7, 8], [5]),
        # 交错
        ("完全交错", [1, 3, 5, 7], [2, 4, 6, 8]),
        # 重复值
        ("全部相同", [2, 2, 2], [2, 2]),
        ("重复值跨两条", [1, 1, 3, 3], [1, 2, 3]),
        # 值域边界、负数
        ("值域边界", [-100, 0, 100], [-100, 100]),
        # 长度上限 50
        ("两条都是 50 个", list(range(0, 100, 2)), list(range(1, 100, 2))),
    ]

    # 穷举：值只取 0~2、长度 0~4 的所有有序链表两两配对（35 x 35 = 1225 组）
    small = [list(c) for k in range(5) for c in itertools.combinations_with_replacement(range(3), k)]
    for x in small:
        for y in small:
            cases.append((f"穷举 {x} + {y}", x, y))

    rng = random.Random(21)
    for i in range(300):  # 随机：长度 0~50，值域 -100~100
        x = sorted(rng.randint(-100, 100) for _ in range(rng.randint(0, 50)))
        y = sorted(rng.randint(-100, 100) for _ in range(rng.randint(0, 50)))
        cases.append((f"随机 #{i}", x, y))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, x, y in cases:
            check(cls, name, x, y)

    # 题目每条最多 50 个节点，规模太小，不做性能用例；复杂度看代码即可
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
