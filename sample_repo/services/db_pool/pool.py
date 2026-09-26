MAX_CONNECTIONS = 20


def get_connection():
    """Borrow a pooled Postgres connection; blocks when the pool is exhausted."""
    return _pool.acquire(timeout=5)


class _Pool:
    def acquire(self, timeout):
        raise NotImplementedError


_pool = _Pool()
