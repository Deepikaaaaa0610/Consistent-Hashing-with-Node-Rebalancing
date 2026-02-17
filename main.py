from __future__ import annotations

import random
from typing import List, Optional

from hash_ring import HashRing, Node
from rebalancer import Rebalancer


def generate_keys(n: int, seed: int = 42) -> List[str]:
    rng = random.Random(seed)
    return [f"user:{rng.getrandbits(64):016x}" for _ in range(n)]


def run_experiment(
    num_keys: int = 200_000,
    initial_nodes: int = 5,
    vnodes_per_node: int = 1,
    add_node_id: str = "node_new",
    remove_node_id: Optional[str] = None,
    seed: int = 42,
) -> None:
    keys = generate_keys(num_keys, seed=seed)

    ring = HashRing(vnodes_per_node=vnodes_per_node)
    reb = Rebalancer(ring)

    for i in range(initial_nodes):
        ring.add_node(Node(f"node_{i}"))

    reb.print_topology("Initial Ring", ring)
    before = reb.map_keys(keys)
    reb.print_distribution("Key distribution BEFORE change", before)

    ring.add_node(Node(add_node_id))
    reb.print_topology("After ADD", ring)
    after_add = reb.map_keys(keys)
    reb.print_distribution("Key distribution AFTER add", after_add)

    moved, total, pct = reb.moved_key_stats(before, after_add)
    exp = 100.0 * reb.expected_move_fraction_add(initial_nodes + 1)
    print(f"\nRebalance (ADD): moved={moved}/{total} ({pct:.2f}%). Expected ~ {exp:.2f}%")

    if remove_node_id is not None:
        before_remove = after_add
        ring.remove_node(remove_node_id)
        reb.print_topology(f"After REMOVE {remove_node_id}", ring)
        after_remove = reb.map_keys(keys)
        reb.print_distribution("Key distribution AFTER remove", after_remove)

        moved2, total2, pct2 = reb.moved_key_stats(before_remove, after_remove)
        print(f"\nRebalance (REMOVE): moved={moved2}/{total2} ({pct2:.2f}%).")


def compare_vnodes_effect(num_keys: int = 200_000, nodes: int = 10, seed: int = 42) -> None:
    keys = generate_keys(num_keys, seed=seed)

    for k in [1, 50, 200]:
        ring = HashRing(vnodes_per_node=k)
        for i in range(nodes):
            ring.add_node(Node(f"node_{i}"))

        reb = Rebalancer(ring)
        mapping = reb.map_keys(keys)
        reb.print_topology(f"VNode Comparison (K={k})", ring)
        reb.print_distribution(f"Distribution with K={k}", mapping)


if __name__ == "__main__":
    # 1) Movement on add/remove with no vnodes
    run_experiment(
        num_keys=200_000,
        initial_nodes=5,
        vnodes_per_node=1,
        add_node_id="node_5",
        remove_node_id="node_2",
        seed=42,
    )

    # 2) Same, with vnodes (better load balance)
    run_experiment(
        num_keys=200_000,
        initial_nodes=5,
        vnodes_per_node=200,
        add_node_id="node_5",
        remove_node_id="node_2",
        seed=42,
    )

    # 3) Load-balance comparison across vnode counts
    compare_vnodes_effect(num_keys=200_000, nodes=10, seed=42)
