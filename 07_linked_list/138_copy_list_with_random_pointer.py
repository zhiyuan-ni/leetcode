"""
Pattern: 哈希表映射 / 交错插入

Core:
- Dict: 两遍。第一遍为每个原节点建只带 val 的拷贝，存进 copies（键是原节点对象，不是 val）；第二遍按 copies[cur.next]、
  copies[cur.random] 接指针。字典里预先放 None: None，空指针不用单独判断。
- Solution: 三遍。插入：每个原节点后面插入它的拷贝，A -> A' -> B -> B'；接 random：A'.random = A.random.next；
  拆分：先 cur.next = clone.next，再 clone.next = clone.next.next（最后一个拷贝的 next 是 None）。
  random 必须在拆分之前单独一遍接好：边拆边接时，往前指的 random 找到的是已经恢复的原节点。

Time: O(n)
Space: Dict O(n)；Solution O(1) 额外空间（不算结果本身）
实测 1000 个节点：Dict 0.3 ms，额外内存 36 KB；Solution 0.4 ms，额外内存 0 KB。
copy.deepcopy(head) 结果也对，但它递归复制，每个节点约 4 层：默认递归上限下最多 249 个节点，放宽后 2.7 ms、额外内存 2.4 MB。

Mistake:
- Dict 第一版：while not cur 条件写反（非空时一次不执行，空链表时 None.val 崩溃）；for node, _ in copies 以为遍历字典
  得到键值对，实际只有键，拆包 TypeError；改成遍历字典后 None 键也被遍历到，None.next 崩溃。改成再沿链表走一遍。
- Solution 第一版，把接 random 和拆分放在同一遍：先 copy.next = copy.next.next 再 cur.next = cur.next.next，
  后者读到的已经是下一个拷贝，原链表被破坏；最后一个拷贝 None.next 崩溃；拆分后才 return head.next，返回了原节点 1；
  random 往前指的（13->0、10->2、1->0）拿到原节点；空链表 head.next 崩溃。
- Solution 第二版：最后一对单独特判后直接 return，循环后的 return None 在 8477 组穷举里执行 0 次，是死代码。

易错点:
- 不能按 val 建映射：[3,3,3] 时 random 会指错节点。
- 变量名 copy 和标准库模块 copy 同名，以后 import copy 会冲突，改叫 clone。
"""


from __future__ import annotations

class Node:
    def __init__(self, x: int, next: "Node" = None, random: "Node" = None):
        self.val = int(x)
        self.next = next
        self.random = random


class SolutionDict:
    def copyRandomList(self, head: "Node | None") -> "Node | None":
        cur = head
        copies = {None: None}
        while cur:
            copies[cur] = Node(cur.val)
            cur = cur.next
        cur = head
        while cur:
            copies[cur].next = copies[cur.next]
            copies[cur].random = copies[cur.random]
            cur = cur.next
        return copies[head]


class Solution:
    def copyRandomList(self, head: "Node | None") -> "Node | None":
        if not head:
            return None
        cur = head
        while cur:
            clone = Node(cur.val, cur.next)
            cur.next = clone
            cur = clone.next

        cur = head
        while cur:
            cur.next.random = cur.random.next if cur.random else None
            cur = cur.next.next

        cur = head
        new_head = head.next
        while cur:
            clone = cur.next
            cur.next = clone.next
            clone.next = clone.next.next if clone.next else None
            cur = cur.next
        return new_head


if __name__ == "__main__":
    import itertools
    import random
    import signal
    import time
    import tracemalloc

    if "Node" not in globals():
        class Node:  # 提交到 LeetCode 时用平台自带的定义，这里本地补一个
            def __init__(self, x: int, next: "Node" = None, random: "Node" = None):
                self.val = int(x)
                self.next = next
                self.random = random

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)
    TIMED_OUT = object()  # 空链表的正确答案就是 None，不能拿 None 当超时标记

    def build(vals, rnd):
        """rnd[i] 是第 i 个节点 random 指向的下标，None 表示空。返回 (head, nodes)。"""
        nodes = [Node(v) for v in vals]
        for a, b in zip(nodes, nodes[1:]):
            a.next = b
        for node, j in zip(nodes, rnd):
            node.random = None if j is None else nodes[j]
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

    def show(vals, rnd):
        return f"{[[v, r] for v, r in zip(vals, rnd)]}" if len(vals) <= 8 else f"{len(vals)} 个节点"

    def call_with_limit(cls, head, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().copyRandomList(head)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def check(cls, name, vals, rnd, seconds=1.0, hint="可能死循环"):
        head, nodes = build(vals, rnd)
        before = [(n.val, n.next, n.random) for n in nodes]
        tag = f"{cls.__name__} {name}: 输入 {show(vals, rnd)}"
        try:
            got, elapsed = call_with_limit(cls, head, seconds)
        except Exception as e:  # 访问 None.next 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        # 题目会检查原链表：交错插入的写法最后必须把原链表拆回来
        changed = [i for i, (n, b) in enumerate(zip(nodes, before)) if (n.val, n.next, n.random) != b]
        assert not changed, f"{tag}，原链表被改了（第一个被改的是下标 {changed[0]}）——交错插入后要把原链表恢复"
        # 多给一个名额：多挂了节点时能看到，而不是误报成环
        copy = walk(got, len(nodes) + 1)
        assert copy is not None, f"{tag}，从返回的头走了 {len(nodes) + 1} 个节点还没到 None，链表成环了"
        assert len(copy) == len(nodes), f"{tag}，期望 {len(nodes)} 个节点，得到 {len(copy)} 个"
        originals = {id(n) for n in nodes}
        shared = [i for i, c in enumerate(copy) if id(c) in originals]
        assert not shared, f"{tag}，下标 {shared[0]} 返回的是原节点——要深拷贝，每个节点都新建"
        assert [c.val for c in copy] == vals, f"{tag}，val 不对：期望 {vals}，得到 {[c.val for c in copy]}"
        # random 要指向「拷贝里对应位置的节点」：翻译成拷贝内的下标再比
        index = {id(c): i for i, c in enumerate(copy)}
        got_rnd = []
        for c in copy:
            if c.random is None:
                got_rnd.append(None)
            elif id(c.random) in index:
                got_rnd.append(index[id(c.random)])
            elif id(c.random) in originals:
                got_rnd.append("原节点")
            else:
                got_rnd.append("链表外的节点")
        assert got_rnd == list(rnd), f"{tag}，random 指向的下标期望 {list(rnd)}，得到 {got_rnd}"
        return elapsed

    cases = [
        # 题目示例：[val, random 下标]
        ("题目示例 1", [7, 13, 11, 10, 1], [None, 0, 4, 2, 0]),
        ("题目示例 2", [1, 2], [1, 1]),
        ("题目示例 3", [3, 3, 3], [None, 0, None]),
        ("空链表", [], []),
        # random 的各种指向
        ("单节点 random 为空", [1], [None]),
        ("单节点 random 指向自己", [1], [0]),
        ("全部指向自己", [1, 2, 3], [0, 1, 2]),
        ("全部指向头", [1, 2, 3], [0, 0, 0]),
        ("全部指向尾", [1, 2, 3], [2, 2, 2]),
        ("全部为空", [1, 2, 3], [None, None, None]),
        ("全部往回指", [1, 2, 3, 4], [None, 0, 1, 2]),
        ("全部往后指", [1, 2, 3, 4], [1, 2, 3, None]),
        # 值重复：按 val 建映射会指错节点
        ("值全相同，random 各不相同", [5, 5, 5, 5], [3, 0, 2, 1]),
        # 值域边界
        ("值域边界", [-10000, 10000], [1, 0]),
    ]

    # 穷举：长度 0~5 的每一种 random 指向组合（每个节点 n+1 种选择，共 8477 组）；值全为 0，只能靠结构区分
    for size in range(6):
        for rnd in itertools.product([None] + list(range(size)), repeat=size):
            cases.append((f"穷举 n={size} random={list(rnd)}", [0] * size, list(rnd)))

    rng = random.Random(138)
    for i in range(200):  # 随机：长度 0~1000（题目上限），值域 -10^4~10^4
        size = rng.randint(0, 1000)
        cases.append((f"随机 #{i}", [rng.randint(-10000, 10000) for _ in range(size)],
                      [rng.choice([None] + list(range(size))) for _ in range(size)]))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, vals, rnd in cases:
            check(cls, name, vals, rnd)

    # 性能：只测 Solution，1000 个节点（题目上限）。本地实测（random 全部指向尾 / 随机）：
    #   哈希表 0.3 / 0.3 ms，交错插入 0.4 / 0.4 ms；
    #   每个节点从头走一遍找 random 的下标 O(n^2)：27 / 4 ms。随机指向时 O(n^2) 只要 4 ms 拦不住，
    #   靠「全部指向尾」那组拦；预算给 10 ms（正确写法 25 倍余量，O(n^2) 超出近 3 倍）
    n = 1000
    big_vals = list(range(n))
    timings = []
    for name, rnd in [("random 全部指向尾", [n - 1] * n), ("random 随机", [rng.randrange(n) for _ in range(n)])]:
        timings.append(check(Solution, f"性能：1000 个节点，{name}", big_vals, rnd, seconds=0.01,
                             hint="可能是 O(n^2)，例如每个节点都从头走一遍去找 random 的位置"))

    # 进阶思路是 O(1) 额外空间（不算结果本身）：峰值减去调用结束后仍占着的（就是拷贝出来的链表），只打印不判失败
    head, _ = build(big_vals, [rng.randrange(n) for _ in range(n)])
    tracemalloc.start()
    result = Solution().copyRandomList(head)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; "
          f"1000 个节点 {' / '.join(f'{t * 1000:.1f}' for t in timings)} ms; "
          f"结果占 {current / 1024:.0f} KB，额外峰值 {(peak - current) / 1024:.1f} KB)")