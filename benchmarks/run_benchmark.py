import os
import subprocess
import time

# Configuration
HOST = "http://localhost:8000"
SCENARIOS = [
    {"users": 10, "spawn_rate": 1, "duration": "30s", "desc": "Warmup & Baseline"},
    {"users": 100, "spawn_rate": 10, "duration": "1m", "desc": "Load Test (100 concurrent)"},
    {"users": 1000, "spawn_rate": 100, "duration": "1m", "desc": "Stress Test (1000 concurrent)"},
]


def run_locust(users, spawn_rate, duration, headless=True):
    cmd = [
        "poetry",
        "run",
        "locust",
        "--headless" if headless else "",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "-t",
        duration,
        "--host",
        HOST,
        "--csv",
        f"benchmarks/results_{users}u",
        "--only-summary",
    ]
    # Filter out empty strings
    cmd = [c for c in cmd if c]

    print(f"--> Running: {users} Users, {spawn_rate}/s Spawn Rate for {duration}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running locust: {e.stderr}")
        return None


def main():
    print("==================================================")
    print("🚀 Starting Automated Benchmark Suite")
    print(f"Target: {HOST}")
    print("==================================================\n")

    for scenario in SCENARIOS:
        print(f"🔹 Scenario: {scenario['desc']}")
        run_locust(scenario["users"], scenario["spawn_rate"], scenario["duration"])

        # Read the generated CSV to show a quick summary
        csv_path = f"benchmarks/results_{scenario['users']}u_stats.csv"
        if os.path.exists(csv_path):
            with open(csv_path, "r") as _:
                # header = f.readline().strip()
                # data = f.readline().strip()  # Total line is usually last or first?
                # Locust CSV format: Method, Name, requests, failures, Median, Average, Min, Max, Content Size, reqs/sec
                # Actually typically the last line is the Aggregated one if usually
                # Let's just print the file path for now
                print(f"✅ Results saved to: {csv_path}")

        print("\n⏳ Cooling down for 5 seconds...\n")
        time.sleep(5)

    print("==================================================")
    print("🎉 Benchmark Suite Completed!")
    print("Check the 'benchmarks/' directory for detailed CSV reports.")
    print("==================================================")


if __name__ == "__main__":
    main()
