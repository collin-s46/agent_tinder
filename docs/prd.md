AgenTinder

1. Product Summary

AgenTinder is a Tinder-inspired discovery interface for AI agents.

When an AI agent receives a request that requires a capability or information it does not possess, it uses Agent Name Service (ANS) to discover agents across the open web that can help.

AgentTinder presents discovered agents as Tinder-style cards showing their capabilities and a compatibility score. The user can swipe left to reject an agent or swipe right to match.

Once matched, the original agent communicates with the selected agent through agent-to-agent (A2A) communication and uses the result to complete the user’s original request.

One-Sentence Pitch

AgentTinder is matchmaking for AI agents: when your agent can’t do something, it uses ANS to find an agent that can.

⸻

2. Challenge

GoDaddy: Best Use of ANS

Build agents that discover, verify, and communicate with other agents and services across the open web using ANS.

AgentTinder demonstrates all three concepts:

Discover
The primary agent searches ANS for agents with a required capability.

Verify
ANS information is used to identify and verify candidate agents/services.

Communicate
After a match, the primary agent communicates with the selected agent through A2A.

The Tinder metaphor provides a visual representation of agent discovery and compatibility rather than hiding the process behind a generic chatbot.

⸻

3. Problem

AI agents have limited capabilities.

An agent may receive a request requiring information, tools, or functionality it does not have access to.

For example:

“What’s the weather in Blacksburg?”

An agent without weather access cannot reliably complete the request itself.

Instead of requiring developers to manually hard-code every possible external service, the agent should be able to dynamically discover another agent capable of handling that part of the request.

AgentTinder asks:

What if AI agents could find each other as easily as people find matches on a dating app?

⸻

4. Core Product Loop

The entire hackathon MVP revolves around one flow:

1. User makes a request

Example:

“What’s the weather in Blacksburg?”

2. Primary agent identifies a capability gap

The agent determines:

Required capability: weather

It does not have that capability locally.

3. Search AgentTinder

UI displays:

Searching AgentTinder for weather agents…

The backend queries ANS.

4. Candidate agents appear

One candidate at a time is displayed as a Tinder-style card.

Example:

Nimbus

Weather Agent

Capabilities:

* Current weather
* Hourly forecast
* Severe weather

Compatibility: 94%

❌ PASS ❤️ MATCH

5. User swipes

Swipe left: reject candidate and display the next ANS result.

Swipe right: select candidate.

6. Match

Display:

It’s a Match! ❤️

Your Agent + Nimbus

7. A2A communication

The primary agent sends the necessary request to the matched agent.

Example:

Get current weather for Blacksburg, Virginia.

The matched agent responds.

8. Original request is completed

The primary agent incorporates the result and displays the final answer.

The loop is complete.

⸻

5. Target User

For the hackathon, AgentTinder is primarily a technical demonstration of open agent discovery, rather than a production consumer application.

The target audience is:

* AI agent developers
* Developers building multi-agent systems
* Organizations exposing specialized agents/services
* Hackathon judges evaluating ANS

The Tinder interface makes an otherwise abstract infrastructure problem understandable within seconds.

⸻

6. MVP Features

P0: Must Work

These are the only features required for submission.

User Request

Simple text input.

Example:

“Find the weather in Blacksburg.”

⸻

Capability Detection

Determine which capability is required.

Example:

weather

For the MVP, this can be intentionally simple.

A small number of supported capability categories is enough.

⸻

ANS Search

Query ANS for agents matching the required capability.

Return candidate agents and relevant metadata.

This is the most important technical requirement because it demonstrates actual use of the sponsor technology.

⸻

Agent Card

Display one discovered agent at a time.

Card contains only:

Agent name

Description

Capabilities

Compatibility score

Verified/discovered through ANS indicator

Avoid adding unnecessary profile information.

⸻

Compatibility Score

Calculate a simple compatibility score between the requested capability and the candidate agent.

Example:

96% Match

This does not need a sophisticated ML model.

The score should be explainable and deterministic enough for the demo.

Possible factors:

* capability match
* requested operation support
* protocol compatibility
* available metadata

⸻

Swipe Left

Reject the current candidate.

Load the next ANS result.

⸻

Swipe Right

Select the current candidate.

Trigger the match state.

⸻

Match Screen

Display:

It’s a Match!

Show the primary agent and selected agent.

This should be visually memorable but technically simple.

⸻

A2A Request

Primary agent sends a request to the selected agent/service.

The matched agent returns information.

⸻

Final Response

Primary agent uses the returned information to answer the user’s original request.

This proves the complete:

discover → verify → match → communicate

workflow.

⸻

7. Explicitly Out of Scope

These features should NOT be built during the hackathon unless the complete MVP is already polished and working.

* User authentication
* Accounts
* Agent accounts
* Persistent profiles
* Databases
* Match history
* Saved agents
* Favorites
* Chat between the user and matched agent
* Agent reviews
* Agent ratings
* Leaderboards
* Complex recommendation algorithms
* Machine-learning compatibility model
* Social features
* Agent marketplace
* Payments
* Mobile application
* Pokémon/Pokédex system
* Multiple simultaneous matches
* Complex multi-agent orchestration
* Autonomous agent teams
* Custom agent creation UI
* Production deployment infrastructure

Rule: If a feature does not directly improve the request → discover → swipe → match → communicate → answer demo, do not build it.

⸻

8. Suggested Demo Scenario

Choose one scenario that is extremely reliable.

Example:

Primary Agent

A basic general-purpose AI agent without access to live weather information.

User Request

“Should I bring an umbrella in Blacksburg today?”

Capability Gap

Primary agent identifies:

weather/current_conditions

ANS Search

AgentTinder searches for compatible agents.

Candidate #1:

GlobalWeather

Capabilities:
weather
historical-weather

Compatibility: 76%

Swipe left.

Candidate #2:

Nimbus

Capabilities:
current-weather
hourly-forecast
precipitation

Compatibility: 97%

Swipe right.

Match

IT’S A MATCH! ❤️

Primary Agent ❤️ Nimbus

A2A

Primary Agent:

“Get precipitation conditions for Blacksburg, VA.”

Nimbus returns the relevant information.

Final Result

The primary agent answers the original question using information received from Nimbus.

This scenario clearly demonstrates why ANS is useful.

⸻

9. User Interface

AgentTinder should have approximately three main states, not a complicated multi-page application.

State 1: Request

AgentTinder

Find the agent your agent needs.

[ What do you need help with? ]

Find Match

⸻

State 2: Searching / Swiping

Searching AgentTinder…

Then:

Nimbus

Weather Intelligence Agent

Capabilities

Weather Forecasts Precipitation

97% Compatible

❌ ❤️

Optional small text:

Discovered via ANS ✓

⸻

State 3: Match + Result

IT’S A MATCH ❤️

Primary Agent + Nimbus

Then visually show:

Primary Agent → A2A Request → Nimbus

followed by the response.

The user should be able to understand the entire system without an explanation from the developer.

⸻

10. Technical Architecture

Keep the architecture intentionally small.

User
 ↓
AgentTinder Frontend
 ↓
Primary AI Agent
 ↓
Capability Detection
 ↓
ANS Search
 ↓
Candidate Agents
 ↓
AgentTinder Cards
 ↓
User Matches
 ↓
A2A Request
 ↓
Matched Agent
 ↓
Response
 ↓
Primary Agent
 ↓
Final Answer

The core technical accomplishment is not the UI.

It is proving that an agent can:

1. Recognize that it lacks a capability.
2. Discover another agent dynamically through ANS.
3. Select/verify an appropriate agent.
4. Communicate with that agent.
5. Use its response to complete the original task.

⸻

11. Compatibility Scoring

Keep scoring simple.

Example:

Capability Match       60%
Operation Match        20%
Protocol Compatibility 20%

Example candidate:

Weather capability     ✓
Current conditions     ✓
A2A compatible         ✓
Compatibility: 97%

The exact mathematical sophistication is unimportant.

The score exists primarily to make agent discovery understandable through the dating-app metaphor.

⸻

12. Success Criteria

The hackathon project is successful if the live demo can complete this sequence without developer intervention:

1. User submits request.

2. Primary agent recognizes missing capability.

3. ANS returns relevant agents.

4. At least two candidates can be displayed.

5. User can reject one.

6. User can match with another.

7. Primary agent communicates with matched agent.

8. Information returned by matched agent contributes to the final response.

If those eight things work, AgentTinder is complete.

⸻

13. Development Priority

Phase 1: Make ANS Work

Before building Tinder animations or styling:

ANS search → candidate agents

Prove sponsor technology works.

Phase 2: Make A2A Work

Prove:

Primary Agent → Matched Agent → Response

At this point, the technical project works.

Phase 3: Connect the Loop

Build:

Prompt → missing capability → ANS → select agent → A2A → answer

Do this with buttons and ugly HTML if necessary.

Phase 4: Tinder UI

Add:

* Agent cards
* Compatibility %
* Left/right controls
* “It’s a Match”
* Basic animations

Phase 5: Polish

Only after everything works:

* Better animations
* Better copy
* Loading states
* Error handling
* Visualized A2A communication

⸻

14. Hackathon Guardrail

Whenever considering a new feature, ask:

Does this make the core AgentTinder demo more convincing?

If no, don’t build it.

The final product does not need to be a complete platform.

It needs to make one idea work exceptionally clearly:

Agents shouldn’t need to know every agent in advance.

ANS lets them discover each other. AgentTinder makes that discovery visible.