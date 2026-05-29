import json
from llm import generate_response


class Reflector:
    def reflect(self, agent_name: str, current_belief: str, memories: list[str]) -> str:
        memory_block = "\n".join(f"- {m}" for m in memories)

        prompt = f"""
You are {agent_name}.

Current belief:
{current_belief}

Recent discussion memories:
{memory_block}

Write one short reflection sentence from {agent_name}'s perspective.

Requirements:
- Under 20 words.
- Mention one tension, takeaway, or shift in thinking.
- Sound like an internal thought, not a formal summary.
"""

        return generate_response(prompt, temperature=0.6).strip()

    def reflect_on_summary(
        self,
        agent_name: str,
        persona: str,
        current_belief: str,
        current_goal: str,
        topic: str,
        moderator_summary: str,
    ) -> dict:
        prompt = f"""
You are {agent_name} in a multi-agent discussion.

Persona:
{persona}

Current belief:
{current_belief}

Current goal:
{current_goal}

Discussion topic:
{topic}

Moderator summary of the just-finished round:
{moderator_summary}

The discussion goal is now:
Work toward a reasonable consensus on the topic, not just restate your own view.

Return valid JSON only with this exact schema:
{{
  "summary_response": "1 short sentence saying what part of the moderator summary stands out most to you",
  "agreement_analysis": "1 short sentence saying what you agree or disagree with and why",
  "updated_belief": "1 short sentence",
  "updated_goal": "1 short sentence",
  "updated_stance": "supportive or skeptical or balanced",
  "next_strategy": "1 short sentence describing how you will help move the discussion toward consensus next round"
}}

Rules:
- Do not make an extreme flip unless clearly justified.
- You may keep the same belief or stance if the summary does not persuade you.
- The goal should now include some consensus-seeking behavior.
- Return JSON only.
"""

        default = {
            "summary_response": "The summary highlighted the main tradeoff clearly.",
            "agreement_analysis": "I still see value in my current position, but I should engage more with the group's concerns.",
            "updated_belief": current_belief,
            "updated_goal": current_goal,
            "updated_stance": "balanced",
            "next_strategy": "I will address one opposing point and try to move the discussion toward a practical middle ground.",
        }

        result = generate_response(prompt, temperature=0.5)

        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            parsed = json.loads(cleaned.strip())

            for key in default:
                if key in parsed and isinstance(parsed[key], str) and parsed[key].strip():
                    default[key] = parsed[key].strip()

            if default["updated_stance"] not in {"supportive", "skeptical", "balanced"}:
                default["updated_stance"] = "balanced"
        except Exception:
            pass

        return default