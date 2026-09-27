"""
Pattern: 快慢指针找中点 + 链表原地反转

Core:
- List: 把值存进 list，下标 i 和 -i-1 两头往中间比。
- Solution: 快指针每次两步、慢指针每次一步，快指针走到尾时慢指针停在下标 n // 2；从慢指针起把后半段原地反转，再从 head 和反转后的头同时往中间比 val。以后半段走到 None 为结束，前半段不用断开。

Time: O(n)
Space: List O(n)；Solution O(1)
实测 10 万节点回文：List 5.2 ms（额外内存 1.5 MB），Solution 7.5 ms（额外内存约 0）。

Mistake:
- 三处循环条件都写成了 x.next is not None，每处都漏掉最后一个节点：
  1. List 收集值：先放 head.val，再从 head 开始 append，并且走到尾节点就停，[1,2,2,1] 收集成 [1,1,2,2]。
  2. 反转后半段：走到尾节点就停，尾节点没接进 rev 链，[1,2,2,1] 的 rev 链只有 [2]。
  3. 比较：rev 链最后一个节点不比；[1,2] 时 rev 为 None 直接 None.next 崩溃。
  遍历要处理每个节点就写 while cur is not None，只有需要停在最后一个节点上才写 while cur.next is not None。

易错点:
- 找中点原写法 while fast.next 加内部 if 能用（n = 1..8 实测 slow 都在 n // 2），改成 while fast is not None and fast.next is not None 结果相同、少一个分支。
- 反转后半段后链表没有恢复原状，LeetCode 不检查。
"""


from __future__ import annotations

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class SolutionList:
    def isPalindrome(self, head: ListNode | None) -> bool:
        cur = head
        nums = []
        while cur is not None:
            nums.append(cur.val)
            cur = cur.next
        for i in range(len(nums) // 2):
            if nums[i] != nums[-i-1]:
                return False
        return True


class Solution:
    def isPalindrome(self, head: ListNode | None) -> bool:
        fast = slow = head
        while fast is not None and fast.next is not None:
            slow = slow.next
            fast = fast.next.next
        rev = None
        while slow is not None:
            nxt = slow.next
            slow.next = rev
            rev = slow
            slow = nxt
        cur = head
        while rev is not None:
            if cur.val != rev.val:
                return False
            cur = cur.next
            rev = rev.next
        return True


if __name__ == "__main__":
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
    TIMED_OUT = object()  # 和「忘了 return 得到 None」区分开

    def build(vals):
        head = None
        for v in reversed(vals):
            head = ListNode(v, head)
        return head

    def snapshot(head):
        # 记录每个节点的 (对象, next, val)，用来检查解法有没有改动链表
        out = []
        cur = head
        while cur is not None:
            out.append((cur, cur.next, cur.val))
            cur = cur.next
        return out

    def show(vals):
        return str(vals) if len(vals) <= 12 else f"长度 {len(vals)}"

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().isPalindrome(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def reference(vals):
        return vals == vals[::-1]

    modified = set()  # 改动了链表结构或 val 的类：LeetCode 不检查，只提示

    def check(cls, name, vals, seconds=1.0):
        head = build(vals)
        before = snapshot(head)
        tag = f"{cls.__name__} {name}"
        try:
            got, elapsed = call_with_limit(cls, head, seconds)
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}: 抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}: 超过 {seconds}s 被中断"
        expected = reference(vals)
        assert got is expected, f"{tag}: 输入 {show(vals)}，期望 {expected}，得到 {got!r}（要返回 bool，不能是 None 或 1/0）"
        if [(n, nxt, v) for n, nxt, v in before] != [(n, n.next, n.val) for n, _, _ in before]:
            modified.add(cls.__name__)
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [1, 2, 2, 1]),
        ("题目示例 2", [1, 2]),
        # 最短
        ("单节点", [7]),
        ("两个相同", [0, 0]),
        # 奇偶长度的回文：奇数长度时中间那个不用比
        ("奇数长度回文", [1, 2, 1]),
        ("奇数长度回文 2", [1, 2, 3, 2, 1]),
        ("偶数长度回文", [1, 2, 3, 3, 2, 1]),
        # 只有一处不对称，位置分别在两端和中间
        ("只有两端不同", [1, 2, 2, 3]),
        ("只有中间一对不同", [1, 2, 3, 4, 2, 1]),
        ("奇数长度，中间旁边不同", [1, 2, 3, 4, 1]),
        # 前半段或后半段自己是回文，整体不是
        ("前缀是回文", [1, 2, 1, 1]),
        ("后缀是回文", [1, 1, 2, 1]),
        ("末尾是 0", [1, 0, 0]),
        # 每个值出现偶数次但不是回文：拦「只数个数」
        ("值成对但顺序不对", [1, 2, 1, 2]),
        # 前半段等于后半段（不反转直接比）：拦「后半段忘了反转」
        ("前后两半相同", [1, 2, 3, 1, 2, 3]),
        # 全部相同
        ("全部相同", [5] * 9),
    ]

    rng = random.Random(234)
    for i in range(200):  # 随机回文
        half = [rng.randint(0, 9) for _ in range(rng.randint(0, 6))]
        mid = [rng.randint(0, 9)] if rng.random() < 0.5 or not half else []
        cases.append((f"随机回文 #{i}", half + mid + half[::-1]))
    for i in range(200):  # 回文改动一个位置，多数变成非回文
        half = [rng.randint(0, 9) for _ in range(rng.randint(1, 6))]
        vals = half + half[::-1]
        j = rng.randrange(len(vals))
        vals[j] = (vals[j] + rng.randint(1, 9)) % 10
        cases.append((f"随机近似回文 #{i}", vals))
    for i in range(200):  # 值域很小的随机序列，回文和非回文都有
        cases.append((f"随机 #{i}", [rng.randint(0, 1) for _ in range(rng.randint(1, 10))]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals in cases:
            check(cls, name, vals)

    # 性能：只测 Solution，节点数上限 10^5。本地实测 10 万节点回文：
    #   存进 list 再比较 4 ms（空间 O(n)），快慢指针 + 反转后半段 7 ms（空间 O(1)）；
    #   每次从头走到对称位置 O(n^2)，4000 节点已要 89 ms，10 万节点约 1 分钟；
    #   拼成大整数正反比较 1.9 s（大整数乘 10 每次 O(位数)，整体 O(n^2)）。
    # 递归写法（前指针 + 递归到尾）在 10 万节点会 RecursionError；把递归上限放宽到 20 万，
    # 本地直接段错误退出（exit 139，已实测），所以不放宽。递归解请命名为 Solution<Approach>，只跑小用例
    n = 100_000
    half = [rng.randint(0, 9) for _ in range(n // 2)]
    big_yes = half + half[::-1]
    big_mid = big_yes[:]
    big_mid[n // 2] = (big_mid[n // 2] + 1) % 10  # 只有正中间一对不同，必须比到最后
    big_end = big_yes[:]
    big_end[-1] = (big_end[-1] + 1) % 10          # 只有两端不同
    timings = []
    for name, vals in [("10 万节点回文", big_yes), ("10 万节点只有中间不同", big_mid),
                       ("10 万节点只有两端不同", big_end)]:
        timings.append(check(Solution, name, vals))

    # 进阶要求 O(1) 空间：只打印峰值额外内存，不作为失败条件
    head = build(big_yes)
    tracemalloc.start()
    Solution().isPalindrome(head)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"10 万节点 {' / '.join(f'{t * 1000:.0f}' for t in timings)} ms; 额外内存峰值 {peak / 1024:.1f} KB)")
    if modified:
        print(f"注意：{', '.join(sorted(modified))} 调用后链表被改动了（next 或 val），LeetCode 不检查，但最好恢复原状")
