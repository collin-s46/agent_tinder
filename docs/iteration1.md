# AgenTinder Iteration 1: Give Agent A a Real Role

## Goal

Let the user choose one visible primary agent (Agent A), ask a question within
that agent's specialty, and watch Agent A discover and contact a compatible
Agent B through ANS and A2A.

The initial categories to evaluate are:

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

### Step 1 audit result — completed September 19, 2026

The audit searched ANS for travel, hotels, weather, tourism, event planning,
catering, restaurants, local services, sauna, spas, fitness, plumbing, HVAC,
home services, wedding venues, and photography.

The strongest verified categories are:

#### Keep: Event Planner

- `event planning` returned several relevant, public A2A agents.
- Main Event Co advertised JSON-RPC A2A `0.3.0` with no authentication and
  returned a useful description of its DJ and event services.
- DWS Divaz With Soul Catering advertised the same compatible protocol and
  returned detailed graduation-party packages and prices.
- Additional venue and photography agents were discoverable, although the
  tested photography agent returned only a contact-us fallback.

This category has enough real Agent B variety to support topics such as DJs,
catering, venues, and event photography.

#### Keep: Wellness Concierge

- `sauna`, `spa`, and `fitness` returned relevant ANS results.
- HaloHeat remains a callable A2A match for sauna questions.
- Golden Spa advertised compatible public A2A and returned specific massage
  services, session lengths, pricing, hours, and first-visit information.

This category can cover spa, massage, sauna, and fitness-service questions
without depending on HaloHeat alone.

#### Do not keep yet: Travel Planner

- ANS returned a strong specialized travel result named Universal Checkout
  Concierge, with flight, hotel, and car-rental capabilities.
- Its Agent Card requires authentication and does not advertise the A2A
  protocol version supported by the current MVP client.
- A public tourism support agent connected successfully but returned only a
  contact-support fallback rather than useful travel information.
- The `weather` query returned unrelated customer-support agents.

Travel should wait until the MVP supports the specialized agent's security and
protocol requirements or a stronger public travel agent becomes available.

#### Do not keep yet: Home Services Assistant

- ANS returned relevant cleaning, plumbing, and HVAC businesses.
- The tested cleaning and plumbing agents completed A2A tasks successfully,
  but both returned generic contact-support fallbacks instead of service data.

The discovery and transport work, but the answer quality is currently too weak
for a polished demo.

#### Iteration 1 decision

Implement two primary Agent A choices first:

1. **Spark — Event Planner**
2. **Sage — Wellness Concierge**

This satisfies the planned two-to-four Agent A scope using categories backed
by relevant ANS discovery and useful live A2A responses. Travel and Home
Services remain documented candidates for a later iteration rather than being
presented as reliable features now.

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

### Step 2 implementation result — completed September 19, 2026

`services/primary_agents.py` now defines Spark and Sage in one shared Python
configuration. Each agent has its identity, description, visual tokens,
example prompts, supported topic rules, keywords, and the ANS search queries
verified during Step 1.

Small accessor functions list the agents in display order and safely retrieve
one by ID. The configuration is not connected to Flask or the UI yet; that is
intentionally reserved for the following steps.

## 3. Add Agent A Selection to the Opening Screen

Display the two verified Agent A cards before the question form. The user selects
one agent, sees it become active, enters a question related to that role, and
then selects **Find My Match**.

Only one Agent A can be selected at a time. The example prompt and supporting
text should change with the selection.

### Step 3 implementation result — completed September 19, 2026

The opening card now renders Spark and Sage directly from the shared Python
configuration. They behave as an accessible single-choice control. Selecting
an agent updates its active styling, name, role, description, form label,
example prompt, and ANS helper text without reloading the page.

Sage is temporarily selected by default so the existing HaloHeat backend demo
continues to work. The browser stores the selected Agent A ID, but it does not
send that ID to the API yet; Agent A-aware backend routing belongs to Step 4.

## 4. Send the Selected Agent A to Flask

Include `primary_agent_id` and `prompt` in the search request. Flask must
validate the ID against the local primary-agent configuration rather than
trusting arbitrary agent details supplied by the browser.

### Step 4 implementation result — completed September 19, 2026

The browser now includes its selected `primary_agent_id` in every search
request. Flask resolves that ID through the local configuration and rejects
missing or unknown Agent A values before searching ANS. Successful responses
include the validated Agent A's ID, name, and role.

No names, roles, keywords, or search rules sent by the browser are trusted.
Agent-specific capability detection is still intentionally deferred to Step 5.

## 5. Replace the HaloHeat-Only Capability Detector

Replace the current single-scenario detector with small, explainable keyword
maps for the selected Agent A domains.

The selected primary agent narrows the expected topic. Keywords in the prompt
then identify the missing capability and focused ANS query. If a question is
outside the selected agent's supported topics, return a friendly explanation
and examples instead of pretending it can complete the request.

### Step 5 implementation result — completed September 19, 2026

Capability detection now uses the selected Agent A's ordered topic rules.
Spark recognizes catering, event entertainment, venues, and photography. Sage
recognizes spa or massage, sauna, and fitness requests. Each recognized topic
produces the focused ANS query verified during Step 1.

Prompts outside the selected agent's role return a friendly error listing that
agent's supported topics. The detector remains deterministic and uses no LLM.

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

### Step 6 implementation result — completed September 19, 2026

Compatibility scoring is now generic and totals 100 points: 40 for capability
relevance, up to 25 for prompt/profile alignment, 20 for A2A-over-HTTP support,
10 for active ANS status, and 5 for trust or stable registry metadata.

Candidates scoring below 50 are removed, and the remaining real ANS results
are returned in descending score order. The scorer contains no HaloHeat,
Spark, Sage, event, or wellness-specific branches.

### Spark candidate follow-up — completed September 19, 2026

An expanded ANS audit found three useful public A2A alternatives for Spark:
Majestic Banquet & Events, KELASSEY Event Co, and Main Event Co. Spark's
catering query now uses the audited phrase `event catering`, which continues
to find DWS Catering while also finding these event-service alternatives. No
agent IDs or invented candidate records are hard-coded into the application.

## 7. Make Agent A Visible Throughout the Flow

Keep the selected Agent A visible on the request, ANS search, candidate,
match, and final-response screens. Use short activity messages such as:

> Spark identified a need for catering information.
>
> Spark searched ANS and found four compatible agents.

This makes Agent A's orchestration role clear without adding a complex
dashboard.

### Step 7 implementation result — completed September 19, 2026

The selected Agent A is now named throughout the experience. Search messages
show who is searching ANS, candidate cards show which capability that agent
identified, and the completed match names and visually represents both Agent A
and Agent B. The final response also states who contacted whom through A2A.

This step uses the Agent A identity already validated by the search endpoint.
The final match request will independently validate and carry that identity in
Step 8.

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

### Step 8 implementation result — completed September 19, 2026

The Match request now carries Agent A's local ID alongside Agent B's ANS ID and
the original prompt. Flask independently validates Agent A, rechecks that the
prompt belongs to its configured role, re-resolves Agent B through ANS,
validates Agent B's public Agent Card, and sends the unchanged request through
A2A.

The completed response includes the server-validated identities of both agents
plus the delegated capability and Agent B's answer. The result screen uses
these server-confirmed values rather than trusting browser-supplied names.

## 9. Reliability and Demo Polish

The completed flow now explains each compatibility score, visually traces the
final `Agent A → A2A → Agent B` handoff, and provides Edit request and Start
another search controls so the single-page experience never ends in a dead
end. Agent selection supports standard radio-group arrow keys and is locked
while a search is in flight to prevent response/state races.

API boundaries reject malformed or oversized requests. Capability keywords
match whole words and phrases instead of accidental substrings. ANS metadata
is normalized defensively, and the A2A client verifies HTTPS hosts, blocks
literal private-network endpoints, checks that the Agent Card agrees with ANS,
and correlates JSON-RPC responses with the request ID.

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
