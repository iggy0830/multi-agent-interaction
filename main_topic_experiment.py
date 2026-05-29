# main_topic_experiment.py

import argparse
import json
import os
import re

from agent_topic import Agent
from moderator import Moderator
from topics import TOPIC_CONFIGS


def get_next_output_dir(base_dir="results"):
    os.makedirs(base_dir, exist_ok=True)

    existing = []
    for name in os.listdir(base_dir):
        if re.fullmatch(r"\d+\.0", name):
            existing.append(int(name.split(".")[0]))

    next_num = max(existing, default=0) + 1
    output_dir = os.path.join(base_dir, f"{next_num}.0")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def build_agents_from_config(topic_config: dict):
    topic_label = topic_config["topic"]
    theme_keywords = topic_config.get("theme_keywords", [])

    agents = []
    for agent_cfg in topic_config["agents"]:
        agents.append(
            Agent(
                name=agent_cfg["name"],
                persona=agent_cfg["persona"],
                initial_belief=agent_cfg["initial_belief"],
                initial_goal=agent_cfg["initial_goal"],
                topic_label=topic_label,
                stance_target=topic_label,
                theme_keywords=theme_keywords,
            )
        )
    return agents


def save_trial_json(trial_id: int, topic: str, agents: list[Agent], moderator_summaries: list[dict], output_dir: str) -> None:
    trial_data = {
        "trial_id": trial_id,
        "topic": topic,
        "moderator_summaries": moderator_summaries,
        "agents": []
    }

    for agent in agents:
        trial_data["agents"].append({
            "name": agent.name,
            "persona": agent.persona,
            "initial_belief": agent.initial_belief,
            "final_belief": agent.current_belief,
            "final_goal": agent.current_goal,
            "stance_history": agent.stance_history,
            "traces": agent.round_traces,
            "memories": [str(m) for m in agent.memory_stream.get_all()]
        })

    with open(os.path.join(output_dir, f"trial_{trial_id}.json"), "w", encoding="utf-8") as f:
        json.dump(trial_data, f, indent=2, ensure_ascii=False)


def save_trial_summary(trial_id: int, topic: str, agents: list[Agent], moderator_summaries: list[dict], output_dir: str) -> None:
    with open(os.path.join(output_dir, f"trial_{trial_id}_summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"TRIAL {trial_id}\n")
        f.write(f"Topic: {topic}\n\n")

        f.write("Moderator summaries:\n")
        for item in moderator_summaries:
            f.write(f"  Round {item['round']}: {item['summary']}\n")
        f.write("\n")

        for agent in agents:
            f.write(f"Agent: {agent.name}\n")
            f.write(f"Persona: {agent.persona}\n")
            f.write(f"Initial belief: {agent.initial_belief}\n")
            f.write(f"Final belief: {agent.current_belief}\n")
            f.write(f"Final goal: {agent.current_goal}\n")
            f.write(f"Stance history: {' -> '.join(agent.stance_history)}\n")
            f.write("Round traces:\n")

            for trace in agent.round_traces:
                f.write(f"  Round {trace['round']}\n")
                f.write(f"    Retrieved memories: {trace['selected_memories']}\n")
                f.write(f"    Observation: {trace['observation_summary']}\n")
                f.write(f"    Thought: {trace['thought']}\n")
                f.write(f"    Influence: {trace['influence_analysis']}\n")
                f.write(f"    Updated belief: {trace['updated_belief']}\n")
                f.write(f"    Updated goal: {trace['updated_goal']}\n")
                f.write(f"    Stance: {trace['stance']}\n")
                f.write(f"    Message: {trace['message']}\n")
                f.write(f"    Moderator summary: {trace.get('moderator_summary', '')}\n")
                f.write(f"    Post-moderator response: {trace.get('post_moderator_response', '')}\n")
                f.write(f"    Post-moderator agreement analysis: {trace.get('post_moderator_agreement_analysis', '')}\n")
                f.write(f"    Post-moderator belief: {trace.get('post_moderator_belief', '')}\n")
                f.write(f"    Post-moderator goal: {trace.get('post_moderator_goal', '')}\n")
                f.write(f"    Next strategy: {trace.get('next_strategy', '')}\n")
            f.write("\n")


def save_overall_summary(all_agents_by_trial: list[list[Agent]], num_trials: int, rounds: int, topic_name: str, output_dir: str) -> None:
    with open(os.path.join(output_dir, "overall_summary.txt"), "w", encoding="utf-8") as f:
        f.write("Overall Experiment Summary\n")
        f.write("==========================\n\n")
        f.write(f"Topic name: {topic_name}\n")
        f.write(f"Total trials: {num_trials}\n")
        f.write(f"Rounds per trial: {rounds}\n\n")

        for i, agents in enumerate(all_agents_by_trial, start=1):
            f.write(f"Trial {i}\n")
            for agent in agents:
                f.write(
                    f"  {agent.name}\n"
                    f"    Final belief: {agent.current_belief}\n"
                    f"    Final goal: {agent.current_goal}\n"
                    f"    Stance history: {' -> '.join(agent.stance_history)}\n"
                )
            f.write("\n")


def run_one_simulation(trial_id: int, topic_name: str, topic_config: dict, output_dir: str, rounds: int = 5):
    topic = topic_config["topic"]
    agents = build_agents_from_config(topic_config)
    moderator = Moderator()
    moderator_summaries = []

    print("\n==============================")
    print(f"TRIAL {trial_id}")
    print(f"Topic name: {topic_name}")
    print(f"Topic: {topic}")
    print("==============================\n")

    previous_round_messages = {}

    for round_id in range(1, rounds + 1):
        print(f"===== Round {round_id} =====")
        current_round_messages = {}

        for speaker in agents:
            message = speaker.speak(topic, current_round=round_id, previous_round_messages=previous_round_messages)
            current_round_messages[speaker.name] = message
            trace = speaker.round_traces[-1]

            print(f"\n{speaker.name}")
            print(f"Belief: {trace['updated_belief']}")
            print(f"Goal: {trace['updated_goal']}")
            print(f"Observation: {trace['observation_summary']}")
            print(f"Thought: {trace['thought']}")
            print(f"Influence: {trace['influence_analysis']}")
            print(f"Message: {message}")

            for listener in agents:
                if listener.name != speaker.name:
                    listener.observe(speaker.name, message, round_id)

        print("\n--- Reflections after this round ---")
        for agent in agents:
            reflection = agent.reflect(current_round=round_id)
            print(f"{agent.name}: {reflection}")

        summary = moderator.summarize_round(
            topic=topic,
            round_id=round_id,
            current_round_messages=current_round_messages,
        )
        moderator_summaries.append({"round": round_id, "summary": summary})

        print("\n--- Moderator summary ---")
        print(summary)

        print("\n--- Updates after moderator summary ---")
        for agent in agents:
            agent.observe_moderator_summary(summary, round_id)
            update_data = agent.update_from_moderator_summary(topic, round_id, summary)
            print(f"{agent.name}:")
            print(f"  Updated belief: {update_data['updated_belief']}")
            print(f"  Updated goal: {update_data['updated_goal']}")
            print(f"  Updated stance target: {update_data['updated_stance']}")
            print(f"  Next strategy: {update_data['next_strategy']}")

        previous_round_messages = current_round_messages
        print()

    print("===== Final Stance Evolution =====")
    for agent in agents:
        history = " → ".join(agent.stance_history) if agent.stance_history else "No stance recorded"
        print(f"{agent.name}: {history}")

    print("\n===== Final Beliefs =====")
    for agent in agents:
        print(f"{agent.name}: {agent.current_belief}")

    print("\n===== Final Goals =====")
    for agent in agents:
        print(f"{agent.name}: {agent.current_goal}")

    save_trial_json(trial_id, topic, agents, moderator_summaries, output_dir)
    save_trial_summary(trial_id, topic, agents, moderator_summaries, output_dir)

    return agents


def run_experiments(topic_name: str, num_trials: int = 5, rounds: int = 5, output_dir: str = "results/1.0"):
    if topic_name not in TOPIC_CONFIGS:
        raise ValueError(f"Unknown topic_name: {topic_name}")

    topic_config = TOPIC_CONFIGS[topic_name]
    all_agents_by_trial = []

    for trial_id in range(1, num_trials + 1):
        agents = run_one_simulation(
            trial_id=trial_id,
            topic_name=topic_name,
            topic_config=topic_config,
            output_dir=output_dir,
            rounds=rounds,
        )
        all_agents_by_trial.append(agents)

    save_overall_summary(all_agents_by_trial, num_trials, rounds, topic_name, output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--topic_name",
        type=str,
        default="autonomous_vehicles",
        help="Topic key from TOPIC_CONFIGS"
    )
    parser.add_argument("--num_trials", type=int, default=5)
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()

    output_dir = get_next_output_dir("results")
    print(f"Saving results to: {output_dir}")
    print(f"Using topic_name: {args.topic_name}")

    run_experiments(
        topic_name=args.topic_name,
        num_trials=args.num_trials,
        rounds=args.rounds,
        output_dir=output_dir
    )


if __name__ == "__main__":
    main()