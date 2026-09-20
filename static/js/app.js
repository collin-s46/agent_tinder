"use strict";

// Cache the page elements once so we can reuse them during every search.
const searchForm = document.querySelector("#search-form");
const promptInput = document.querySelector("#agent-request");
const promptLabel = document.querySelector("#agent-request-label");
const findMatchButton = document.querySelector("#find-match-button");
const buttonLabel = findMatchButton.querySelector(".button-label");
const searchStatus = document.querySelector("#search-status");
const requestView = document.querySelector("#request-view");
const candidateView = document.querySelector("#candidate-view");
const candidateName = document.querySelector("#candidate-name");
const candidateDescription = document.querySelector("#candidate-description");
const candidateScore = document.querySelector("#candidate-score");
const scoreDetails = document.querySelector("#score-details");
const scoreBreakdownValues = document.querySelectorAll("[data-score-key]");
const candidateStatus = document.querySelector("#candidate-status");
const candidateSkillList = document.querySelector("#candidate-skill-list");
const candidateAnsName = document.querySelector("#candidate-ans-name");
const candidatePosition = document.querySelector("#candidate-position");
const candidatePrimaryAgentName = document.querySelector(
  "#candidate-primary-agent-name",
);
const candidateCapabilityLabel = document.querySelector(
  "#candidate-capability-label",
);
const passButton = document.querySelector("#pass-button");
const matchButton = document.querySelector("#match-button");
const matchButtonLabel = matchButton.querySelector(".match-button-label");
const candidateControlStatus = document.querySelector(
  "#candidate-control-status",
);
const editRequestButton = document.querySelector("#edit-request-button");
const matchView = document.querySelector("#match-view");
const matchKicker = document.querySelector("#match-kicker");
const matchMessage = document.querySelector("#match-message");
const matchedPrimaryAgentName = document.querySelector(
  "#matched-primary-agent-name",
);
const matchedAgentName = document.querySelector("#matched-agent-name");
const matchedAgentAnswer = document.querySelector("#matched-agent-answer");
const matchedPrimaryAvatarInitials = document.querySelector(
  "#matched-primary-avatar-initials",
);
const matchedPrimaryAvatarName = document.querySelector(
  "#matched-primary-avatar-name",
);
const matchedAgentAvatarInitials = document.querySelector(
  "#matched-agent-avatar-initials",
);
const matchedAgentAvatarName = document.querySelector(
  "#matched-agent-avatar-name",
);
const agentResponseTitle = document.querySelector("#agent-response-title");
const tracePrimaryAgent = document.querySelector("#trace-primary-agent");
const traceProtocol = document.querySelector("#trace-protocol");
const traceMatchedAgent = document.querySelector("#trace-matched-agent");
const answerQualityWarning = document.querySelector(
  "#answer-quality-warning",
);
const tryNextButton = document.querySelector("#try-next-button");
const newSearchButton = document.querySelector("#new-search-button");
const primaryAgentOptions = document.querySelectorAll(".primary-agent-option");
const selectedPrimaryAgentName = document.querySelector(
  "#selected-primary-agent-name",
);
const selectedPrimaryAgentRole = document.querySelector(
  "#selected-primary-agent-role",
);
const selectedPrimaryAgentDescription = document.querySelector(
  "#selected-primary-agent-description",
);
const selectedAgentNote = document.querySelector("#selected-agent-note");

// Flask renders the safe local configuration into this JSON script element.
// Parsing it avoids duplicating names, descriptions, and examples in JavaScript.
const primaryAgentData = JSON.parse(
  document.querySelector("#primary-agent-data").textContent,
);
const primaryAgentsById = new Map(
  primaryAgentData.map((agent) => [agent.id, agent]),
);

// Keep the search and selection in memory so Pass can move through the deck
// and Match can send the currently displayed agent to the Flask backend.
const searchState = {
  primaryAgentId: "sage",
  primaryAgent: null,
  capability: null,
  capabilityLabel: null,
  candidates: [],
  currentIndex: 0,
  selectedCandidate: null,
};

for (const option of primaryAgentOptions) {
  option.addEventListener("click", () => {
    selectPrimaryAgent(option.dataset.agentId);
  });

  option.addEventListener("keydown", (event) => {
    const options = [...primaryAgentOptions];
    const currentIndex = options.indexOf(option);
    let nextIndex = null;

    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      nextIndex = (currentIndex + 1) % options.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      nextIndex = (currentIndex - 1 + options.length) % options.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = options.length - 1;
    }

    if (nextIndex !== null) {
      event.preventDefault();
      options[nextIndex].click();
      options[nextIndex].focus();
    }
  });
}

function selectPrimaryAgent(agentId) {
  const agent = primaryAgentsById.get(agentId);
  if (!agent || agentId === searchState.primaryAgentId) {
    return;
  }

  const previousAgent = primaryAgentsById.get(searchState.primaryAgentId);
  const currentPrompt = promptInput.value.trim();
  const previousExample = previousAgent?.example_prompts[0] || "";

  searchState.primaryAgentId = agent.id;
  searchState.primaryAgent = null;
  searchState.capability = null;
  searchState.capabilityLabel = null;
  searchState.candidates = [];

  // Use radio semantics so keyboard and screen-reader users receive the same
  // single-selection behavior as someone clicking the cards visually.
  for (const option of primaryAgentOptions) {
    const isSelected = option.dataset.agentId === agent.id;
    option.classList.toggle("primary-agent-option--selected", isSelected);
    option.setAttribute("aria-checked", String(isSelected));
    option.tabIndex = isSelected ? 0 : -1;
  }

  selectedPrimaryAgentName.textContent = agent.name;
  selectedPrimaryAgentRole.textContent = agent.role;
  selectedPrimaryAgentDescription.textContent = agent.description;
  promptLabel.textContent = `What should ${agent.name} help with?`;
  selectedAgentNote.textContent =
    `${agent.name} will search ANS for compatible agents.`;

  // Replace an empty prompt or the previous agent's untouched example. Never
  // overwrite a question the user has started writing themselves.
  if (!currentPrompt || currentPrompt === previousExample) {
    promptInput.value = agent.example_prompts[0];
  }
  promptInput.placeholder = agent.example_prompts[0];

  // A message from an earlier search no longer applies to the newly selected
  // primary agent.
  searchStatus.hidden = true;
}

searchForm.addEventListener("submit", async (event) => {
  // A form normally reloads the page. Preventing that lets JavaScript call the
  // Flask API while the current page stays visible.
  event.preventDefault();

  const prompt = promptInput.value.trim();
  if (!prompt) {
    showStatus("Please enter a request before searching.", "error");
    promptInput.focus();
    return;
  }

  setSearching(true);
  const selectedPrimaryAgent = primaryAgentsById.get(
    searchState.primaryAgentId,
  );
  showStatus(
    `${selectedPrimaryAgent.name} is searching ANS for compatible agents…`,
    "loading",
  );

  try {
    // Send the selected local Agent A ID with the prompt. Flask validates the
    // ID against its own configuration instead of trusting browser-supplied
    // names, roles, or capability rules.
    const response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        primary_agent_id: searchState.primaryAgentId,
        prompt,
      }),
    });

    const data = await readApiResponse(response, "The agent search failed.");
    if (!Array.isArray(data.candidates) || !data.primary_agent) {
      throw new Error("The search service returned an unexpected response.");
    }

    searchState.primaryAgent = data.primary_agent;
    searchState.capability = data.capability;
    searchState.capabilityLabel = data.capability_label;
    searchState.candidates = buildDemoDeck(data.candidates);
    searchState.currentIndex = 0;
    searchState.selectedCandidate = null;

    const count = searchState.candidates.length;
    if (count === 0) {
      showStatus("No compatible agents were found through ANS.", "error");
      return;
    }

    const noun = count === 1 ? "agent" : "agents";
    showStatus(
      `${data.primary_agent.name} found ${count} compatible ${noun} through ANS.`,
      "success",
    );

    // Start the deck at its first candidate. Pass moves forward through this
    // in-memory list, while Match connects the displayed candidate over A2A.
    renderCandidate(searchState.candidates[0]);
  } catch (error) {
    // This handles both Flask API errors and browser/network failures.
    showStatus(error.message || "Unable to reach the search service.", "error");
  } finally {
    setSearching(false);
  }
});

function setSearching(isSearching) {
  // Disable the button to prevent duplicate searches while one is running.
  searchForm.setAttribute("aria-busy", String(isSearching));
  findMatchButton.disabled = isSearching;
  for (const option of primaryAgentOptions) {
    option.disabled = isSearching;
  }
  buttonLabel.textContent = isSearching ? "Searching ANS…" : "Find My Match";
}

function showStatus(message, type) {
  // Reuse one accessible live region for loading, success, and error messages.
  searchStatus.textContent = message;
  searchStatus.className = `search-status search-status--${type}`;
  searchStatus.hidden = false;
}

function renderCandidate(candidate) {
  // Use textContent and DOM elements instead of innerHTML because all candidate
  // text comes from an external registry.
  candidateName.textContent = candidate.name;
  candidateDescription.textContent =
    candidate.description || "No description provided by this agent.";
  candidateScore.textContent = `${candidate.compatibility.score}%`;
  candidateStatus.textContent = candidate.status || "Unknown";
  const isActive = candidate.status?.toLowerCase() === "active";
  candidateStatus.classList.toggle("active-badge--inactive", !isActive);
  candidateAnsName.textContent = candidate.ans_name;
  candidatePosition.textContent = `${searchState.currentIndex + 1} of ${searchState.candidates.length}`;
  candidatePrimaryAgentName.textContent = searchState.primaryAgent.name;
  candidateCapabilityLabel.textContent = searchState.capabilityLabel;
  candidateControlStatus.textContent = "";
  scoreDetails.open = false;

  const breakdown = candidate.compatibility.breakdown || {};
  for (const value of scoreBreakdownValues) {
    const points = Number(breakdown[value.dataset.scoreKey]) || 0;
    value.textContent = `+${points}`;
  }

  candidateSkillList.replaceChildren();
  const skills = candidate.skills.slice(0, 3);

  if (skills.length === 0) {
    const fallbackSkill = document.createElement("span");
    fallbackSkill.textContent = "General assistance";
    candidateSkillList.append(fallbackSkill);
  } else {
    for (const skill of skills) {
      const skillPill = document.createElement("span");
      skillPill.textContent = skill.name || skill.id;
      candidateSkillList.append(skillPill);
    }
  }

  requestView.hidden = true;
  matchView.hidden = true;
  candidateView.hidden = false;
  candidateView.classList.remove("candidate-view--passing");
  setCandidateControlsDisabled(false);
  candidateView.focus();
}

passButton.addEventListener("click", () => {
  const nextIndex = searchState.currentIndex + 1;

  if (nextIndex >= searchState.candidates.length) {
    candidateControlStatus.textContent = "No more compatible agents were found.";
    passButton.disabled = true;
    return;
  }

  // Briefly move the current card left before replacing it with the next real
  // ANS result. Disabling both controls prevents double-clicks mid-animation.
  setCandidateControlsDisabled(true);
  candidateView.classList.add("candidate-view--passing");

  window.setTimeout(() => {
    searchState.currentIndex = nextIndex;
    renderCandidate(searchState.candidates[searchState.currentIndex]);
  }, 220);
});

matchButton.addEventListener("click", async () => {
  const candidate = searchState.candidates[searchState.currentIndex];
  const prompt = promptInput.value.trim();

  // A candidate should always be present here, but this guard prevents a bad
  // request if the page state changes unexpectedly.
  if (!candidate || !prompt) {
    candidateControlStatus.textContent =
      "This match is missing an agent or request. Please search again.";
    return;
  }

  // Keep the user on the candidate card while the remote agent is working.
  // This gives us a natural place to show loading and error messages.
  setMatching(true);
  candidateControlStatus.textContent = `Connecting with ${candidate.name} over A2A…`;

  try {
    // Send only Agent A's short local ID, Agent B's registry ID, and the
    // original prompt. Flask independently validates both identities and never
    // accepts a remote endpoint URL from the browser.
    const response = await fetch("/api/match", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        primary_agent_id: searchState.primaryAgentId,
        agent_id: candidate.agent_id,
        prompt,
      }),
    });

    const data = await readApiResponse(response, "The A2A connection failed.");
    if (!data.primary_agent || typeof data.answer !== "string") {
      throw new Error("The matched agent returned an unexpected response.");
    }

    // Save and display the confirmed result only after the agent completes its
    // task. Use Flask's validated Agent A identity instead of browser config.
    // textContent keeps the external response safely escaped as text.
    searchState.selectedCandidate = candidate;
    searchState.primaryAgent = data.primary_agent;
    searchState.capability = data.capability;
    searchState.capabilityLabel = data.capability_label;
    const primaryAgent = data.primary_agent;
    const agentName = data.agent_name || candidate.name;

    matchedPrimaryAgentName.textContent = primaryAgent.name;
    matchedAgentName.textContent = agentName;
    matchedPrimaryAvatarInitials.textContent = getInitials(primaryAgent.name);
    matchedPrimaryAvatarName.textContent = primaryAgent.name;
    matchedAgentAvatarInitials.textContent = getInitials(agentName);
    matchedAgentAvatarName.textContent = agentName;
    matchKicker.textContent = `${primaryAgent.name} completed the connection`;
    matchMessage.textContent =
      `${primaryAgent.name} contacted ${agentName} successfully through A2A.`;
    agentResponseTitle.textContent = `${agentName} replied`;
    matchedAgentAnswer.textContent = data.answer;
    tracePrimaryAgent.textContent = primaryAgent.name;
    traceProtocol.textContent = `A2A ${data.protocol_version || ""}`.trim();
    traceMatchedAgent.textContent = agentName;

    const responseIsLimited = data.answer_quality?.status === "limited";
    const hasAnotherCandidate =
      searchState.currentIndex + 1 < searchState.candidates.length;
    answerQualityWarning.hidden = !responseIsLimited;
    answerQualityWarning.textContent = responseIsLimited
      ? data.answer_quality.message ||
        "This response may not contain the requested details."
      : "";
    tryNextButton.hidden = !(responseIsLimited && hasAnotherCandidate);

    candidateView.hidden = true;
    matchView.hidden = false;
    matchView.focus();
  } catch (error) {
    // Leave the candidate visible so the user can retry a temporary ANS or A2A
    // failure without repeating the search.
    candidateControlStatus.textContent =
      error.message || "Unable to communicate with this agent.";
  } finally {
    setMatching(false);
  }
});

function buildDemoDeck(candidates) {
  // The PRD demo passes one candidate before finding the strongest match, so
  // arrange one real alternative before the top score. No records are invented
  // or removed.
  if (candidates.length < 2) {
    return candidates;
  }

  const sortedCandidates = [...candidates].sort(
    (first, second) =>
      second.compatibility.score - first.compatibility.score,
  );
  const strongestMatch = sortedCandidates.shift();

  return [sortedCandidates.shift(), strongestMatch, ...sortedCandidates];
}

function setCandidateControlsDisabled(isDisabled) {
  passButton.disabled = isDisabled;
  matchButton.disabled = isDisabled;
  editRequestButton.disabled = isDisabled;
}

function setMatching(isMatching) {
  // Disable Pass as well as Match so the selected card cannot change while
  // its A2A request is in flight.
  setCandidateControlsDisabled(isMatching);
  matchButtonLabel.textContent = isMatching ? "Connecting…" : "Match";
}

function getInitials(name) {
  // Two short initials distinguish Agent A and Agent B without needing remote
  // profile images, which ANS does not guarantee.
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

editRequestButton.addEventListener("click", showRequestView);
newSearchButton.addEventListener("click", showRequestView);
tryNextButton.addEventListener("click", showNextCandidate);

function showNextCandidate() {
  const nextIndex = searchState.currentIndex + 1;
  if (nextIndex >= searchState.candidates.length) {
    showRequestView();
    return;
  }

  searchState.currentIndex = nextIndex;
  renderCandidate(searchState.candidates[nextIndex]);
}

function showRequestView() {
  candidateView.hidden = true;
  matchView.hidden = true;
  requestView.hidden = false;
  searchStatus.hidden = true;
  searchState.primaryAgent = null;
  searchState.capability = null;
  searchState.capabilityLabel = null;
  searchState.candidates = [];
  searchState.currentIndex = 0;
  searchState.selectedCandidate = null;
  candidateControlStatus.textContent = "";
  answerQualityWarning.hidden = true;
  tryNextButton.hidden = true;
  setCandidateControlsDisabled(false);
  promptInput.focus();
}

async function readApiResponse(response, fallbackMessage) {
  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      response.ok
        ? "The service returned an unexpected response."
        : fallbackMessage,
    );
  }

  if (!response.ok) {
    throw new Error(data?.error?.message || fallbackMessage);
  }

  return data;
}
