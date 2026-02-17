from __future__ import annotations

from collections import Counter
import statistics
from typing import Dict, Iterable, Tuple

from hash_ring import HashRing


class Rebalancer:
    """
    Metrics + mapping utilities:
    - map_keys: compute key -> node_id mapping
    - moved_key_stats: moved count and percent between two mappings
    - distribution_stats: mean/variance/stdev/min/max for per-node loads
    - logs: topology + distribution prints
    """

    def __init__(self, ring: HashRing):
        self.ring = ring

    def map_keys(self, keys: Iterable[str]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for k in keys:
            out[k] = self.ring.get_node_for_key(k).node_id
        return out

    @staticmethod
    def moved_key_stats(before: Dict[str, str], after: Dict[str, str]) -> Tuple[int, int, float]:
        if before.keys() != after.keys():
            raise ValueError("Key sets differ; cannot compare movement")

        total = len(before)
        moved = sum(1 for k in before if before[k] != after[k])
        pct = (moved / total * 100.0) if total else 0.0
        return moved, total, pct

    @staticmethod
    def distribution_stats(mapping: Dict[str, str]) -> Dict[str, float]:
        counts = Counter(mapping.values())
        values = list(counts.values())

        if not values:
            return {
                "nodes": 0.0,
                "keys": 0.0,
                "mean": 0.0,
                "variance": 0.0,
                "stdev": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        mean = statistics.mean(values)
        variance = statistics.pvariance(values)
        stdev = statistics.pstdev(values)

        return {
            "nodes": float(len(values)),
            "keys": float(sum(values)),
            "mean": float(mean),
            "variance": float(variance),
            "stdev": float(stdev),
            "min": float(min(values)),
            "max": float(max(values)),
        }

    @staticmethod
    def expected_move_fraction_add(total_nodes_after: int) -> float:
        if total_nodes_after <= 0:
            return 0.0
        return 1.0 / total_nodes_after

    @staticmethod
    def print_topology(title: str, ring: HashRing) -> None:
        print(f"\n=== {title} ===")
        print(f"Physical nodes: {len(ring)} | Total vnodes: {ring.total_vnodes()} | K={ring.vnodes_per_node}")
        print("Nodes:", ", ".join(ring.list_nodes()))

    @staticmethod
    def print_distribution(title: str, mapping: Dict[str, str]) -> None:
        stats = Rebalancer.distribution_stats(mapping)
        print(f"\n--- {title} ---")
        print(
            "keys={keys:.0f} nodes={nodes:.0f} mean={mean:.2f} "
            "min={min:.0f} max={max:.0f} variance={variance:.2f} stdev={stdev:.2f}".format(**stats)
        )
