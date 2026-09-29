"""Kruskal's minimum spanning tree algorithm."""

from __future__ import annotations

from disjointset import UnionFind

from .graph import Edge, Graph


def kruskal(graph: Graph) -> list[Edge]:
    """Return the edges of a minimum spanning tree.

    If the graph is disconnected, returns a minimum spanning forest
    (fewer than V-1 edges, one tree per connected component).
    """
    disjoint_set = UnionFind(graph.vertices)
    minimum_spanning_tree: list[Edge] = []
    target = len(graph) - 1
    
    for edge in sorted(graph.edges(), key=lambda e: e.weight):
        if len(minimum_spanning_tree) == target:
            break
        if disjoint_set.union(edge.u, edge.v):
            minimum_spanning_tree.append(edge)
            
    return minimum_spanning_tree
        

    
