"""Undirected weighted graph stored as an edge list."""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Iterator
from typing import NamedTuple


class Edge(NamedTuple):
    """An undirected weighted edge. Weight comes first so edges sort by weight."""

    weight: float
    u: Hashable
    v: Hashable


class Graph:
    def __init__(self) -> None:
        self._vertices: set[Hashable] = set()
        self._edges: list[Edge] = []

    def add_vertex(self, v: Hashable) -> None:
        self._vertices.add(v)
        
    def bulk_add_vertices(self, vertices: Iterable[Hashable]) -> None:
        self._vertices.update(vertices)

    def add_edge(self, u: Hashable, v: Hashable, weight: float) -> None:
        """Add an undirected edge; its endpoints are added as vertices if new."""
        self._vertices.update((u, v))
        self._edges.append(Edge(weight, u, v))
        
    def bulk_add_edges(self, edges: Iterable[Edge]) -> None:
        for edge in edges:
            self.add_edge(edge.u, edge.v, edge.weight)

    @property
    def vertices(self) -> set[Hashable]:
        return set(self._vertices)

    def edges(self) -> Iterator[Edge]:
        return iter(self._edges)

    def __len__(self) -> int:
        """Number of vertices."""
        return len(self._vertices)
