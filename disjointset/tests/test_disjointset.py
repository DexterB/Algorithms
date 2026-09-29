"""Contract tests for DisjointSet implementations.

Add further implementations to IMPLEMENTATIONS to run the same suite against them.
"""

from __future__ import annotations

import random

import pytest

from disjointset import DisjointSet, UnionFind

IMPLEMENTATIONS: list[type[DisjointSet]] = [UnionFind]


@pytest.fixture(params=IMPLEMENTATIONS, ids=lambda cls: cls.__name__)
def ds_cls(request) -> type[DisjointSet]:
    return request.param


@pytest.fixture
def ds(ds_cls) -> DisjointSet:
    return ds_cls()


# --- interface --------------------------------------------------------------


def test_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        DisjointSet()  # type: ignore[abstract]


def test_implementation_is_a_disjoint_set(ds):
    assert isinstance(ds, DisjointSet)


# --- empty / construction ---------------------------------------------------


def test_empty(ds):
    assert len(ds) == 0
    assert ds.set_count == 0
    assert "a" not in ds
    assert ds.groups() == []


def test_constructor_with_items(ds_cls):
    ds = ds_cls([1, 2, 3])
    assert len(ds) == 3
    assert ds.set_count == 3
    for x in (1, 2, 3):
        assert x in ds
        assert ds.find(x) == x
        assert ds.set_size(x) == 1


def test_constructor_ignores_duplicates(ds_cls):
    ds = ds_cls([1, 1, 2, 2, 2])
    assert len(ds) == 2
    assert ds.set_count == 2


def test_constructor_accepts_generator(ds_cls):
    ds = ds_cls(i for i in range(5))
    assert len(ds) == 5


# --- make_set ---------------------------------------------------------------


def test_make_set_creates_singleton(ds):
    ds.make_set("a")
    assert "a" in ds
    assert ds.find("a") == "a"
    assert ds.set_size("a") == 1
    assert len(ds) == 1
    assert ds.set_count == 1


def test_make_set_duplicate_raises(ds):
    ds.make_set("a")
    with pytest.raises(ValueError):
        ds.make_set("a")
    assert len(ds) == 1
    assert ds.set_count == 1


def test_make_set_duplicate_after_union_raises(ds):
    ds.make_set("a")
    ds.make_set("b")
    ds.union("a", "b")
    with pytest.raises(ValueError):
        ds.make_set("b")
    assert ds.connected("a", "b")


@pytest.mark.parametrize("item", [0, -1, "", "x", (1, 2), frozenset({1}), None, 3.5])
def test_make_set_various_hashable_types(ds, item):
    ds.make_set(item)
    assert item in ds
    assert ds.find(item) == item


def test_contains_missing_item(ds):
    ds.make_set(1)
    assert 2 not in ds


# --- missing items ----------------------------------------------------------


def test_find_missing_raises_keyerror(ds):
    with pytest.raises(KeyError):
        ds.find("missing")


def test_set_size_missing_raises_keyerror(ds):
    with pytest.raises(KeyError):
        ds.set_size("missing")


@pytest.mark.parametrize("a,b", [("x", "missing"), ("missing", "x"), ("m1", "m2")])
def test_union_missing_raises_keyerror(ds, a, b):
    ds.make_set("x")
    with pytest.raises(KeyError):
        ds.union(a, b)


@pytest.mark.parametrize("a,b", [("x", "missing"), ("missing", "x")])
def test_connected_missing_raises_keyerror(ds, a, b):
    ds.make_set("x")
    with pytest.raises(KeyError):
        ds.connected(a, b)


def test_failed_union_leaves_state_unchanged(ds):
    ds.make_set("x")
    with pytest.raises(KeyError):
        ds.union("x", "missing")
    assert "missing" not in ds
    assert len(ds) == 1
    assert ds.set_count == 1


# --- union / find / connected -----------------------------------------------


def test_union_merges_two_sets(ds_cls):
    ds = ds_cls(["a", "b"])
    assert ds.union("a", "b") is True
    assert ds.connected("a", "b")
    assert ds.find("a") == ds.find("b")
    assert ds.find("a") in {"a", "b"}
    assert ds.set_count == 1
    assert ds.set_size("a") == ds.set_size("b") == 2
    assert len(ds) == 2


def test_union_same_set_returns_false(ds_cls):
    ds = ds_cls(["a", "b"])
    ds.union("a", "b")
    assert ds.union("a", "b") is False
    assert ds.union("b", "a") is False
    assert ds.set_count == 1
    assert ds.set_size("a") == 2


def test_union_with_self_returns_false(ds_cls):
    ds = ds_cls(["a"])
    assert ds.union("a", "a") is False
    assert ds.set_count == 1
    assert ds.set_size("a") == 1


def test_connected_is_reflexive(ds_cls):
    ds = ds_cls(["a"])
    assert ds.connected("a", "a")


def test_not_connected_initially(ds_cls):
    ds = ds_cls(["a", "b"])
    assert not ds.connected("a", "b")
    assert not ds.connected("b", "a")


def test_connectivity_is_transitive(ds_cls):
    ds = ds_cls("abcd")
    ds.union("a", "b")
    ds.union("b", "c")
    assert ds.connected("a", "c")
    assert ds.connected("c", "a")
    assert not ds.connected("a", "d")
    assert ds.set_count == 2
    assert ds.set_size("c") == 3
    assert ds.set_size("d") == 1


def test_union_of_two_multi_element_sets(ds_cls):
    ds = ds_cls(range(6))
    ds.union(0, 1)
    ds.union(1, 2)
    ds.union(3, 4)
    ds.union(4, 5)
    assert ds.set_count == 2
    assert not ds.connected(0, 5)
    assert ds.union(2, 3) is True
    assert ds.set_count == 1
    assert all(ds.connected(0, i) for i in range(6))
    assert all(ds.set_size(i) == 6 for i in range(6))


def test_representative_is_a_member(ds_cls):
    ds = ds_cls(range(10))
    for i in range(0, 10, 2):
        ds.union(i, i + 1)
    for i in range(10):
        rep = ds.find(i)
        assert rep in ds
        assert ds.connected(i, rep)


def test_representative_is_stable_without_unions(ds_cls):
    ds = ds_cls(range(5))
    ds.union(0, 1)
    ds.union(1, 2)
    rep = ds.find(0)
    for _ in range(3):
        assert ds.find(0) == ds.find(1) == ds.find(2) == rep


def test_find_is_idempotent_on_representative(ds_cls):
    ds = ds_cls(range(4))
    ds.union(0, 1)
    ds.union(2, 3)
    ds.union(0, 3)
    rep = ds.find(2)
    assert ds.find(rep) == rep


def test_make_set_after_unions(ds_cls):
    ds = ds_cls(["a", "b"])
    ds.union("a", "b")
    ds.make_set("c")
    assert ds.set_count == 2
    assert len(ds) == 3
    assert not ds.connected("a", "c")
    ds.union("c", "a")
    assert ds.set_count == 1
    assert ds.set_size("b") == 3


def test_distinct_sets_have_distinct_representatives(ds_cls):
    ds = ds_cls(range(9))
    for a, b in [(0, 1), (1, 2), (3, 4), (5, 6), (6, 7), (7, 8)]:
        ds.union(a, b)
    reps = {ds.find(i) for i in range(9)}
    assert len(reps) == ds.set_count == 3


def test_items_equal_by_value_are_same_item(ds):
    ds.make_set((1, 2))
    assert (1, 2) in ds
    with pytest.raises(ValueError):
        ds.make_set((1, 2))


def test_1_and_true_are_same_key(ds):
    # Python treats 1 == True with equal hashes, so they are the same item.
    ds.make_set(1)
    assert True in ds
    with pytest.raises(ValueError):
        ds.make_set(True)


# --- groups -----------------------------------------------------------------


def _normalize(groups):
    return sorted(sorted(g) for g in groups)


def test_groups_singletons(ds_cls):
    ds = ds_cls([1, 2, 3])
    assert _normalize(ds.groups()) == [[1], [2], [3]]


def test_groups_after_unions(ds_cls):
    ds = ds_cls(range(7))
    ds.union(0, 1)
    ds.union(2, 3)
    ds.union(3, 4)
    ds.union(0, 6)
    assert _normalize(ds.groups()) == [[0, 1, 6], [2, 3, 4], [5]]


def test_groups_consistent_with_counts(ds_cls):
    ds = ds_cls(range(20))
    for a, b in [(0, 5), (5, 10), (1, 2), (3, 19), (19, 7)]:
        ds.union(a, b)
    groups = ds.groups()
    assert len(groups) == ds.set_count
    assert sum(len(g) for g in groups) == len(ds)
    for g in groups:
        for x in g:
            assert ds.set_size(x) == len(g)


# --- independence -----------------------------------------------------------


def test_instances_do_not_share_state(ds_cls):
    a = ds_cls([1, 2])
    b = ds_cls([1, 2])
    a.union(1, 2)
    assert a.connected(1, 2)
    assert not b.connected(1, 2)
    assert "x" not in b
    a.make_set("x")
    assert "x" not in b


def test_default_constructor_does_not_share_state(ds_cls):
    a = ds_cls()
    b = ds_cls()
    a.make_set(1)
    assert 1 not in b


# --- larger / randomized ----------------------------------------------------


def test_long_chain(ds_cls):
    n = 10_000
    ds = ds_cls(range(n))
    for i in range(n - 1):
        ds.union(i, i + 1)
    assert ds.set_count == 1
    assert ds.set_size(0) == n
    assert ds.connected(0, n - 1)


def test_long_chain_reverse_order(ds_cls):
    n = 10_000
    ds = ds_cls(range(n))
    for i in range(n - 1, 0, -1):
        ds.union(i, i - 1)
    assert ds.set_count == 1
    assert ds.connected(0, n - 1)


class _NaiveDisjointSet:
    """Obviously-correct O(n) reference model for randomized comparison."""

    def __init__(self, items):
        self.label = {x: x for x in items}

    def union(self, a, b):
        la, lb = self.label[a], self.label[b]
        if la == lb:
            return False
        for k, v in self.label.items():
            if v == lb:
                self.label[k] = la
        return True

    def connected(self, a, b):
        return self.label[a] == self.label[b]

    def set_size(self, a):
        la = self.label[a]
        return sum(1 for v in self.label.values() if v == la)

    @property
    def set_count(self):
        return len(set(self.label.values()))


@pytest.mark.parametrize("seed", range(10))
def test_randomized_against_reference(ds_cls, seed):
    rng = random.Random(seed)
    n = 200
    ds = ds_cls(range(n))
    ref = _NaiveDisjointSet(range(n))

    for _ in range(500):
        a, b = rng.randrange(n), rng.randrange(n)
        op = rng.random()
        if op < 0.4:
            assert ds.union(a, b) == ref.union(a, b)
        elif op < 0.8:
            assert ds.connected(a, b) == ref.connected(a, b)
        else:
            assert ds.set_size(a) == ref.set_size(a)
        assert ds.set_count == ref.set_count

    assert len(ds) == n
    assert _normalize(ds.groups()) == _normalize(
        {x for x in range(n) if ref.label[x] == lbl} for lbl in set(ref.label.values())
    )
