# Create a Custom exception for the analyser pool
class AnalyserPoolException(Exception):
    """No more objects in pool"""
    pass


class Reusable:
    def test(self):
        print(f"Using object {id(self)}")


class ReusablePool:
    def __init__(self, size=5):
        self._available_pool = []
        self.in_use = []
        self._size = size
        self._current = 0
        for _ in range(size):
            self.add(Reusable())

    def acquire(self) -> Reusable:
        if len(self._available_pool) <= 0:
            raise AnalyserPoolException("No more objects in pool")
        r = self._available_pool[0]
        self._available_pool.remove(r)
        self.in_use.append(r)
        return r

    def release(self, item: Reusable):
        self._available_pool.append(item)
        self.in_use.remove(item)

    def __call__(self):
        if self._current >= self._size:
            return None
        self._current += 1
        return self._available_pool[self._current - 1]

    def add(self, item):
        self._available_pool.append(item)

    def reset(self):
        self._current = 0


def __main():
    pool = ReusablePool(2)
    r = pool.acquire()
    r2 = pool.acquire()
    r3 = pool.acquire()
    r.test()
    r2.test()


if __name__ == "__main__":
    __main()
