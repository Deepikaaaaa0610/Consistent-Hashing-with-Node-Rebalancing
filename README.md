# 1. Consistent Hashing with Node Rebalancing

---

# 2. Overview

This project implements a **Consistent Hashing mechanism** with support for:

* Virtual Nodes (vnodes)
* Deterministic key lookup
* Efficient node rebalancing

The goal is to design a scalable and fault-tolerant key-to-node mapping strategy that minimizes key movement when nodes are added or removed.

The system does **not** store actual data. It only computes:

```
key → responsible physical node
```

---

# 3. Problem Background

Traditional partitioning uses:

```
hash(key) % N
```

This approach fails when `N` changes.

## 3.1 Why Modulo Hashing Fails

When a node is added or removed:

1. The divisor `N` changes
2. Almost all keys get remapped
3. Cache invalidation occurs
4. Massive data migration is triggered

This leads to downtime and instability.

---

# 4. How Consistent Hashing Solves the Problem

Consistent hashing:

1. Maps both keys and nodes onto a circular hash ring
2. Assigns keys to the next clockwise node
3. Ensures only local key ranges change during topology updates

Result: **Minimal disruption during node changes**

---

# 5. Architecture

The repository is divided into four modules:

```
hash_function.py
hash_ring.py
rebalancer.py
main.py
```

---

# 6. Module Breakdown

---

## 6.1 hash_function.py

Defines the deterministic hashing strategy.

### Features:

* Uses SHA-1 hashing
* Truncates to 32-bit unsigned integer
* Produces values in range 0 → 2³²−1
* Guarantees same input always maps to same output

This provides a stable coordinate system for the ring.

---

## 6.2 hash_ring.py

Implements the core consistent hashing data structure.

### Includes:

* Physical Node abstraction
* Virtual Node abstraction
* Sorted circular hash ring
* Node addition logic
* Node removal logic
* Clockwise successor lookup

### Data Structures Used:

* Sorted list of vnode positions
* Dictionary mapping position → vnode
* Dictionary mapping node → list of its vnode positions

### Time Complexity:

* Lookup: **O(log V)**
* Node add/remove: **O(V)** worst case (due to list insertion)
  Acceptable for assignment scale.

---

## 6.3 rebalancer.py

Provides analysis and validation utilities.

### Implements:

* Key mapping snapshot generation
* Key movement percentage calculation
* Load distribution statistics
* Variance and standard deviation analysis
* Observability logging

### Used to Demonstrate:

* Minimal key movement on node changes
* Improved load balance with virtual nodes

---

## 6.4 main.py

Entry point for experiments.

### Executes:

1. Initial ring creation
2. Key distribution measurement
3. Node addition scenario
4. Node removal scenario
5. Virtual node comparison (K = 1 vs K = 50 vs K = 200)

This file validates correctness and generates output logs.

---

# 7. Hash Ring Model

* Ring space: 0 → 2³²−1
* Both keys and virtual nodes are hashed into this space

### Ownership Rule

A key belongs to the first vnode clockwise from its hash position.

If no vnode exists clockwise, lookup wraps to ring start.

---

# 8. Virtual Nodes

Each physical node is assigned **K virtual nodes**.

## 8.1 Why Virtual Nodes Are Needed

### Without Virtual Nodes:

* Node positions are uneven
* Some nodes get large hash ranges
* Load variance is high

### With Virtual Nodes:

* Each node owns multiple smaller segments
* Distribution becomes statistically uniform
* Variance decreases significantly

### Expected Behavior

As `K` increases → load variance decreases.

---

# 9. Rebalancing Logic

---

## 9.1 Node Addition

When adding node X:

Only keys in intervals between:

```
predecessor vnode → X vnode
```

are reassigned.

All other keys remain untouched.

### Expected Moved Fraction

```
≈ 1 / (total_nodes_after_addition)
```

---

## 9.2 Node Removal

When removing a node:

* Only keys owned by that node move
* They are reassigned to immediate successors
* No global reshuffle occurs

---

# 10. Determinism

The system is fully deterministic:

* Same key always maps to same node
* Given same topology, lookup results are identical
* No randomness in routing decisions

---

# 11. Non-Functional Guarantees

| Aspect        | Guarantee                                  |
| ------------- | ------------------------------------------ |
| Determinism   | Same inputs → same outputs                 |
| Stability     | Minimal remapping                          |
| Scalability   | Supports 10–10,000 nodes                   |
| Extensibility | Replication layer can be added later       |
| Observability | Key movement & distribution metrics logged |

---

# 12. Running the Project

```
python main.py
```

This will:

1. Run experiment without virtual nodes
2. Run experiment with virtual nodes
3. Compare load balance across different vnode counts

---

# 13. Example Output Observations

* With K = 1
  Load variance is high

* With K = 200
  Load variance significantly decreases

* On node addition
  Key movement approaches ~ 1/(N+1)

* On node removal
  Only keys of removed node move

---

# 14. Why Consistent Hashing Works

Instead of partitioning by modulo:

* The keyspace is circular
* Nodes own ranges between predecessor and self
* Adding a node splits only specific ranges
* Removing a node merges only specific ranges

This ensures minimal disruption.

---

# 15. Trade-offs

## Pros

* Minimal remapping
* Deterministic routing
* Uniform distribution with vnodes
* No central coordinator required

## Cons

* Higher memory usage due to vnodes
* Insert/remove cost higher than modulo hashing
* Requires maintaining sorted structure

---

# 16. Conclusion

This implementation demonstrates:

* Correct ring construction
* Deterministic lookup
* Minimal key movement
* Efficient rebalancing
* Clear impact of virtual nodes on load balance

The design is modular, extensible, and follows separation of concerns principles.
