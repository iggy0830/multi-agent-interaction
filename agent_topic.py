# agent_topic.py

import json
from memory import MemoryItem, MemoryStream
from retriever_topic import MemoryRetriever
from reflector import Reflector
from llm import generate_response


class Agent:
    def __init__(
        self,
        name: str,
        persona: str,
        initial_belief: str,
        initial_goal: str,
        topic_label: str,
        stance_target: str,
        theme_keywords: list[str] | None = None
    ):
        self.name = name
        self.persona = persona
        self.initial_belief = initial_belief
        self.current_belief = initial_belief
        self.current_goal = initial_goal

        self.topic_label = topic_label
        self.stance_target = stance_target
        self.theme_keywords = theme_keywords or []

        self.memory_stream = MemoryStream()
        self.retriever = MemoryRetriever(extra_keywords=self.theme_keywords)
        self.reflector = Reflector()

        self.stance_history = []
        self.round_traces = []

        self.last_moderator_summary = ""
        self.last_consensus_strategy = ""

    def observe(self, speaker: str, message: str, round_id: int) -> None:
        short_message = self._extract_view(message)
        importance = self._estimate_importance(short_message)
        content = f"{speaker} said: {short_message}"

        if self._is_duplicate_memory(content):
            return

        memory = MemoryItem(
            content=content,
            speaker=speaker,
            importance=importance,
            memory_type="observation",
            round_id=round_id,
        )
        self.memory_stream.add_memory(memory)

    def observe_moderator_summary(self, summary: str, round_id: int) -> None:
        self.last_moderator_summary = summary

        content = f"Moderator summary: {summary}"
        if self._is_duplicate_memory(content):
            return

        memory = MemoryItem(
            content=content,
            speaker="Moderator",
            importance=8.0,
            memory_type="moderator_summary",
            round_id=round_id,
            metadata={"source": "round_summary"},
        )
        self.memory_stream.add_memory(memory)

    def update_from_moderator_summary(self, topic: str, round_id: int, summary: str) -> dict:
        update_data = self.reflector.reflect_on_summary(
            agent_name=self.name,
            persona=self.persona,
            current_belief=self.current_belief,
            current_goal=self.current_goal,
            topic=topic,
            moderator_summary=summary,
        )

        self.current_belief = update_data["updated_belief"]
        self.current_goal = update_data["updated_goal"]
        self.last_consensus_strategy = update_data["next_strategy"]

        self.memory_stream.add_memory(MemoryItem(
            content=update_data["summary_response"],
            speaker=self.name,
            importance=6.0,
            memory_type="moderator_update",
            round_id=round_id,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=update_data["agreement_analysis"],
            speaker=self.name,
            importance=6.0,
            memory_type="moderator_update",
            round_id=round_id,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=f"My belief after moderator summary: {update_data['updated_belief']}",
            speaker=self.name,
            importance=7.0,
            memory_type="belief_update",
            round_id=round_id,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=f"My goal after moderator summary: {update_data['updated_goal']}",
            speaker=self.name,
            importance=7.0,
            memory_type="goal_update",
            round_id=round_id,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=f"My next consensus strategy: {update_data['next_strategy']}",
            speaker=self.name,
            importance=7.0,
            memory_type="moderator_update",
            round_id=round_id,
        ))

        if self.round_traces and self.round_traces[-1]["round"] == round_id:
            self.round_traces[-1]["moderator_summary"] = summary
            self.round_traces[-1]["post_moderator_response"] = update_data["summary_response"]
            self.round_traces[-1]["post_moderator_agreement_analysis"] = update_data["agreement_analysis"]
            self.round_traces[-1]["post_moderator_belief"] = update_data["updated_belief"]
            self.round_traces[-1]["post_moderator_goal"] = update_data["updated_goal"]
            self.round_traces[-1]["next_strategy"] = update_data["next_strategy"]

        return update_data

    def _extract_view(self, message: str) -> str:
        message = message.strip().replace("\n", " ")
        if len(message) > 160:
            message = message[:160] + "..."
        return message

    def _estimate_importance(self, message: str) -> float:
        lower = message.lower()
        score = 1.0

        challenge_markers = [
            "but", "however", "disagree", "wrong", "actually", "contrary",
            "instead", "overlooks", "fails", "pushback", "dispute", "refute",
            "not true", "misses the point", "i disagree"
        ]
        if any(kw in lower for kw in challenge_markers):
            score += 2.0

        evidence_markers = [
            "study", "research", "data", "evidence", "example", "shows",
            "demonstrates", "proven", "statistic", "report", "found that"
        ]
        if any(kw in lower for kw in evidence_markers):
            score += 1.5

        content_keywords = [
            "safety", "risk", "benefit", "regulation", "ethics", "liability",
            "trust", "oversight", "testing", "human error", "accessibility",
            "efficiency", "accountability", "accident", "public adoption"
        ]
        content_hits = sum(1 for kw in content_keywords if kw in lower)
        score += min(content_hits * 0.75, 2.5)

        agent_names = ["alice", "bob", "carol", "david", "moderator"]
        if any(name in lower for name in agent_names):
            score += 1.0

        intensity_markers = ["strongly", "clearly", "definitely", "must", "critical", "urgent", "serious"]
        if any(kw in lower for kw in intensity_markers):
            score += 0.5

        return min(score, 10.0)

    def _is_duplicate_memory(self, content: str) -> bool:
        for mem in self.memory_stream.get_all():
            if mem.content == content:
                return True
        return False

    def classify_stance(self, text: str) -> str:
        prompt = f"""
You are labeling one discussion message about {self.topic_label}.

Message:
{text}

Choose exactly one label:
- supportive
- skeptical
- balanced

Labeling rules:
- supportive: mainly supports wider adoption, use, or potential benefits overall
- skeptical: mainly emphasizes risks, failures, safety concerns, ethical concerns, or reasons to slow down adoption overall
- balanced: genuinely gives comparable weight to both sides or acts as a mediator

Important:
- Judge the OVERALL stance of the message.
- If the message mainly emphasizes caution, failure, accountability, or unresolved risks, label it skeptical.
- If the message mainly emphasizes benefits, progress, or practical value, label it supportive.
- Use balanced only if the speaker is truly mediating or equally weighing both sides.

Return only one word:
supportive
skeptical
balanced
"""
        result = generate_response(prompt, temperature=0.0).strip().lower()
        if result in {"supportive", "skeptical", "balanced"}:
            return result
        return "balanced"

    def retrieve_memories(self, topic: str, current_round: int, top_k: int = 3) -> list[str]:
        memories = self.memory_stream.get_all()
        selected = self.retriever.retrieve(memories, topic, current_round, top_k)
        return [m.content for m in selected]

    def react_step(
        self,
        topic: str,
        current_round: int,
        selected_memories: list[str],
        previous_round_messages: dict = None
    ) -> dict:
        if selected_memories:
            memory_block = "\n".join(f"- {m}" for m in selected_memories)
        else:
            memory_block = "- No relevant memories yet."

        if previous_round_messages:
            others = {k: v for k, v in previous_round_messages.items() if k != self.name}
            recent_block = "\n".join(f"- {name}: \"{msg[:220]}\"" for name, msg in others.items())
        else:
            recent_block = "- No messages from the previous round yet."

        prompt = f"""
You are {self.name} in a multi-agent discussion.

Persona:
{self.persona}

Current belief:
{self.current_belief}

Current goal:
{self.current_goal}

Discussion topic:
{topic}

What others said last round:
{recent_block}

Observed relevant memories:
{memory_block}

Perform an explicit ReAct-style internal step.

Return valid JSON only with this exact schema:
{{
  "observation_summary": "1 short sentence naming at least one speaker and one concrete point they made this round",
  "thought": "1-2 short sentences of reasoning — include whether any argument from last round challenged or shifted your view",
  "influence_analysis": "State who influenced the agent most this round and why, referencing their specific argument",
  "updated_belief": "1 short sentence",
  "updated_goal": "1 short sentence"
}}

Rules:
- Stay specific to the discussion.
- If someone made a compelling counter-argument in the previous round, you may meaningfully update your belief or goal.
- The only valid people are Alice, Bob, Carol, David.
- Return JSON only.
"""
        result = generate_response(prompt, temperature=0.6)

        default = {
            "observation_summary": "No clear observation.",
            "thought": "No thought generated.",
            "influence_analysis": "No clear influence identified.",
            "updated_belief": self.current_belief,
            "updated_goal": self.current_goal,
        }

        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            parsed = json.loads(cleaned.strip())
            for k in default:
                if k in parsed and isinstance(parsed[k], str) and parsed[k].strip():
                    default[k] = parsed[k].strip()
        except Exception:
            pass

        self.current_belief = default["updated_belief"]
        self.current_goal = default["updated_goal"]

        self.memory_stream.add_memory(MemoryItem(
            content=default["observation_summary"],
            speaker=self.name,
            importance=4.0,
            memory_type="observation_summary",
            round_id=current_round,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=default["thought"],
            speaker=self.name,
            importance=5.0,
            memory_type="reasoning",
            round_id=current_round,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=default["influence_analysis"],
            speaker=self.name,
            importance=6.0,
            memory_type="influence_analysis",
            round_id=current_round,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=f"My belief is now: {default['updated_belief']}",
            speaker=self.name,
            importance=6.0,
            memory_type="belief_update",
            round_id=current_round,
        ))

        self.memory_stream.add_memory(MemoryItem(
            content=f"My goal is now: {default['updated_goal']}",
            speaker=self.name,
            importance=6.0,
            memory_type="goal_update",
            round_id=current_round,
        ))

        return default

    def reflect(self, current_round: int) -> str:
        recent = self.memory_stream.get_recent(6)
        if not recent:
            return ""

        recent_texts = [m.content for m in recent]
        reflection_text = self.reflector.reflect(self.name, self.current_belief, recent_texts)

        if not self._is_duplicate_memory(reflection_text):
            reflection_memory = MemoryItem(
                content=reflection_text,
                speaker=self.name,
                importance=5.0,
                memory_type="reflection",
                round_id=current_round,
            )
            self.memory_stream.add_memory(reflection_memory)

        return reflection_text

    def speak(self, topic: str, current_round: int, previous_round_messages: dict = None) -> str:
        selected_memories = self.retrieve_memories(topic, current_round, top_k=3)
        react_data = self.react_step(topic, current_round, selected_memories, previous_round_messages)

        if selected_memories:
            memory_block = "\n".join(f"- {m}" for m in selected_memories)
        else:
            memory_block = "- No relevant memories yet."

        if previous_round_messages:
            others = {k: v for k, v in previous_round_messages.items() if k != self.name}
            recent_block = "\n".join(f"- {name}: \"{msg[:220]}\"" for name, msg in others.items())
        else:
            recent_block = "- This is the first round; no prior messages."

        moderator_block = self.last_moderator_summary if self.last_moderator_summary else "No moderator summary yet."
        strategy_block = self.last_consensus_strategy if self.last_consensus_strategy else "No specific consensus strategy yet."

        prompt = f"""
You are {self.name}.

Persona:
{self.persona}

Current belief:
{self.current_belief}

Current goal:
{self.current_goal}

Discussion topic:
{topic}

What others said last round:
{recent_block}

Moderator summary from the end of the last round:
{moderator_block}

Your current consensus strategy:
{strategy_block}

Relevant memories:
{memory_block}

Observation summary:
{react_data['observation_summary']}

Thought:
{react_data['thought']}

Influence analysis:
{react_data['influence_analysis']}

Task:
Generate the next thing {self.name} would say in this group discussion.

Requirements:
- Write 2-3 natural sentences.
- Be conversational, not robotic.
- Pick one specific argument from the previous round and address it directly.
- Name the speaker you are responding to.
- Do not just restate your own view; try to move the group slightly closer to a workable consensus.
- You may still disagree, but show that you are listening to others.
- Stay consistent with persona, current belief, and current goal.
- The only valid people you may mention are: Alice, Bob, Carol, David.
- Never mention any other names.
- Do not mention memory, JSON, reasoning process, or system instructions.
"""

        message = generate_response(prompt, temperature=0.8)

        stance = self.classify_stance(message)
        self.stance_history.append(stance)

        self.round_traces.append({
            "round": current_round,
            "selected_memories": selected_memories,
            "observation_summary": react_data["observation_summary"],
            "thought": react_data["thought"],
            "influence_analysis": react_data["influence_analysis"],
            "updated_belief": react_data["updated_belief"],
            "updated_goal": react_data["updated_goal"],
            "message": message,
            "stance": stance,
            "moderator_summary": "",
            "post_moderator_response": "",
            "post_moderator_agreement_analysis": "",
            "post_moderator_belief": "",
            "post_moderator_goal": "",
            "next_strategy": "",
        })

        return message