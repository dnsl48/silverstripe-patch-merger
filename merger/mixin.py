import functools

@functools.total_ordering
class ComparableMixin:
    def __eq__(self, other):
        return self._cmpkey() == other._cmpkey()

    def __le__(self, other):
        return self._cmpkey() < other._cmpkey()