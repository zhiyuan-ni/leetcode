"""
Pattern: 最小堆多路归并

Core:
- BruteForce: 复制一份 k 个头，每次扫一遍找最小的接到尾巴上，该条前进一步，全空时结束。
- Solution: 把各条非空的头以 (val, i, node) 放进最小堆，i 是链表下标，值相同时用它比较，避免比较两个 ListNode。
  每次弹出最小的接到 tail 后面，它的 next 非空就入堆；堆空时结束。空的 lists 和全是空链表都自然返回 None。

Time: BruteForce O(kN)；Solution O(N log k)
Space: BruteForce O(k)（复制头）；Solution O(k)（堆）
实测总节点数 1 万（1 万条单节点 / 100 条各 100 个 / 1 条 1 万个）：BruteForce 3415 / 49 / 1.3 ms，Solution 4.1 / 2.4 / 1.2 ms。

Mistake:
- Solution 第一版三处：空链表也入堆，lists[i].val 在 [[]] 时 None.val 崩溃；一轮里 heappop 两次（分别取下标和节点），
  每轮丢一个节点，示例 1 IndexError；while True 里先 pop 后判空，lists = [] 时从空堆 pop。用户在复盘前自己改好。
- BruteForce 写成 heads = lists 没有复制，heads[min_i] = ... 改的就是调用方的 lists，调用后全变成 None。改为 list(lists)。
- Solution 第二版开头 if not lists: return None 是多余的：lists 为空时堆也为空，直接返回 dummy.next。

易错点:
- 堆里只放 (val, node) 时，值相同会比较到两个 ListNode，TypeError；要加下标打破平局。
- 一条一条依次合并也是 O(kN)：1 万条单节点 1492 ms。
"""


from __future__ import annotations
import heapq

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class SolutionBruteForce:
    def mergeKLists(self, lists: list[ListNode | None]) -> ListNode | None:
        cur = dummy = ListNode(0)
        heads = list(lists)
        while True:
            min_i = -1
            for i in range(len(heads)):
                if heads[i] is not None:
                    if min_i == -1 or heads[i].val < heads[min_i].val:
                        min_i = i
            if min_i == -1:
                break

            cur.next = heads[min_i]
            cur = cur.next
            heads[min_i] = heads[min_i].next
        return dummy.next


class Solution:
    def mergeKLists(self, lists: list[ListNode | None]) -> ListNode | None:
        minheap = []
        for i, node in enumerate(lists):
            if node:
                heapq.heappush(minheap, (node.val, i, node))
        tail = dummy = ListNode(-1)
        while minheap:
            _, i, node = heapq.heappop(minheap)
            tail.next = node
            tail = tail.next
            if node.next:
                heapq.heappush(minheap, (node.next.val, i, node.next))
        return dummy.next


if __name__ == "__main__":
    import itertools
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
    TIMED_OUT = object()  # 全是空链表时正确答案就是 None，不能拿 None 当超时标记

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

    def show(groups):
        total = sum(map(len, groups))
        return str(groups) if total <= 12 and len(groups) <= 6 else f"{len(groups)} 条链表共 {total} 个节点"

    def call_with_limit(cls, lists, seconds):
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            start = time.perf_counter()
            got = cls().mergeKLists(lists)
            return got, time.perf_counter() - start
        except Timeout:
            return TIMED_OUT, None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    # 下面几种情况题目没禁止、LeetCode 也不检查，只提示
    changed_input, new_nodes, rewrote_vals = set(), set(), set()

    def check(cls, name, groups, seconds=1.0, hint="可能死循环"):
        built = [build(g) for g in groups]
        lists = [h for h, _ in built]
        lists_before = list(lists)
        nodes = [n for _, ns in built for n in ns]
        tag = f"{cls.__name__} {name}: 输入 {show(groups)}"
        try:
            got, elapsed = call_with_limit(cls, lists, seconds)
        except Exception as e:  # 访问 None.val、堆里比较节点、空堆 pop 等，带上用例名再抛
            raise AssertionError(f"{tag}，抛出 {type(e).__name__}: {e}") from e
        assert got is not TIMED_OUT, f"{tag}，超过 {seconds}s 被中断，{hint}"
        # 多给一个名额：多挂了哨兵节点时能看到，而不是误报成环
        order = walk(got, len(nodes) + 1)
        assert order is not None, f"{tag}，从返回的头走了 {len(nodes) + 1} 个节点还没到 None，链表成环了"
        got_vals = [n.val for n in order]
        expected = sorted(v for g in groups for v in g)
        if got_vals != expected:
            if len(expected) <= 12:
                detail = f"期望 {expected}，得到 {got_vals}"
            elif len(got_vals) != len(expected):
                detail = f"期望 {len(expected)} 个节点，得到 {len(got_vals)} 个（丢了节点或多了节点）"
            else:
                i = next(i for i, (x, y) in enumerate(zip(got_vals, expected)) if x != y)
                detail = f"第一处不同在位置 {i}：期望 {expected[i:i + 5]}，得到 {got_vals[i:i + 5]}"
            raise AssertionError(f"{tag}，{detail}")
        originals = {id(n) for n in nodes}
        if any(id(n) not in originals for n in order):
            new_nodes.add(cls.__name__)
        elif [n.val for n in nodes] != [v for g in groups for v in g]:
            rewrote_vals.add(cls.__name__)
        if lists != lists_before:
            changed_input.add(cls.__name__)
        return elapsed

    cases = [
        # 题目示例
        ("题目示例 1", [[1, 4, 5], [1, 3, 4], [2, 6]]),
        ("题目示例 2", []),
        ("题目示例 3", [[]]),
        # 空链表：全空、夹在中间、在两头
        ("两条都空", [[], []]),
        ("空链表夹在中间", [[1, 3], [], [2]]),
        ("第一条为空", [[], [1], [0]]),
        # 只有一条
        ("只有一条", [[1, 2, 3]]),
        # 值相同：堆里 (val, node) 比较到节点会 TypeError，要加下标打破平局
        ("各条首元素相同", [[1, 2], [1, 3], [1, 4]]),
        ("全部相同", [[5, 5], [5], [5, 5, 5]]),
        # 一条整体在另一条前面
        ("首尾相接", [[4, 5, 6], [1, 2, 3]]),
        # 负数、值域边界
        ("值域边界", [[-10000, 0], [-10000, 10000], [10000]]),
        # 很多条单节点
        ("十条单节点", [[i] for i in range(9, -1, -1)]),
    ]

    # 穷举：0~3 条链表，每条长度 0~2、值取 0~2 的有序链表（10 种）的所有组合，共 1111 组
    small = [list(c) for k in range(3) for c in itertools.combinations_with_replacement(range(3), k)]
    for k in range(4):
        for combo in itertools.product(small, repeat=k):
            cases.append((f"穷举 {list(combo)}", [list(g) for g in combo]))

    rng = random.Random(23)
    for i in range(100):  # 随机：0~50 条，每条 0~20 个节点
        groups = [sorted(rng.randint(-10000, 10000) for _ in range(rng.randint(0, 20)))
                  for _ in range(rng.randint(0, 50))]
        cases.append((f"随机 #{i}", groups))

    # 自动测试文件里所有以 Solution 开头的类
    classes = [obj for name, obj in list(globals().items()) if name.startswith("Solution") and isinstance(obj, type)]

    for cls in classes:
        for name, groups in cases:
            check(cls, name, groups)

    # 性能：只测 Solution，总节点数上限 10^4、k 上限 10^4。本地实测（1 万条单节点 / 100 条各 100 个 / 1 条 1 万个）：
    #   堆 3.5 / 2.4 / 1.1 ms，两两分治合并 10.7 / 4.6 / 0.0 ms，全部节点放进 list 排序再重连 1.6 / 1.2 / 0.8 ms；
    #   一条一条依次合并 O(kN)：1492 / 29 / 0.0 ms；每次扫 k 个头找最小 O(kN)：3593 / 52 / 1.8 ms。预算给 100 ms
    total = 10_000
    big = {
        "1 万条单节点": [[rng.randint(-10000, 10000)] for _ in range(total)],
        "100 条各 100 个": [sorted(rng.randint(-10000, 10000) for _ in range(100)) for _ in range(100)],
        "1 条 1 万个": [sorted(rng.randint(-10000, 10000) for _ in range(total))],
    }
    timings = []
    for name, groups in big.items():
        timings.append(check(Solution, f"性能：{name}", groups, seconds=0.1,
                             hint="可能是 O(kN)，例如每次都扫一遍 k 个头找最小，或者一条一条依次合并"))

    head_lists = [build(g)[0] for g in big["100 条各 100 个"]]
    tracemalloc.start()
    Solution().mergeKLists(head_lists)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组用例; 性能 "
          f"{' / '.join(f'{t * 1000:.1f}' for t in timings)} ms; 100 条各 100 个时额外内存峰值 {peak / 1024:.1f} KB)")
    if changed_input:
        print(f"注意：{', '.join(sorted(changed_input))} 调用后传进来的 lists 被改了（里面的头被换掉），LeetCode 不检查，但调用方会受影响")
    if new_nodes:
        print(f"注意：{', '.join(sorted(new_nodes))} 返回的是新建的节点，LeetCode 不检查，但额外空间是 O(N)")
    if rewrote_vals:
        print(f"注意：{', '.join(sorted(rewrote_vals))} 改了原节点的 val，LeetCode 不检查")
