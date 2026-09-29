"""Your implementation of the DisjointSet interface.

Suggested approach: dict-based parent pointers with path compression in
`find` and union by size (or rank) in `union`, giving near-O(1) amortized
operations.

Run the tests with:  pytest -q
"""

from __future__ import annotations

from collections.abc import Iterable

from .base import DisjointSet, T


class UnionFind(DisjointSet[T]):
    def __init__(self, items: Iterable[T] = ()) -> None:
        # Initialise your internal state here (e.g. parent / size dicts)
        self.parent: dict[T, T] = {}
        self.rank: dict[T, int]= {}
        
        super().__init__(items)
        for item in items:
            if item not in self.parent:
             self.make_set(item)


    def make_set(self, item: T) -> None:
        if item in self.parent:
            raise ValueError(f"{item} is already in the disjoint set")
        self.parent[item] = item
        self.rank[item] = 0

    def find(self, item: T) -> T:
        if not item in self.parent:
            raise KeyError(f"{item} is not in the disjoint set")
        
        root = item
        path = []
        while root != self.parent[root]:
            path.append(root)
            root = self.parent[root]

        for node in path:
            self.parent[node] = root

        return root

    def union(self, item_a: T, item_b: T) -> bool:
        root_a = self.find(item_a)
        root_b = self.find(item_b)
        
        if root_a == root_b:
            return False

        if self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
            for item in [x for x in self.parent if self.parent[x] == root_b]:
                self.parent[item] = root_a
        else:
            self.parent[root_a] = root_b
            for item in [x for x in self.parent if self.parent[x] == root_b]:
                self.parent[item] = root_b
            if root_a == root_b:
                self.rank[root_b] += 1
                
        return True

    def set_size(self, item: T) -> int:
        root = self.find(item)
        return len([k for k in self.parent if self.find(k) == root])

    @property
    def set_count(self) -> int:
        return len([item for item in self.parent if item == self.parent[item]])

    def __len__(self) -> int:
        return len(self.parent)

    def __contains__(self, item: object) -> bool:
        return item in self.parent

    def _items(self) -> Iterable[T]:
        return [item for item in self.parent]
