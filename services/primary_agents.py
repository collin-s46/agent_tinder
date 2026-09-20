"""Local configuration for the primary agents shown by AgenTinder.

These are Agent A choices: small local orchestrators that discover a remote
Agent B through ANS. They are not records copied from ANS and they do not need
their own network service for this MVP.
"""


# Keeping these definitions in one Python dictionary gives Flask, the future
# capability detector, and the UI one shared source of truth. The order is
# intentional: Spark will appear first and Sage second when the UI uses this
# configuration in a later step.
PRIMARY_AGENTS = {
    "spark": {
        "id": "spark",
        "name": "Spark",
        "role": "Event Planner",
        "description": (
            "Plans celebrations by finding specialists for catering, venues, "
            "entertainment, and photography."
        ),
        # The UI can translate these small tokens into its existing visual
        # style without putting CSS classes or markup in Python.
        "icon": "spark",
        "theme": "coral",
        "prompt_placeholder": (
            "Ask anything about catering, DJs, entertainment, venues, "
            "or event photography…"
        ),
        "example_prompts": (
            "What catering services do you offer for a graduation party?",
            "Find a DJ service for a birthday celebration.",
        ),
        "topic_rules": (
            {
                "id": "catering",
                "label": "Catering",
                "keywords": (
                    "cater",
                    "catering",
                    "food",
                    "menu",
                    "meal",
                ),
                # This broader audited query still finds DWS Catering while
                # also returning usable event-planning alternatives for Pass.
                "search_query": "event catering",
            },
            {
                "id": "entertainment",
                "label": "DJs and entertainment",
                "keywords": (
                    "dj",
                    "music",
                    "entertainment",
                    "performer",
                    "event planner",
                    "event planning",
                    "birthday party",
                    "celebration",
                ),
                "search_query": "event planning",
            },
            {
                "id": "venue",
                "label": "Venues",
                "keywords": (
                    "venue",
                    "banquet",
                    "event space",
                    "wedding location",
                ),
                "search_query": "wedding venue",
            },
            {
                "id": "photography",
                "label": "Event photography",
                "keywords": (
                    "photo",
                    "photographer",
                    "photography",
                    "pictures",
                ),
                "search_query": "photography",
            },
        ),
    },
    "sage": {
        "id": "sage",
        "name": "Sage",
        "role": "Wellness Concierge",
        "description": (
            "Finds wellness specialists for spa treatments, massage, sauna, "
            "and fitness services."
        ),
        "icon": "lotus",
        "theme": "lavender",
        "prompt_placeholder": "Ask anything about wellness…",
        "example_prompts": (
            "What services does HaloHeat offer, and how much is a drop-in sauna session?",
            "What spa services and prices are available for a first-time visitor?",
        ),
        "topic_rules": (
            {
                "id": "spa",
                "label": "Spa and massage",
                "keywords": (
                    "spa",
                    "massage",
                    "facial",
                    "treatment",
                    "relaxation",
                    "wellness",
                    "self-care",
                ),
                # The Golden Spa agent returned detailed services and prices
                # for this query during the Step 1 audit.
                "search_query": "spa",
            },
            {
                "id": "sauna",
                "label": "Sauna",
                "keywords": (
                    "sauna",
                    "haloheat",
                    "infrared",
                    "heat therapy",
                    "sweat session",
                ),
                "search_query": "sauna",
            },
            {
                "id": "fitness",
                "label": "Fitness",
                "keywords": (
                    "fitness",
                    "gym",
                    "workout",
                    "training",
                    "exercise",
                ),
                "search_query": "fitness",
            },
        ),
    },
}


def list_primary_agents():
    """Return the configured Agent A choices in their display order."""
    return list(PRIMARY_AGENTS.values())


def get_primary_agent(agent_id):
    """Return one configured Agent A, or None when its ID is unknown."""
    if not isinstance(agent_id, str):
        return None
    return PRIMARY_AGENTS.get(agent_id.strip().casefold())
