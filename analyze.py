import json
import glob
import os
import re
import matplotlib.pyplot as plt
from matplotlib_venn import venn2

# This file analyzes the latest saved simulation results.
# It reads trial JSON files from the newest results/x.0 folder and saves:
#   - venn_diagram.png
#   - stance_evolution.png
# back into that same folder.

KEY_THEMES = [
    "critical thinking", "over-rely", "dependency", "misuse", "fairness",
    "creativity", "personalize", "personalized", "guidelines", "boundaries",
    "responsibility", "responsible", "access", "equity", "engagement",
    "brainstorm", "research", "feedback", "learning", "harm",
    "benefits", "risks", "moderation", "integrity", "shortcuts",
    "skills", "independent", "reliance", "support", "adoption"
]


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


def load_trial(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_themes(text: str) -> set:
    text = text.lower()
    found = set()
    for theme in KEY_THEMES:
        if theme in text:
            found.add(theme)
    return found


def get_trial_themes(trial: dict) -> set:
    themes = set()

    for agent in trial.get("agents", []):
        for trace in agent.get("traces", []):
            for field in [
                "observation_summary",
                "thought",
                "influence_analysis",
                "updated_belief",
                "updated_goal",
                "message",
                "moderator_summary",
                "post_moderator_response",
                "post_moderator_agreement_analysis",
                "post_moderator_belief",
                "post_moderator_goal",
                "next_strategy",
            ]:
                if field in trace and isinstance(trace[field], str):
                    themes |= extract_themes(trace[field])

        if isinstance(agent.get("final_belief"), str):
            themes |= extract_themes(agent["final_belief"])

        for mem in agent.get("memories", []):
            if isinstance(mem, str):
                themes |= extract_themes(mem)

    for item in trial.get("moderator_summaries", []):
        if isinstance(item, dict) and isinstance(item.get("summary"), str):
            themes |= extract_themes(item["summary"])

    return themes


def get_trial_stances(trial: dict) -> dict:
    return {
        agent["name"]: agent.get("stance_history", [])
        for agent in trial.get("agents", [])
    }


def print_venn_sets(sets: list[set], labels: list[str]):
    if not sets:
        print("No theme sets found.")
        return

    all_themes = set().union(*sets)
    shared_all = sets[0].copy()
    for s in sets[1:]:
        shared_all &= s

    unique = [
        s - set().union(*[sets[j] for j in range(len(sets)) if j != i])
        for i, s in enumerate(sets)
    ]

    print("\n=== Theme Analysis Across Trials ===")
    print(f"\nShared across ALL {len(sets)} trials:")
    for t in sorted(shared_all):
        print(f"  • {t}")

    for i, label in enumerate(labels):
        print(f"\nUnique to {label}:")
        for t in sorted(unique[i]):
            print(f"  • {t}")

    print(f"\nAll themes observed (any trial): {sorted(all_themes)}")


def plot_venn(sets: list[set], labels: list[str], title: str, output_dir: str):
    if len(sets) < 2:
        print("Not enough trials to draw venn_diagram.png")
        return

    fig, axes = plt.subplots(1, len(sets) - 1, figsize=(6 * (len(sets) - 1), 5))
    if len(sets) - 1 == 1:
        axes = [axes]

    for i in range(len(sets) - 1):
        ax = axes[i]
        a, b = sets[i], sets[i + 1]
        la, lb = labels[i], labels[i + 1]
        venn2([a, b], set_labels=(la, lb), ax=ax)
        ax.set_title(f"{la} vs {lb}")

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "venn_diagram.png"), dpi=150)
    print(f"Saved: {os.path.join(output_dir, 'venn_diagram.png')}")
    plt.close()


def plot_stance_evolution(all_stances: list[dict], trial_labels: list[str], output_dir: str):
    if not all_stances:
        print("No stance data found.")
        return

    agents = list(all_stances[0].keys())
    stance_to_num = {"supportive": 1, "balanced": 0, "skeptical": -1}
    colors = {"Alice": "#4C9BE8", "Bob": "#E85C5C", "Carol": "#6DBF6D", "David": "#F5A623"}

    max_rounds = 0
    for stances in all_stances:
        for history in stances.values():
            max_rounds = max(max_rounds, len(history))

    fig, axes = plt.subplots(1, len(agents), figsize=(4 * len(agents), 4), sharey=True)
    fig.suptitle("Stance Evolution per Agent Across Trials", fontsize=13, fontweight="bold")

    if len(agents) == 1:
        axes = [axes]

    for ax, agent in zip(axes, agents):
        for i, (stances, label) in enumerate(zip(all_stances, trial_labels)):
            history = stances.get(agent, [])
            nums = [stance_to_num.get(s, 0) for s in history]
            rounds = list(range(1, len(nums) + 1))

            ax.plot(
                rounds,
                nums,
                marker="o",
                label=label,
                alpha=0.7,
                color=plt.cm.tab10(i / max(1, len(trial_labels)))
            )

        ax.set_title(agent, color=colors.get(agent, "black"), fontweight="bold")
        ax.set_yticks([-1, 0, 1])
        ax.set_yticklabels(["skeptical", "balanced", "supportive"])
        ax.set_xlabel("Round")
        ax.set_xticks(range(1, max_rounds + 1))
        ax.set_xlim(0.8, max_rounds + 0.2)
        ax.grid(True, alpha=0.3)

    axes[-1].legend(title="Trial", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "stance_evolution.png"), dpi=150)
    print(f"Saved: {os.path.join(output_dir, 'stance_evolution.png')}")
    plt.close()


def main():
    output_dir = get_latest_output_dir("results")
    if output_dir is None:
        print("No results folder found. Run main.py first.")
        return

    paths = sorted(
        p for p in glob.glob(os.path.join(output_dir, "trial_*.json"))
        if re.fullmatch(r".*/trial_\d+\.json", p)
    )

    if not paths:
        print("No numeric trial files found in latest results folder.")
        return

    trials = [load_trial(p) for p in paths]
    labels = [f"Trial {t['trial_id']}" for t in trials]
    theme_sets = [get_trial_themes(t) for t in trials]
    all_stances = [get_trial_stances(t) for t in trials]

    print(f"Reading trials from: {output_dir}")
    print_venn_sets(theme_sets, labels)
    plot_venn(theme_sets[:3], labels[:3], "Discussion Themes: Trial Comparison", output_dir)
    plot_stance_evolution(all_stances, labels, output_dir)


if __name__ == "__main__":
    main()