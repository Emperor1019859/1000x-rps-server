# Benchmarks & Monitoring

## 🚀 Automated Benchmark Suite
We provide a script to automatically run 10, 100, and 1000 user scenarios.

### Usage
```bash
python benchmarks/run_benchmark.py
```
This will:
1. Run a 10-user warmup test (30s).
2. Run a 100-user load test (1m).
3. Run a 1000-user stress test (1m).
4. Save CSV reports to this directory (`benchmarks/results_*.csv`).

## 📊 Real-time Dashboard (Grafana)
Access the dashboard at: http://localhost:3000

### Known Issues
**Missing CPU/Memory on macOS:**
If you are running Docker Desktop on macOS, the CPU and Memory panels in Grafana might be empty. This is a known limitation of `cAdvisor` on macOS, as it cannot access the virtual machine's cgroups to map container names to resource usage reliably.

**Workaround:**
To monitor resource usage on macOS, use the native Docker stats command:
```bash
docker stats
```
On Linux production environments, the Grafana dashboard will work as expected.
