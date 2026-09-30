"""
Pattern: 虚拟头节点 + 逐位相加带进位

Core:
- 两条链表低位在前，正好从个位开始加。用完的一边当 0，两边都有、只有一边、只剩进位这几种情况用同一段计算：
  total = val1 + val2 + carry，当前位 total % 10，进位 total // 10。循环条件 l1 or l2 or carry，最后的进位也由循环生成。

Time: O(max(m, n))
Space: O(max(m, n))，结果链表；输入不改动

Mistake:
- （本题第一版就通过全部用例，问题在写法）第一版同一段「算和、更新进位、建节点、前进」写了三遍：两边都有一段、只剩 l1 一段、只剩 l2 一段，
  最后再特判进位，方法体 26 行；外层 if l1 / elif l2 和里面的 while 重复检查。用完的一边当 0 后合成一个循环，再把 carry 并进循环条件，12 行。

易错点:
- 短的那条用完后不能把长的那条剩余部分直接接上：进位还要继续往下传，999 + 1 应得 0001。
- 最后还有进位要多生成一位：5 + 5 = [0, 1]。
- 转成大整数相加在 Python 里能过（整数无上限），但其他语言 100 位会溢出，本题考的是逐位进位。
"""


from __future__ import annotations

# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next


class Solution:
    def addTwoNumbers(self, l1: ListNode | None, l2: ListNode | None) -> ListNode | None:
        tail = dummy = ListNode()
        carry = 0
        while l1 or l2 or carry:
            val1 = l1.val if l1 else 0
            val2 = l2.val if l2 else 0
            total = val1 + val2 + carry
            carry = total // 10
            tail.next = ListNode(total % 10)
            tail = tail.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
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
    TIMED_OUT = object()  # 和「忘了 return 得到 None」区分开

    def digits(num):
        """整数 -> 逆序数位列表，342 -> [2, 4, 3]。"""
        return [int(c) for c in reversed(str(num))]

    def build(ds):
        """返回 (head, nodes)，nodes 按原顺序保存每个节点对象。"""
        nodes = [ListNode(d) for d in ds]
        for a, b in zip(nodes, nodes[1:]):
            a.next = b
        return (nodes[0] if nodes else None), nodes

    def walk(head, limit):
        """沿 next 走，最多 limit 个节点；还没到 None 就返回 None（说明成环或结果太长）。"""
        out = []
        cur = head
        while cur is not None:
            if len(out) == limit:
                return None
            out.append(cur)
            cur = cur.next
        return out

    def show(ds):
        return str(ds) if len(ds) <= 12 else f"{len(ds)} 位"

    def call_with_limit(cls, a, b, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().addTwoNumbers(a, b)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(ds1, ds2):
        # 用 Python 大整数直接相加，和逐位进位是两套独立的逻辑
        to_int = lambda ds: int("".join(map(str, reversed(ds))))
        return digits(to_int(ds1) + to_int(ds2))

    modified = set()  # 改动了输入链表（复用 l1 / l2 的节点存结果）的类：LeetCode 不检查，只提示

    def check(cls, name, ds1, ds2, seconds=1.0):
        a, nodes1 = build(ds1)
        b, nodes2 = build(ds2)
        before = [(n.next, n.val) for n in nodes1 + nodes2]
        tag = f"{cls.__name__} {name}: 输入 {show(ds1)} + {show(ds2)}"
        try:
            got, _ = call_with_limit(cls, a, b, seconds)
        except Exception as e:  # 访问 None.val 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，可能死循环"
        expected = reference(ds1, ds2)
        # 结果最多比长的那条多 1 位；多给一个名额，返回了哨兵节点时能看到多出来的那一位
        order = walk(got, len(expected) + 1)
        assert order is not None, f"{tag}，从返回的头走了 {len(expected) + 1} 个节点还没到 None，链表成环了"
        got_ds = [n.val for n in order]
        assert got_ds == expected, f"{tag}，期望 {show(expected)}，得到 {show(got_ds)}" + (
            f"（第一处不同在下标 {next(i for i, (x, y) in enumerate(zip(got_ds, expected)) if x != y)}）"
            if len(got_ds) == len(expected) and len(expected) > 12 else "")
        if before != [(n.next, n.val) for n in nodes1 + nodes2]:
            modified.add(cls.__name__)

    cases = [
        # 题目示例
        ("题目示例 1", [2, 4, 3], [5, 6, 4]),
        ("题目示例 2", [0], [0]),
        ("题目示例 3", [9] * 7, [9] * 4),
        # 最高位进位：结果比两条都长
        ("最后还有进位", [5], [5]),
        ("最后还有进位，多位", [9, 9], [1]),
        # 长短不一：短的那条用完后，进位还要沿长的那条一路传下去
        ("进位传过整条长链", [1], [9, 9, 9]),
        ("进位传过整条长链（反过来）", [9, 9, 9], [1]),
        ("进位在长链中途停下", [1], [9, 9, 3, 4]),
        # 长短不一但没有进位
        ("无进位，list1 长", [1, 2, 3], [4]),
        ("无进位，list2 长", [4], [1, 2, 3]),
        # 加 0
        ("0 加多位数", [0], [1, 2]),
        ("多位数加 0", [1, 2], [0]),
        # 每一位都恰好凑 10
        ("每位和都是 10", [1, 2, 3], [9, 8, 7]),
        # 每一位和都是 9：进位为 0，但只要中间误加 1 就会连锁出错
        ("每位和都是 9", [1, 2, 3, 4], [8, 7, 6, 5]),
        # 长度上限 100 位，并且进位传过 100 位
        ("100 个 9 加 1", [9] * 100, [1]),
        ("两个 100 个 9", [9] * 100, [9] * 100),
    ]

    # 穷举：0~199 的所有两两组合（4 万组），覆盖 1~3 位、各种进位位置和长短组合
    for x in range(200):
        for y in range(200):
            cases.append((f"穷举 {x}+{y}", digits(x), digits(y)))

    rng = random.Random(2)
    for i in range(300):  # 随机：长度 1~100，最高位不为 0（除非数字就是 0）
        ds = []
        for _ in range(2):
            n = rng.randint(1, 100)
            d = [rng.randint(0, 9) for _ in range(n - 1)] + [rng.randint(1, 9)] if n > 1 else [rng.randint(0, 9)]
            ds.append(d)
        cases.append((f"随机 #{i}", ds[0], ds[1]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, x, y in cases:
            check(cls, name, x, y)

    # 每条最多 100 位，规模太小，不做性能用例
    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例)")
    if modified:
        print(f"注意：{', '.join(sorted(modified))} 调用后输入链表被改动了，LeetCode 不检查，但最好不要改输入")
