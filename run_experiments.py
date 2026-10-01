"""
Runs repeated trials of the agent under different configurations and
records results to CSV. The part that actually invokes the agent is a
placeholder until the local model is set up — this file is for testing
the recording/CSV logic first, with dummy data.
"""

import csv
import os

import config

RESULTS_DIR = "results"


def run_single_trial(run_number, defence_enabled):
    """Run one trial and report what happened.

    PLACEHOLDER: does not call agent.py yet. Once the model is set up,
    this should:
      1. set config.DEFENCE_ENABLED = defence_enabled
      2. run the agent on the attack scenario (page including
         ev_battery_costs.html)
      3. check attacker_log.txt / attacker's response for whether the
         leak happened
      4. check whether save_summary was reached normally
    For now it returns dummy data so the CSV-writing logic can be tested
    on its own.
    """
    # --- PLACEHOLDER: replace with a real agent.py run ---
    violation_detected = not defence_enabled  # dummy: "attack succeeds" when defence is off
    summary_completed = True
    # --- end placeholder ---

    return {
        "run_number": run_number,
        "defence_enabled": defence_enabled,
        "violation_detected": violation_detected,
        "summary_completed": summary_completed,
    }


def run_trials(num_trials, defence_enabled, output_path):
    """Run num_trials trials under one configuration and write results to a CSV."""
    os.makedirs(RESULTS_DIR, exist_ok=True)

    fieldnames = ["run_number", "defence_enabled", "violation_detected", "summary_completed"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for run_number in range(1, num_trials + 1):
            result = run_single_trial(run_number, defence_enabled)
            writer.writerow(result)
            print(f"Run {run_number}: {result}")


def main():
    # No-defence trials -> results/attack_results.csv
    run_trials(
        num_trials=10,
        defence_enabled=False,
        output_path=os.path.join(RESULTS_DIR, "attack_results.csv"),
    )

    # Defence-enabled trials -> results/defence_results.csv
    run_trials(
        num_trials=10,
        defence_enabled=True,
        output_path=os.path.join(RESULTS_DIR, "defence_results.csv"),
    )


if __name__ == "__main__":
    main()
