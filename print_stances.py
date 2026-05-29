import json
import glob
import os
import re


def get_latest_output_dir(base_dir="results"):
    if not os.path.exists(base_dir):
        return None

    existing = []
    for name in os.listdir(base_dir):
        if re.fullmatch(r"\d+\.0", name):
            existing.append(int(name.split(".")[0]))

    if not existing:
        return None

    latest_num = max(existing)
    return os.path.join(base_dir, f"{latest_num}.0")


def load_trial(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    output_dir = get_latest_output_dir("results")
    if output_dir is None:
        print("No results folder found.")
        return

    paths = sorted(
        p for p in glob.glob(os.path.join(output_dir, "trial_*.json"))
        if re.fullmatch(r".*/trial_\d+\.json", p)
    )

    if not paths:
        print("No trial files found.")
        return

    print(f"Reading from: {output_dir}")

    for path in paths:
        trial = load_trial(path)
        trial_id = trial.get("trial_id", os.path.basename(path).replace(".json", ""))

        print(f"\nTRIAL {trial_id}")
        for agent in trial.get("agents", []):
            name = agent.get("name", "Unknown")
            history = agent.get("stance_history", [])
            print(f"{name}: {' -> '.join(history)}")


if __name__ == "__main__":
    main()