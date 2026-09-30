"""
Pattern: 快慢指针判环 + 推导入环点

Core:
- Set: 用 set 记走过的节点（记对象，不是 val），第一个重复遇到的节点就是入口；走到 None 说明无环。
- Solution: 第一阶段同 141，快慢指针同时从 head 出发，先移动再比较，相遇就停；快指针走到 None 或尾节点说明无环。
  第二阶段 slow 放回 head，两个指针每次各走 1 步，第一次相等处就是入口。
  推导：设 head 到入口 a 步、入口到相遇点 b 步、相遇点回到入口 c 步。慢指针进环后不到一圈就被追上，走了 a + b；
  快指针多绕 k 圈（k >= 1），走了 a + b + k(b + c) = 2(a + b)，得 a = (k - 1)(b + c) + c。
  从相遇点走 a 步 = 走 c 步到入口再绕 k - 1 整圈，仍停在入口；head 那个指针进环前两者不可能重合，所以第一次相等就是入口。

Time: O(n)
Space: Set O(n)；Solution O(1)
实测 1 万节点、入口在中间：Solution 0.3 ms，Set 0.4 ms（额外内存 640 KB）。
枚举 n <= 300 的所有入环位置：慢指针进环后从不超过一圈，恰好一圈的只有 a = 0；k 最大 299（长尾巴、环长 1）。

Mistake:
- 第一版把 fast is not slow 放进循环条件：同时出发时条件一开始就为假，循环一次不执行，只要节点数不少于 2 就返回 head（[3,2,0,-4] 得到下标 0，[1,2] 无环也得到下标 0）。要先移动再比较。
- 两处没判 fast 本身是不是 None：循环里 fast = fast.next.next 可能变成 None，下一轮 fast.next 崩溃；空链表时循环后的 fast.next 崩溃。
- 修到一半时循环后只写了 if fast is None：无环且奇数长度时快指针停在尾节点而不是 None，于是进了第二阶段，[1] 返回 head，[1,2,3] 崩溃。无环的判断要和循环条件对应，写 fast is None or fast.next is None；最终版改用 while ... else：else 只在循环没被 break 打断时执行，正好对应「没相遇 = 无环」，不用把循环条件再写一遍。

易错点:
- a 不一定等于 c：只有 k = 1 时相等。n=7 pos=5 时 a=5、c=1、环长 2、k=3，从相遇点出发的指针走 1 步就到入口，但要再绕 2 圈等 head 那边走完尾巴。
- 题目要求不修改链表，141 的标记法在这题不合规。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None


class SolutionSet:
    def detectCycle(self, head: ListNode | None) -> ListNode | None:
        seen = set()
        cur = head
        while cur is not None:
            if cur in seen:
                return cur
            seen.add(cur)
            cur = cur.next
        return None


class Solution:
    def detectCycle(self, head: ListNode | None) -> ListNode | None:
        fast = slow = head
        while fast is not None and fast.next is not None:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                break
        else:
            return None
        slow = head
        while fast is not slow:
            fast = fast.next
            slow = slow.next
        return fast


if __name__ == "__main__":
    import random
    import signal
    import time
    import tracemalloc

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
    TIMED_OUT = object()  # 无环时正确答案就是 None，不能拿 None 当超时标记

    def build(vals, pos):
        """返回 (head, nodes)。pos >= 0 时尾节点的 next 指回 nodes[pos]，-1 表示无环。"""
        nodes = [ListNode(v) for v in vals]
        for a, b in zip(nodes, nodes[1:]):
            a.next = b
        if pos >= 0:
            nodes[-1].next = nodes[pos]
        return (nodes[0] if nodes else None), nodes

    def show(vals, pos):
        return f"{vals} pos={pos}" if len(vals) <= 12 else f"长度 {len(vals)} pos={pos}"

    def describe(got, nodes):
        # 把返回值翻译成「第几个节点」，方便看差了几步
        if got is None:
            return "None"
        for i, n in enumerate(nodes):
            if got is n:
                return f"下标 {i} 的节点（val={n.val}）"
        return f"不在原链表里的 {type(got).__name__} {got!r}（要返回节点本身）"

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().detectCycle(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def check(cls, name, vals, pos, seconds=1.0, hint="有环时一直沿 next 走，或者第二阶段两个指针差一步、永远碰不上？"):
        head, nodes = build(vals, pos)
        before = [(n.next, n.val) for n in nodes]
        tag = f"{cls.__name__} {name}"
        try:
            got, elapsed = call_with_limit(cls, head, seconds)
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}: 输入 {show(vals, pos)}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}: 输入 {show(vals, pos)}，超过 {seconds}s 被中断（{hint}）"
        # 期望值直接由 pos 决定，不走链表
        expected = nodes[pos] if pos >= 0 else None
        assert got is expected, (
            f"{tag}: 输入 {show(vals, pos)}，期望 {describe(expected, nodes)}，得到 {describe(got, nodes)}")
        # 题目明确要求不能修改链表，所以这里是失败而不是提示（141 的标记法在这题不合规）
        assert before == [(n.next, n.val) for n in nodes], f"{tag}: 输入 {show(vals, pos)}，题目要求不修改链表，但 next 或 val 被改了"
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [3, 2, 0, -4], 1),
        ("题目示例 2", [1, 2], 0),
        ("题目示例 3", [1], -1),
        # 空链表
        ("空链表", [], -1),
        # 自环
        ("单节点自环", [1], 0),
        ("尾节点自环", [1, 2, 3], 2),
        # 整条是环：入口是 head，快慢指针也恰好在 head 相遇
        ("整条是环", [1, 2, 3, 4], 0),
        # 入口在中间
        ("入口在中间", [1, 2, 3, 4, 5], 2),
        # 环外尾巴远长于环：第二阶段要绕环好几圈
        ("长尾巴自环", list(range(20)), 19),
        ("长尾巴两节点环", list(range(20)), 18),
        # 环远长于环外尾巴
        ("短尾巴长环", list(range(20)), 1),
        # 值重复：按 val 判断会找错入口
        ("值全相同，入口在中间", [7] * 6, 3),
        ("值重复但无环", [1, 1], -1),
        # 值域边界
        ("值域边界", [-100000, 100000], 0),
    ]

    # 穷举所有形状：n <= 30 的每一个入口位置（含无环），值只取 0~2，重复很多
    for n in range(1, 31):
        for pos in range(-1, n):
            cases.append((f"穷举 n={n} pos={pos}", [i % 3 for i in range(n)], pos))

    rng = random.Random(142)
    for i in range(100):  # 随机值
        n = rng.randint(0, 40)
        pos = rng.randint(-1, n - 1) if n else -1
        cases.append((f"随机 #{i}", [rng.randint(-5, 5) for _ in range(n)], pos))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals, pos in cases:
            check(cls, name, vals, pos)

    # 性能：只测 Solution，节点数上限 10^4。本地实测 1 万节点、入口在中间：
    #   快慢指针 0.3 ms，set 记节点 0.4 ms（额外内存 640 KB）；
    #   用 list 记走过的节点、每步 in 查找 O(n^2)，227 ms。预算给 30 ms
    n = 10_000
    big = list(range(n))
    timings = []
    for name, pos in [("1 万节点无环", -1), ("1 万节点整条是环", 0),
                      ("1 万节点入口在中间", n // 2), ("1 万节点尾节点自环", n - 1)]:
        timings.append(check(Solution, name, big, pos, seconds=0.03,
                             hint="可能是 O(n^2)，例如每步在 list 里查找走过的节点"))

    # 进阶要求 O(1) 空间：只打印峰值额外内存，不作为失败条件
    head, _ = build(big, n // 2)
    tracemalloc.start()
    Solution().detectCycle(head)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1 万节点 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms; 额外内存峰值 {peak / 1024:.1f} KB)")
