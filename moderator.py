# from llm import generate_response


# class Moderator:
#     def __init__(self, name: str = "Moderator"):
#         self.name = name

#     def summarize_round(self, topic: str, round_id: int, current_round_messages: dict[str, str]) -> str:
#         if current_round_messages:
#             message_block = "\n".join(
#                 f"- {speaker}: {message}"
#                 for speaker, message in current_round_messages.items()
#             )
#         else:
#             message_block = "- No messages this round."

#         prompt = f"""
# You are a neutral moderator in a multi-agent discussion.

# Discussion topic:
# {topic}

# Round:
# {round_id}

# This round's messages:
# {message_block}

# Your job:
# 1. Briefly summarize what each participant said.


# Requirements:
# - Be neutral.
# - Do not state your own opinion.
# - Keep it to 4-6 sentences.
# - Mention only these agents by name if needed: Alice, Bob, Carol, David.
# - The overall group goal is to move toward a reasonable consensus, not just repeat positions.
# """

#         return generate_response(prompt, temperature=0.4).strip()
    


# # 2. Identify the main disagreement or tension.
# # 3. Identify any emerging common ground.
# # 4. Suggest one next-step direction that may help the group move toward consensus.



# from llm import generate_response


# class Moderator:
#     def __init__(self, name: str = "Moderator"):
#         self.name = name

#     def summarize_round(self, topic: str, round_id: int, current_round_messages: dict[str, str]) -> str:
#         if current_round_messages:
#             message_block = "\n".join(
#                 f"- {speaker}: {message}"
#                 for speaker, message in current_round_messages.items()
#             )
#         else:
#             message_block = "- No messages this round."

#         prompt = f"""
# You are a neutral moderator in a multi-agent discussion.

# Discussion topic:
# {topic}

# Round:
# {round_id}

# This round's messages:
# {message_block}

# Your job:
# 1. Briefly summarize what each participant said.
# 2. Identify the main disagreement or unresolved tension.
# 3. Identify any emerging common ground.
# 4. Point out one important issue about the topic that still needs deeper discussion next round.

# Requirements:
# - Be neutral.
# - Do not state your own opinion.
# - Keep it to 5-7 sentences.
# - Mention only these agents by name if needed: Alice, Bob, Carol, David.
# - Keep the group focused on the core issue of the topic itself, not only side effects or policy details.
# """

#         return generate_response(prompt, temperature=0.4).strip()


from llm import generate_response


class Moderator:
    def __init__(self, name: str = "Moderator"):
        self.name = name

    def summarize_round(self, topic: str, round_id: int, current_round_messages: dict[str, str]) -> str:
        if current_round_messages:
            message_block = "\n".join(
                f"- {speaker}: {message}"
                for speaker, message in current_round_messages.items()
            )
        else:
            message_block = "- No messages this round."

        prompt = f"""
You are a neutral moderator in a multi-agent discussion.

Discussion topic:
{topic}

Round:
{round_id}

This round's messages:
{message_block}

Your job:
1. Briefly summarize what each participant said.
2. Identify the main disagreement or unresolved tension.
3. Identify any emerging common ground.
4. Say whether anyone seems meaningfully persuaded, unconvinced, or more cautious after this round.
5. Point out one important issue that still needs deeper discussion next round.

Requirements:
- Be neutral.
- Do not state your own opinion.
- Keep it to 5-7 sentences.
- Mention only these agents by name if needed: Alice, Bob, Carol, David.
- Do not blur disagreement into a generic group summary.
- Do not force consensus if a real disagreement remains.
- The overall group goal is to move toward a reasonable consensus, not just repeat positions.
- Keep the group focused on the core issue of the topic itself, not only side effects or policy details.
"""
        return generate_response(prompt, temperature=0.4).strip()