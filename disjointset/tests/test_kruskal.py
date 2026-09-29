"""Tests for the graph package and Kruskal's algorithm."""

from __future__ import annotations

import itertools
import random

import pytest

from graph import Edge, Graph, kruskal


def _total(edges):
    return sum(e.weight for e in edges)


def test_add_edge_adds_vertices():
    g = Graph()
    g.add_edge("A", "B", 3)
    assert g.vertices == {"A", "B"}
    assert list(g.edges()) == [Edge(3, "A", "B")]


def test_empty_graph():
    assert kruskal(Graph()) == []


def test_single_vertex():
    g = Graph()
    g.add_vertex("A")
    assert kruskal(g) == []


def test_small_graph():
    g = Graph()
    g.add_edge("A", "B", 4)
    g.add_edge("A", "C", 1)
    g.add_edge("B", "C", 2)
    g.add_edge("B", "D", 5)
    g.add_edge("C", "D", 8)
    mst = kruskal(g)
    assert len(mst) == len(g) - 1
    assert _total(mst) == 8
    assert {frozenset((e.u, e.v)) for e in mst} == {
        frozenset("AC"), frozenset("BC"), frozenset("BD")
    }


def test_disconnected_graph_gives_forest():
    g = Graph()
    g.add_edge(1, 2, 1)
    g.add_edge(2, 3, 2)
    g.add_edge(1, 3, 3)
    g.add_edge(4, 5, 7)
    g.add_vertex(6)
    mst = kruskal(g)
    assert len(mst) == 3  # 6 vertices, 3 components -> 6 - 3 edges
    assert _total(mst) == 10


def test_self_loop_and_parallel_edges_ignored():
    g = Graph()
    g.add_edge("A", "A", 0)
    g.add_edge("A", "B", 5)
    g.add_edge("A", "B", 2)
    assert kruskal(g) == [Edge(2, "A", "B")]


def test_equal_weights_with_uncomparable_vertices():
    # Sorting only on weight means vertex types need not be comparable.
    g = Graph()
    g.add_edge("A", 1, 1)
    g.add_edge(1, (2, 3), 1)
    assert len(kruskal(g)) == 2


# --- minimum spanning tree properties ----------------------------------------
# These helpers deliberately avoid UnionFind so they check kruskal independently.


def _components(vertices, edges):
    """Return the connected components as a list of sets, using DFS."""
    adj = {v: [] for v in vertices}
    for e in edges:
        adj[e.u].append(e.v)
        adj[e.v].append(e.u)
    seen, comps = set(), []
    for start in vertices:
        if start in seen:
            continue
        comp, stack = set(), [start]
        while stack:
            v = stack.pop()
            if v not in comp:
                comp.add(v)
                stack.extend(adj[v])
        seen |= comp
        comps.append(comp)
    return comps


def _is_spanning_tree(vertices, edges):
    """V-1 edges that connect every vertex form a tree (no room for a cycle)."""
    return len(edges) == len(vertices) - 1 and len(_components(vertices, edges)) == 1


def _brute_force_mst_weight(g):
    """Weight of the lightest spanning tree, found by trying every edge subset."""
    edges = list(g.edges())
    n = len(g)
    return min(
        _total(subset)
        for subset in itertools.combinations(edges, n - 1)
        if _is_spanning_tree(g.vertices, subset)
    )


def _random_connected_graph(rng, n, extra_edges, max_weight=10):
    g = Graph()
    # A random spanning path guarantees connectivity; extra edges add cycles.
    order = list(range(n))
    rng.shuffle(order)
    for a, b in zip(order, order[1:]):
        g.add_edge(a, b, rng.randint(1, max_weight))
    for _ in range(extra_edges):
        a, b = rng.sample(range(n), 2)
        g.add_edge(a, b, rng.randint(1, max_weight))
    return g


def test_textbook_example():
    # Classic 9-vertex example from CLRS "Introduction to Algorithms"; MST weight 37.
    g = Graph()
    for u, v, w in [
        ("a", "b", 4), ("a", "h", 8), ("b", "c", 8), ("b", "h", 11),
        ("c", "d", 7), ("c", "f", 4), ("c", "i", 2), ("d", "e", 9),
        ("d", "f", 14), ("e", "f", 10), ("f", "g", 2), ("g", "h", 1),
        ("g", "i", 6), ("h", "i", 7),
    ]:
        g.add_edge(u, v, w)
    mst = kruskal(g)
    assert _is_spanning_tree(g.vertices, mst)
    assert _total(mst) == 37


def test_mst_edges_come_from_graph():
    rng = random.Random(0)
    g = _random_connected_graph(rng, n=8, extra_edges=10)
    graph_edges = list(g.edges())
    for e in kruskal(g):
        assert e in graph_edges


def test_tree_graph_is_its_own_mst():
    g = Graph()
    for u, v, w in [(0, 1, 9), (1, 2, 1), (1, 3, 5), (3, 4, 2)]:
        g.add_edge(u, v, w)
    assert sorted(kruskal(g)) == sorted(g.edges())


def test_negative_and_float_weights():
    g = Graph()
    g.add_edge("A", "B", -3.5)
    g.add_edge("B", "C", 0.25)
    g.add_edge("A", "C", -1.0)
    mst = kruskal(g)
    assert _is_spanning_tree(g.vertices, mst)
    assert _total(mst) == pytest.approx(-4.5)


def test_complete_graph_equal_weights():
    # Every spanning tree is minimal; just check a valid one comes back.
    g = Graph()
    for a, b in itertools.combinations(range(6), 2):
        g.add_edge(a, b, 1)
    mst = kruskal(g)
    assert _is_spanning_tree(g.vertices, mst)
    assert _total(mst) == 5


def test_mst_forest_spans_each_component():
    g = Graph()
    g.add_edge(1, 2, 4)
    g.add_edge(2, 3, 1)
    g.add_edge(1, 3, 2)
    g.add_edge(10, 11, 3)
    g.add_edge(11, 12, 3)
    g.add_edge(10, 12, 1)
    mst = kruskal(g)
    comps = _components(g.vertices, mst)
    assert sorted(map(sorted, comps)) == [[1, 2, 3], [10, 11, 12]]
    assert len(mst) == len(g) - len(comps)
    assert _total(mst) == 3 + 4


@pytest.mark.parametrize("seed", range(25))
def test_randomized_against_brute_force(seed):
    rng = random.Random(seed)
    n = rng.randint(2, 6)
    g = _random_connected_graph(rng, n, extra_edges=rng.randint(0, 6))
    mst = kruskal(g)
    assert _is_spanning_tree(g.vertices, mst)
    assert _total(mst) == _brute_force_mst_weight(g)


# --- bulk loading -------------------------------------------------------------


def test_bulk_add_vertices_from_list():
    g = Graph()
    g.bulk_add_vertices(["A", "B", "C"])
    assert g.vertices == {"A", "B", "C"}
    assert len(g) == 3
    assert list(g.edges()) == []


def test_bulk_add_vertices_from_generator():
    g = Graph()
    g.bulk_add_vertices(i for i in range(5))
    assert g.vertices == set(range(5))


def test_bulk_add_vertices_ignores_duplicates():
    g = Graph()
    g.add_vertex("A")
    g.bulk_add_vertices(["A", "B", "B"])
    assert g.vertices == {"A", "B"}
    assert len(g) == 2


def test_bulk_add_vertices_empty():
    g = Graph()
    g.bulk_add_vertices([])
    assert len(g) == 0


def test_bulk_add_vertices_keeps_existing_edges():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.bulk_add_vertices(["C", "D"])
    assert g.vertices == {"A", "B", "C", "D"}
    assert list(g.edges()) == [Edge(1, "A", "B")]


def test_bulk_vertices_are_isolated_in_mst():
    g = Graph()
    g.bulk_add_vertices(range(4))
    g.add_edge(0, 1, 2)
    mst = kruskal(g)
    assert mst == [Edge(2, 0, 1)]
    assert len(_components(g.vertices, mst)) == 3  # {0,1}, {2}, {3}


def test_bulk_add_edges_from_list():
    edges = [Edge(4, "A", "B"), Edge(1, "A", "C"), Edge(2, "B", "C")]
    g = Graph()
    g.bulk_add_edges(edges)
    assert list(g.edges()) == edges  # insertion order preserved
    assert g.vertices == {"A", "B", "C"}


def test_bulk_add_edges_from_generator():
    g = Graph()
    g.bulk_add_edges(Edge(i, i, i + 1) for i in range(5))
    assert len(list(g.edges())) == 5
    assert g.vertices == set(range(6))


def test_bulk_add_edges_empty():
    g = Graph()
    g.bulk_add_edges([])
    assert len(g) == 0
    assert list(g.edges()) == []


def test_bulk_add_edges_keeps_parallel_edges():
    g = Graph()
    g.bulk_add_edges([Edge(5, "A", "B"), Edge(2, "A", "B")])
    assert len(list(g.edges())) == 2
    assert kruskal(g) == [Edge(2, "A", "B")]


def test_bulk_add_edges_appends_to_existing():
    g = Graph()
    g.add_edge("A", "B", 1)
    g.bulk_add_edges([Edge(2, "B", "C")])
    assert list(g.edges()) == [Edge(1, "A", "B"), Edge(2, "B", "C")]
    assert g.vertices == {"A", "B", "C"}


def test_bulk_add_edges_accepts_edges_from_another_graph():
    src = _random_connected_graph(random.Random(1), n=6, extra_edges=5)
    g = Graph()
    g.bulk_add_edges(src.edges())
    assert list(g.edges()) == list(src.edges())
    assert g.vertices == src.vertices


@pytest.mark.parametrize("seed", range(10))
def test_bulk_loaded_graph_matches_incremental(seed):
    rng = random.Random(seed)
    src = _random_connected_graph(rng, n=6, extra_edges=6)
    edges = list(src.edges())

    incremental = Graph()
    for e in edges:
        incremental.add_edge(e.u, e.v, e.weight)

    bulk = Graph()
    bulk.bulk_add_edges(edges)

    assert bulk.vertices == incremental.vertices
    assert list(bulk.edges()) == list(incremental.edges())
    assert kruskal(bulk) == kruskal(incremental)
    assert _total(kruskal(bulk)) == _brute_force_mst_weight(bulk)


def test_bulk_load_vertices_and_edges_together():
    g = Graph()
    g.bulk_add_vertices("ABCDE")
    g.bulk_add_edges([
        Edge(4, "A", "B"), Edge(1, "A", "C"), Edge(2, "B", "C"),
        Edge(5, "B", "D"), Edge(8, "C", "D"),
    ])
    mst = kruskal(g)
    assert len(g) == 5
    assert _total(mst) == 8
    assert len(_components(g.vertices, mst)) == 2  # E stays isolated
