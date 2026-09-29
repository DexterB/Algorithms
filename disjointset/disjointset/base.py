"""Disjoint Set (Union-Find) data structure interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterable
from typing import Generic, TypeVar

T = TypeVar("T", bound=Hashable)


class DisjointSet(ABC, Generic[T]):
    """Interface for a disjoint-set (union-find) data structure.

    Contract:
      * Every item belongs to exactly one set.
      * Each set is identified by a representative, which is one of its members.
        The representative may change after a `union`, but two items are in the
        same set iff `find` returns the same representative for both.
      * Operations on an item that was never added raise `KeyError`.
    """

    def __init__(self, items: Iterable[T] = ()) -> None:
        """Create a structure where each item in `items` is its own singleton set.

        Duplicate items in `items` are ignored.
        """

    @abstractmethod
    def make_set(self, item: T) -> None:
        """Create a new singleton set containing only `item`.

        Raises:
            ValueError: if `item` is already present.
        """

    @abstractmethod
    def find(self, item: T) -> T:
        """Return the representative of the set containing `item`.

        Raises:
            KeyError: if `item` is not present.
        """

    @abstractmethod
    def union(self, item_a: T, item_b: T) -> bool:
        """Merge the sets containing `item_a` and `item_b`.

        Returns:
            True if two distinct sets were merged, False if they were already
            the same set.

        Raises:
            KeyError: if either item is not present.
        """

    @abstractmethod
    def set_size(self, item: T) -> int:
        """Return the number of items in the set containing `item`.

        Raises:
            KeyError: if `item` is not present.
        """

    @property
    @abstractmethod
    def set_count(self) -> int:
        """Number of disjoint sets currently tracked."""

    @abstractmethod
    def __len__(self) -> int:
        """Total number of items across all sets."""

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        """Return True if `item` has been added via `make_set`."""

    def connected(self, item_a: T, item_b: T) -> bool:
        """Return True if `item_a` and `item_b` are in the same set.

        Raises:
            KeyError: if either item is not present.
        """
        return self.find(item_a) == self.find(item_b)

    def groups(self) -> list[set[T]]:
        """Return all sets as a list of Python sets (order unspecified).

        The default implementation is O(n) calls to `find`; it relies on
        `_items()` which implementations must provide.
        """
        by_root: dict[T, set[T]] = {}
        for item in self._items():
            by_root.setdefault(self.find(item), set()).add(item)
        return list(by_root.values())

    @abstractmethod
    def _items(self) -> Iterable[T]:
        """Iterate over every item that has been added."""
