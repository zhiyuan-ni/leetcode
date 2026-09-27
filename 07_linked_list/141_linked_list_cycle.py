"""
Pattern: 快慢指针判环

Core:
- Mark: 把走过的节点的 val 标成 inf（题目 val 在 [-10^5, 10^5]，不会冲突），再遇到 inf 说明回到了走过的节点。会改掉输入。
- Solution: 快慢指针同时从 head 出发，慢的每次 1 步、快的每次 2 步，移动之后再比较 slow is fast。有环时，进环后两者的差距每步正好缩小 1，不会跳过，最多一圈内相遇；无环时快指针先走到 None。

Time: O(n)
Space: O(1)
实测 1 万节点无环：Solution 0.2 ms，Mark 0.41 ms，set 记节点 0.4 ms（额外内存 640 KB）。
枚举 n <= 300 的所有入环位置，快慢指针相遇所需步数最多正好是 n。

Mistake:
- Mark 第一版每步写 float('inf')：每次调用都新建一个 float 对象，1 万个节点各持有一个，额外内存 232 KB，实际是 O(n) 空间；还要每步查全局名 float 再调用，1.15 ms。提到循环外只建一次后，内存约 0、0.41 ms。

易错点:
- 标记法依赖 val 的取值范围已知，并且会破坏输入，调用后所有 val 都变成 inf。
- 快慢指针同时出发，一开始 slow is fast 就成立，比较必须放在移动之后，否则无环的 [1,2] 也返回 True。
- 循环条件要写 fast is not None and fast.next is not None，空链表、奇偶长度都不会访问 None.next。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None


class SolutionMark:
    def hasCycle(self, head: ListNode | None) -> bool:
        mark = float('inf')
        cur = head
        while cur is not None:
            if cur.val == mark:
                return True
            cur.val = mark
            cur = cur.next
        return False


class Solution:
    def hasCycle(self, head: ListNode | None) -> bool:
        fast = slow = head
        while fast is not None and fast.next is not None:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                return True
        return False


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
    TIMED_OUT = object()  # 和「忘了 return 得到 None」区分开

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

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().hasCycle(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(vals, pos):
        # 期望值只由 pos 决定，不走链表
        return pos >= 0

    modified = set()  # 改动了 next 或 val 的类（比如把走过的节点标记掉）：LeetCode 不检查，只提示

    def check(cls, name, vals, pos, seconds=1.0, hint="有环时一直沿 next 走就停不下来？"):
        head, nodes = build(vals, pos)
        before = [(n.next, n.val) for n in nodes]
        tag = f"{cls.__name__} {name}"
        try:
            got, elapsed = call_with_limit(cls, head, seconds)
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}: 输入 {show(vals, pos)}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}: 输入 {show(vals, pos)}，超过 {seconds}s 被中断（{hint}）"
        expected = reference(vals, pos)
        assert got is expected, f"{tag}: 输入 {show(vals, pos)}，期望 {expected}，得到 {got!r}（要返回 bool）"
        if before != [(n.next, n.val) for n in nodes]:
            modified.add(cls.__name__)
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [3, 2, 0, -4], 1),
        ("题目示例 2", [1, 2], 0),
        ("题目示例 3", [1], -1),
        # 空链表
        ("空链表", [], -1),
        # 自环：环长 1
        ("单节点自环", [1], 0),
        ("尾节点自环", [1, 2, 3], 2),
        # 整条链都是环
        ("整条是环，奇数长度", [1, 2, 3], 0),
        ("整条是环，偶数长度", [1, 2, 3, 4], 0),
        # 无环，奇偶长度（快指针走到 None 和走到尾节点两种退出方式）
        ("无环，两个节点", [1, 2], -1),
        ("无环，奇数长度", [1, 2, 3], -1),
        ("无环，偶数长度", [1, 2, 3, 4], -1),
        # 值重复：按 val 判断「走过没有」会误判
        ("值重复但无环", [1, 1], -1),
        ("值全相同但无环", [7] * 6, -1),
        # 环入口不在头也不在尾：只检查「尾是否指回头」会漏
        ("环入口在中间", [1, 2, 3, 4, 5], 2),
        # 环外很长、环很短
        ("长尾巴短环", list(range(20)), 18),
        # 值域边界
        ("值域边界", [-100000, 100000], 0),
    ]

    rng = random.Random(141)
    for i in range(500):
        n = rng.randint(0, 15)
        pos = rng.randint(-1, n - 1) if n else -1
        if n and rng.random() < 0.3:
            pos = -1  # 多一些无环的
        cases.append((f"随机 #{i}", [rng.randint(0, 3) for _ in range(n)], pos))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals, pos in cases:
            check(cls, name, vals, pos)

    # 性能：只测 Solution，节点数上限 10^4。本地实测 1 万节点无环：
    #   快慢指针 0.2 ms，set 记节点 0.4 ms（额外内存 640 KB）；
    #   用 list 记走过的节点、每步 in 查找 O(n^2)，227 ms。预算给 30 ms
    n = 10_000
    big = list(range(n))
    timings = []
    for name, pos in [("1 万节点无环", -1), ("1 万节点整条是环", 0), ("1 万节点尾节点自环", n - 1)]:
        timings.append(check(Solution, name, big, pos, seconds=0.03,
                             hint="可能是 O(n^2)，例如每步在 list 里查找走过的节点"))

    # 进阶要求 O(1) 空间：只打印峰值额外内存，不作为失败条件
    head, _ = build(big, -1)
    tracemalloc.start()
    Solution().hasCycle(head)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1 万节点 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms; 额外内存峰值 {peak / 1024:.1f} KB)")
    if modified:
        print(f"注意：{', '.join(sorted(modified))} 调用后链表被改动了（next 或 val），LeetCode 不检查，但最好不要改输入")
