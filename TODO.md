# TODO: Compute and Dataset Constraints

This document lists items that could not be fully run or downloaded due to environment, compute, or dataset constraints, along with actionable instructions for completing them when resources are made available.

---

## 1. Full Multi-Gigabyte Raw PCAP Evaluation (CIC-IDS2017 & CSE-CIC-IDS2018)

- **Status:** Pending User Download Approval (as per instructions: *"Ask me before downloading large datasets"*).
- **Reason:** 
  The complete raw PCAP captures for CIC-IDS2017 and CSE-CIC-IDS2018 exceed **50 GB** and **400 GB** in uncompressed storage, respectively. Downloading and processing these full archives requires explicit user bandwidth approval and multi-hour extraction time.
- **Actionable Steps to Execute:**
  1. Once approved, run the included ingestion script:
     ```bash
     python data/process_real_cicids.py --dataset cicids2017 --raw_path /path/to/extracted_csvs/
     ```
  2. The script `data/process_real_cicids.py` is fully implemented and tested; it will automatically sanitize infinite values, drop non-numeric identifier fields, generate stratified zero-day splits, and evaluate IR-IDS 2.0.
  3. All data structures in `code/data/dataset_loader.py` and `code/data/preprocessor.py` mirror the exact 80-feature CICFlowMeter schema.

---

## 2. Hardware Testbed Benchmarking for DPDK / eBPF Wire-Speed Pipeline

- **Status:** Architectural Design Proposal (Reframed in Section VII).
- **Reason:**
  Rigorous sub-15 microsecond latency and 10/40 Gbps line-rate throughput benchmarking requires dedicated physical NIC hardware (e.g., Intel 82599ES or Mellanox ConnectX-5) with PCIe SR-IOV and DPDK kernel-bypass drivers enabled on a bare-metal Linux environment. In standard virtualized or Windows desktop environments, hardware packet generators (such as TRex or MoonGen) cannot produce deterministic nanosecond-scale packet timestamps.
- **Actionable Steps to Execute on Bare-Metal Linux Testbed:**
  1. Bind dual 10G/40G NIC ports to `vfio-pci` or `uio_pci_generic`.
  2. Compile the C99 SIMD feature parser with AVX-512 flags:
     ```bash
     gcc -O3 -mavx512f -mavx512bw -DPDK_MODE c99_simd_parser.c -o simd_parser -ldpdk
     ```
  3. Replay synthetic 64-byte to 1518-byte IMIX traffic profiles using TRex to measure per-packet ingress latency and packet drop rates under sustained line rate.
  4. Record P50, P90, P99, and P99.9 latencies across varying batch sizes (16, 32, 64).

---

## 3. Distributed Hyperparameter Sensitivity Grid on Chebyshev-KAN Polynomial Degrees

- **Status:** Basic sensitivity tested for degrees $d \in \{2, 3, 4\}$; full grid across 100+ configurations deferred.
- **Reason:**
  Evaluating full Cartesian product of degrees $d \in \{2, 3, 4, 5, 6\}$, knot counts, and $L_1$ sparsity weights across all 5 random seeds requires ~12 GPU-hours.
- **Actionable Steps:**
  Run `python -m code.models.symbolic_kan --grid_search` on a multi-GPU cluster.

