from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_left
from typing import Dict, List

from hash_function import HashFunction


@dataclass(frozen=True)
class Node:
    """
    Physical node identity. In real systems, this could be host:port or node_id.
    """
    node_id: str


@dataclass(frozen=True)
class VNode:
    """
    Virtual node identity: (physical node, vnode index).
    This is what actually gets placed on the ring.
    """
    physical: Node
    replica_index: int

    @property
    def vnode_key(self) -> str:
        return f"{self.physical.node_id}#vn{self.replica_index}"


class HashRing:
    """
    Maintains a sorted structure of (position -> vnode).
    Successor search: given key hash h, find first position >= h else wrap to 0.

    Data structures:
    - _positions: sorted list of int ring positions
    - _vnode_at: dict position -> VNode
    - _positions_by_node: dict node_id -> list of positions (for clean removal)
    """

    def __init__(self, vnodes_per_node: int = 100, hash_fn: HashFunction | None = None):
        if vnodes_per_node <= 0:
            raise ValueError("vnodes_per_node must be > 0")

        self.vnodes_per_node = vnodes_per_node
        self.hash_fn = hash_fn or HashFunction()

        self._positions: List[int] = []
        self._vnode_at: Dict[int, VNode] = {}
        self._positions_by_node: Dict[str, List[int]] = {}

    def add_node(self, node: Node) -> None:
        if node.node_id in self._positions_by_node:
            raise ValueError(f"Node {node.node_id} already exists in ring")

        pos_list: List[int] = []

        for i in range(self.vnodes_per_node):
            vnode = VNode(node, i)
            pos = self.hash_fn.hash32(vnode.vnode_key)

            # Extremely rare collision handling: deterministic probing
            attempt = 0
            while pos in self._vnode_at:
                attempt += 1
                pos = self.hash_fn.hash32(f"{vnode.vnode_key}@{attempt}")

            idx = bisect_left(self._positions, pos)
            self._positions.insert(idx, pos)
            self._vnode_at[pos] = vnode
            pos_list.append(pos)

        self._positions_by_node[node.node_id] = pos_list

    def remove_node(self, node_id: str) -> None:
        if node_id not in self._positions_by_node:
            raise ValueError(f"Node {node_id} not found in ring")

        for pos in self._positions_by_node[node_id]:
            self._vnode_at.pop(pos, None)

            idx = bisect_left(self._positions, pos)
            if idx >= len(self._positions) or self._positions[idx] != pos:
                raise RuntimeError("Ring corruption: position missing from sorted index")
            self._positions.pop(idx)

        del self._positions_by_node[node_id]

    def get_node_for_key(self, key: str) -> Node:
        if not self._positions:
            raise ValueError("Ring is empty")

        h = self.hash_fn.hash32(key)
        idx = bisect_left(self._positions, h)
        if idx == len(self._positions):
            idx = 0

        vnode = self._vnode_at[self._positions[idx]]
        return vnode.physical

    def list_nodes(self) -> List[str]:
        return sorted(self._positions_by_node.keys())

    def total_vnodes(self) -> int:
        return len(self._positions)

    def __len__(self) -> int:
        return len(self._positions_by_node)
