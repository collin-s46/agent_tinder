# AgenTinder Iteration 1: Give Agent A a Real Role

## Goal

Let the user choose one visible primary agent (Agent A), ask a question within
that agent's specialty, and watch Agent A discover and contact a compatible
Agent B through ANS and A2A.

The recommended starting set is:

- **Atlas — Travel Planner:** destinations, accommodations, weather, and activities.
- **Spark — Event Planner:** venues, catering, entertainment, and event logistics.
- **Scout — Local Services Assistant:** businesses, pricing, bookings, and customer support.

These primary agents will be small, deterministic Python orchestrators. This
iteration will not add an LLM, database, authentication, user accounts, or
separately hosted Agent A services.

## 1. Validate the Available ANS Agents First

Before changing the interface, search ANS for likely domains such as travel,
hotels, weather, event planning, catering, and local services. Inspect the
Agent Cards and test harmless A2A questions with the strongest candidates.

Only keep an Agent A category if ANS contains at least one relevant, publicly
callable Agent B. Do not invent agents or hard-code fake responses when a
category has no usable live match.

## 2. Add a Small Primary-Agent Configuration

Create one Python configuration containing each Agent A's:

- ID
- Name and role
- Description
- Supported topics
- Example questions
- Visual color or icon
- Capability keywords and ANS search terms

Keep this as ordinary Python data rather than introducing a database.

## 3. Add Agent A Selection to the Opening Screen

Display three clean Agent A cards before the question form. The user selects
one agent, sees it become active, enters a question related to that role, and
then selects **Find My Match**.

Only one Agent A can be selected at a time. The example prompt and supporting
text should change with the selection.

## 4. Send the Selected Agent A to Flask

Include `primary_agent_id` and `prompt` in the search request. Flask must
validate the ID against the local primary-agent configuration rather than
trusting arbitrary agent details supplied by the browser.

## 5. Replace the HaloHeat-Only Capability Detector

Replace the current single-scenario detector with small, explainable keyword
maps for the selected Agent A domains.

The selected primary agent narrows the expected topic. Keywords in the prompt
then identify the missing capability and focused ANS query. If a question is
outside the selected agent's supported topics, return a friendly explanation
and examples instead of pretending it can complete the request.

## 6. Replace the HaloHeat-Specific Compatibility Score

Use a generic, deterministic score rather than awarding most points for the
word `HaloHeat`. The score should consider:

- Requested capability overlap with Agent B's skills or tags
- Prompt overlap with Agent B's name or description
- A usable A2A-over-HTTP endpoint
- Active ANS lifecycle status
- Available trust or registry metadata

Reject extremely weak results instead of presenting unrelated agents as good
matches.

## 7. Make Agent A Visible Throughout the Flow

Keep the selected Agent A visible on the request, ANS search, candidate,
match, and final-response screens. Use short activity messages such as:

> Atlas identified a need for local activity information.
>
> Atlas searched ANS and found four compatible agents.

This makes Agent A's orchestration role clear without adding a complex
dashboard.

## 8. Let Agent A Perform the A2A Delegation

When the user chooses Match, send `primary_agent_id`, the selected ANS
`agent_id`, and the original `prompt` to Flask. The backend will:

1. Validate Agent A.
2. Re-resolve Agent B through ANS.
3. Validate Agent B's Agent Card.
4. Send the request through A2A.
5. Return the answer with both agent names.

For this MVP, Agent A will transparently wrap and present Agent B's response.
It will not use an LLM to rewrite the answer.

## Intended Flow

```text
Choose Agent A
      ↓
Ask a question within its specialty
      ↓
Agent A identifies the missing capability
      ↓
Agent A searches ANS
      ↓
User passes or matches with an ANS Agent B
      ↓
Agent A contacts Agent B over A2A
      ↓
Agent A presents Agent B's response
```
