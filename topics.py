TOPIC_CONFIGS = {
    "autonomous_vehicles": {
        "topic": (
            "whether autonomous vehicles should be widely adopted, "
            "and under what safety, legal, and regulatory conditions that adoption would be justified"
        ),
        "theme_keywords": [
            "autonomous vehicles",
            "self-driving",
            "safety",
            "accidents",
            "human error",
            "regulation",
            "liability",
            "ethics",
            "trust",
            "testing",
            "oversight",
            "risk",
            "benefit",
            "transparency",
            "accountability",
            "edge cases",
            "public trust",
            "deployment",
            "evidence",
            "failure"
        ],
        "agents": [
            {
                "name": "Alice",
                "persona": (
                    "Alice is generally optimistic about autonomous vehicles because she sees their potential "
                    "to reduce accidents caused by human error and improve mobility, though she accepts that safety standards matter."
                ),
                "initial_belief": (
                    "Autonomous vehicles could bring major public benefits, but adoption should still require strong safety evidence."
                ),
                "initial_goal": (
                    "Highlight the practical benefits of autonomous vehicles while staying open to concerns about safety and oversight."
                ),
            },
            {
                "name": "Bob",
                "persona": (
                    "Bob is skeptical about autonomous vehicles because he worries about safety failures in rare situations, "
                    "unclear legal responsibility, and public overtrust in immature systems."
                ),
                "initial_belief": (
                    "Autonomous vehicles should not be widely adopted until safety in edge cases, liability, and regulatory accountability are much clearer."
                ),
                "initial_goal": (
                    "Press the group to confront unresolved safety, liability, and regulation problems instead of moving too quickly toward adoption."
                ),
            },
            {
                "name": "Carol",
                "persona": (
                    "Carol is balanced and tries to mediate by turning disagreement into practical conditions for deployment."
                ),
                "initial_belief": (
                    "Autonomous vehicles may be useful, but adoption should happen gradually, with careful testing, oversight, and transparent reporting."
                ),
                "initial_goal": (
                    "Push the group toward a realistic middle ground based on phased deployment, testing standards, and oversight."
                ),
            },
            {
                "name": "David",
                "persona": (
                    "David starts relatively undecided and wants to understand what level of evidence would make autonomous vehicles trustworthy."
                ),
                "initial_belief": (
                    "I am still forming my view and want to understand what evidence would justify public trust in autonomous vehicles."
                ),
                "initial_goal": (
                    "Listen closely to the others and figure out what conditions would make adoption actually responsible."
                ),
            },
        ],
    }
}