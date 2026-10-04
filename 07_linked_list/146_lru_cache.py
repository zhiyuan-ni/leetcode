"""
Pattern: 哈希表 + 双向链表（设计题）

Core:
- 字典 key -> 节点，负责 O(1) 定位；双向链表按使用先后排队，head 一侧最近使用、tail 一侧最久未用，负责 O(1) 挪动和淘汰。
  两头各放一个哨兵，真实节点永远有前驱和后继，摘下、插入都不用判空。节点里存 key，淘汰时才能从字典里删掉。
- get：命中就挪到 head 后面再返回 val，否则 -1。put：已有 key 就改 val 并挪到前面（不淘汰）；新 key 在满时先淘汰 tail.prev，再插到前面。
- RemoveAdd: 所有指针只在 remove(node)（2 个）和 add_front(node)（4 个）里改，刷新、淘汰、放入都由它们组合。
- LRUCache: insert / evict / move_to_front 各自改指针，move_to_front 要改 6 个。

Time: get、put 均 O(1)
Space: O(capacity)
实测容量 3000、20 万次操作（随机 / 反复访问最近用过的 key）：LRUCache 68 / 72 ms，RemoveAdd 72 / 75 ms，
OrderedDict 35 / 34 ms，普通 dict（删掉再插回、next(iter(d)) 淘汰）87 / 36 ms；用 list 存使用顺序 452 / 2582 ms。

Mistake:
- 第一版 get 和 put 更新已有 key 都没有挪到最近那头，链表顺序只是放入的先后：示例第 4 步 get(2) 期望 -1 得到 2。
- 第二版 put_head 只改了 6 个指针中的 4 个：摘下时漏了 prev.next = next，插入时漏了 head.next.prev = node（要写在 head.next = node 之前）。
  get(1) 之后从头往后走成环 [1, 2, 1, 2, ...]，从尾往前只有 [2]；只有一个节点时 get 它，节点的 next 指向自己。用户随后自己补上。

易错点:
- 题目只要求 O(1)，不要求链表；但这题练的就是自己实现「字典 + 双向链表」，OrderedDict 底层就是这个结构。
- 更新已有 key 算一次使用，且不能触发淘汰；值可能为 0，判断 key 是否存在不能看值的真假。
- 状态要放在实例上（self.xxx），写成类属性会被所有实例共享。
"""


class ListNode:
    def __init__(self, key=0, val=0, prev=None, next=None):
        self.key = key
        self.val = val
        self.prev = prev
        self.next = next


class LRUCacheRemoveAdd:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.nodes = {}
        self.head = ListNode()
        self.tail = ListNode(prev=self.head)
        self.head.next = self.tail

    def get(self, key: int) -> int:
        if key not in self.nodes:
            return -1
        node = self.nodes[key]
        self.remove(node)
        self.add_front(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.nodes:
            node = self.nodes[key]
            node.val = value
            self.remove(node)
        else:
            if len(self.nodes) == self.capacity:
                lru = self.tail.prev
                self.remove(lru)
                del self.nodes[lru.key]
            node = ListNode(key, value)
            self.nodes[key] = node
        self.add_front(node)

    def remove(self, node: ListNode) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def add_front(self, node: ListNode) -> None:
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.nodes = {}
        self.head = ListNode()
        self.tail = ListNode(prev=self.head)
        self.head.next = self.tail

    def get(self, key: int) -> int:
        if key in self.nodes:
            self.move_to_front(self.nodes[key])
            return self.nodes[key].val
        else:
            return -1

    def put(self, key: int, value: int) -> None:
        if key in self.nodes:
            self.nodes[key].val = value
            self.move_to_front(self.nodes[key])
        else:
            if len(self.nodes) == self.capacity:
                self.evict()
            self.insert(key, value)

    def insert(self, key: int, value: int) -> None:
        node = ListNode(key, value, self.head, self.head.next)
        self.nodes[key] = node
        self.head.next.prev = node
        self.head.next = node

    def evict(self) -> None:
        lru = self.tail.prev
        prev = lru.prev
        prev.next = self.tail
        self.tail.prev = prev
        del self.nodes[lru.key]

    def move_to_front(self, node: ListNode) -> None:
        node.next.prev = node.prev
        node.prev.next = node.next
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node


if __name__ == "__main__":
    import itertools
    import random
    import signal
    import time

    class Timeout(Exception):
        pass

    def _on_alarm(signum, frame):
        raise Timeout

    signal.signal(signal.SIGALRM, _on_alarm)

    class Reference:
        """对拍用：按最近使用顺序存一个 key 列表，每次操作都线性查找。逻辑简单、慢，只用来算期望值。"""

        def __init__(self, capacity):
            self.capacity = capacity
            self.order = []   # 从最久未用到最近使用
            self.values = {}

        def get(self, key):
            if key not in self.values:
                return -1
            self.order.remove(key)
            self.order.append(key)
            return self.values[key]

        def put(self, key, value):
            if key in self.values:
                self.order.remove(key)
            elif len(self.order) == self.capacity:
                del self.values[self.order.pop(0)]
            self.order.append(key)
            self.values[key] = value

    def fmt(op):
        return f"get({op[1]})" if op[0] == "get" else f"put({op[1]}, {op[2]})"

    def run_ops(cls, name, capacity, ops, seconds=1.0):
        """逐个执行操作，每个 get 都和 Reference 对比；出错时显示最近几步操作。"""
        tag = f"{cls.__name__} {name}（capacity={capacity}）"
        ref = Reference(capacity)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        try:
            cache = cls(capacity)
            for step, op in enumerate(ops):
                history = ", ".join(fmt(o) for o in ops[max(0, step - 6):step])
                where = f"第 {step} 步 {fmt(op)}（前面几步：{history or '无'}）"
                try:
                    if op[0] == "get":
                        got, want = cache.get(op[1]), ref.get(op[1])
                        assert got == want and type(got) is int, (
                            f"{tag}，{where}：期望 {want}，得到 {got!r}；此时缓存里应是（从最久未用到最近使用）"
                            f"{[(k, ref.values[k]) for k in ref.order]}")
                    else:
                        got = cache.put(op[1], op[2])
                        ref.put(op[1], op[2])
                        assert got is None, f"{tag}，{where}：put 应返回 None，得到 {got!r}"
                except AssertionError:
                    raise
                except Timeout:
                    raise
                except Exception as e:
                    raise AssertionError(f"{tag}，{where}：抛出 {type(e).__name__}: {e}") from e
        except Timeout:
            raise AssertionError(f"{tag}，超过 {seconds}s 被中断，可能死循环或单次操作不是 O(1)") from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)

    def parse(capacity, commands, args):
        """把 LeetCode 的输入格式转成操作列表。"""
        ops = []
        for c, a in zip(commands[1:], args[1:]):
            ops.append(("get", a[0]) if c == "get" else ("put", a[0], a[1]))
        return capacity, ops

    cases = [
        # 题目示例
        ("题目示例", *parse(2, ["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"],
                             [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]])),
        # 容量 1：每次放新 key 都要淘汰
        ("容量 1", 1, [("put", 1, 1), ("get", 1), ("put", 2, 2), ("get", 1), ("get", 2)]),
        # get 不存在的 key
        ("空缓存 get", 2, [("get", 1)]),
        # 更新已有 key：值要变，且算一次「使用」，不能触发淘汰
        ("更新已有 key 不淘汰", 2, [("put", 1, 1), ("put", 2, 2), ("put", 1, 10), ("get", 1), ("get", 2)]),
        ("更新后刷新最近使用", 2, [("put", 1, 1), ("put", 2, 2), ("put", 1, 10), ("put", 3, 3),
                                   ("get", 1), ("get", 2), ("get", 3)]),
        # get 也算一次「使用」
        ("get 刷新最近使用", 2, [("put", 1, 1), ("put", 2, 2), ("get", 1), ("put", 3, 3),
                                 ("get", 1), ("get", 2), ("get", 3)]),
        # 反复 put 同一个 key
        ("同一个 key 反复 put", 2, [("put", 1, 1), ("put", 1, 2), ("put", 1, 3), ("put", 2, 2),
                                   ("get", 1), ("get", 2)]),
        # 被淘汰后再放回来
        ("淘汰后重新放入", 1, [("put", 1, 1), ("put", 2, 2), ("put", 1, 3), ("get", 2), ("get", 1)]),
        # 值为 0：不能用「值为真」判断 key 是否存在
        ("值为 0", 2, [("put", 1, 0), ("get", 1), ("put", 2, 0), ("put", 3, 3), ("get", 1), ("get", 2)]),
        # key 为 0
        ("key 为 0", 2, [("put", 0, 5), ("get", 0), ("put", 1, 1), ("put", 2, 2), ("get", 0)]),
    ]

    # 穷举：容量 1~3，key 只有 0~2，长度 0~5 的所有操作序列（get 三种 + put 三种），共 3 x 9331 组。
    # put 的值用步数，保证每次写入的值都不同，读到旧值能被发现
    alphabet = [("get", k) for k in range(3)] + [("put", k) for k in range(3)]
    for capacity in range(1, 4):
        for length in range(6):
            for seq in itertools.product(alphabet, repeat=length):
                ops = [op if op[0] == "get" else (op[0], op[1], step + 1) for step, op in enumerate(seq)]
                cases.append((f"穷举 {[fmt(o) for o in ops]}", capacity, ops))

    rng = random.Random(146)
    for i in range(200):  # 随机：长一点的序列，key 空间比容量大一些，淘汰频繁
        capacity = rng.randint(1, 20)
        ops = [("get", rng.randint(0, 30)) if rng.random() < 0.5 else ("put", rng.randint(0, 30), rng.randint(0, 100000))
               for _ in range(500)]
        cases.append((f"随机 #{i}", capacity, ops))

    # 自动测试文件里所有以 LRUCache 开头的类（设计题的类名由题目给定，备选实现命名为 LRUCache<Approach>）
    classes = [obj for name, obj in list(globals().items()) if name.startswith("LRUCache") and isinstance(obj, type)]

    # 先跑题目示例确认基本功能，再查两个实例互不影响：状态如果写成类属性，会被所有实例共享，
    # 后面的用例也会互相污染、报在不相干的地方
    for cls in classes:
        run_ops(cls, *cases[0])
        a, b = cls(2), cls(2)
        a.put(1, 1)
        assert b.get(1) == -1, f"{cls.__name__}：a.put(1, 1) 之后，另一个实例 b.get(1) 应为 -1，得到 {b.get(1)}——状态写成了类属性？"

    for cls in classes:
        for name, capacity, ops in cases:
            run_ops(cls, name, capacity, ops)

    # 性能：只测 LRUCache，题目上限：容量 3000，2 * 10^5 次操作，key 0~10^4。
    # 计时时不能每步都和 Reference 对拍（它每步 O(容量)，自己就会超时），所以先用 OrderedDict 算出所有 get 的期望值，
    # 再只给被测类计时，最后统一比对。本地实测（随机操作 / 反复访问最近用过的 key）：
    #   字典 + 双向链表 67 / 64 ms，OrderedDict 34 / 33 ms；
    #   用 list 存使用顺序、每次 remove 再 append（每步 O(容量)）：452 / 2582 ms。预算给 300 ms
    from collections import OrderedDict

    def expected_gets(capacity, ops):
        d = OrderedDict()
        out = []
        for op in ops:
            if op[0] == "get":
                if op[1] in d:
                    d.move_to_end(op[1])
                    out.append(d[op[1]])
                else:
                    out.append(-1)
            else:
                if op[1] in d:
                    d.move_to_end(op[1])
                d[op[1]] = op[2]
                if len(d) > capacity:
                    d.popitem(last=False)
        return out

    capacity = 3000
    workloads = {
        "随机操作": [("get", rng.randint(0, 10000)) if rng.random() < 0.5
                     else ("put", rng.randint(0, 10000), rng.randint(0, 100000)) for _ in range(200_000)],
        # 先放满，再反复读写最近用过的那个 key：按使用顺序存 list 时，它在末尾，每次 remove 都要从头扫到尾
        "反复访问最近用过的 key": [("put", k, k) for k in range(capacity)]
                                  + [("get", capacity - 1) if i % 2 else ("put", capacity - 1, i)
                                     for i in range(200_000 - capacity)],
    }
    timings = []
    for name, ops in workloads.items():
        want = expected_gets(capacity, ops)
        got = []
        signal.setitimer(signal.ITIMER_REAL, 0.3)
        try:
            start = time.perf_counter()
            cache = LRUCache(capacity)
            for op in ops:
                if op[0] == "get":
                    got.append(cache.get(op[1]))
                else:
                    cache.put(op[1], op[2])
            timings.append(time.perf_counter() - start)
        except Timeout:
            raise AssertionError(f"LRUCache 性能：{name}，超过 0.3s 被中断，单次操作可能不是 O(1)（例如在 list 里 remove）") from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if got != want:
            i = next(i for i, (x, y) in enumerate(zip(got, want)) if x != y)
            raise AssertionError(f"LRUCache 性能：{name}，第 {i} 个 get 期望 {want[i]}，得到 {got[i]}")

    print(f"ok ({', '.join(c.__name__ for c in classes)}; {len(cases)} 组操作序列; 20 万次操作 "
          f"{' / '.join(f'{t * 1000:.0f}' for t in timings)} ms)")
