"use strict";

// Cache the page elements once so we can reuse them during every search.
const searchForm = document.querySelector("#search-form");
const promptInput = document.querySelector("#agent-request");
const findMatchButton = document.querySelector("#find-match-button");
const buttonLabel = findMatchButton.querySelector(".button-label");
const searchStatus = document.querySelector("#search-status");
const requestView = document.querySelector("#request-view");
const candidateView = document.querySelector("#candidate-view");
const candidateName = document.querySelector("#candidate-name");
const candidateDescription = document.querySelector("#candidate-description");
const candidateScore = document.querySelector("#candidate-score");
const candidateStatus = document.querySelector("#candidate-status");
const candidateSkillList = document.querySelector("#candidate-skill-list");
const candidateAnsName = document.querySelector("#candidate-ans-name");
const candidatePosition = document.querySelector("#candidate-position");
const passButton = document.querySelector("#pass-button");
const matchButton = document.querySelector("#match-button");
const candidateControlStatus = document.querySelector(
  "#candidate-control-status",
);
const matchView = document.querySelector("#match-view");
const matchedAgentName = document.querySelector("#matched-agent-name");

// Keep the successful response in memory. The next frontend step will use
// these candidates to build the swipeable agent cards.
const searchState = {
  capability: null,
  candidates: [],
  currentIndex: 0,
  selectedCandidate: null,
};

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
  showStatus("Searching ANS for compatible agents…", "loading");

  try {
    // Send the prompt as JSON to the Flask route implemented in app.py.
    const response = await fetch("/api/search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    });

    const data = await response.json();

    // Flask returns errors in a consistent {error: {message: ...}} shape.
    if (!response.ok) {
      throw new Error(data.error?.message || "The agent search failed.");
    }

    searchState.capability = data.capability;
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
      `${count} compatible ${noun} discovered through ANS.`,
      "success",
    );

    // This step displays only the first candidate. Pass and Match controls will
    // move through the remaining in-memory candidates in the next feature.
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
  candidateAnsName.textContent = candidate.ans_name;
  candidatePosition.textContent = `${searchState.currentIndex + 1} of ${searchState.candidates.length}`;
  candidateControlStatus.textContent = "";

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

matchButton.addEventListener("click", () => {
  const candidate = searchState.candidates[searchState.currentIndex];
  searchState.selectedCandidate = candidate;

  matchedAgentName.textContent = candidate.name;
  candidateView.hidden = true;
  matchView.hidden = false;
  matchView.focus();
});

function buildDemoDeck(candidates) {
  // The PRD demo passes one candidate before finding the strongest match. ANS
  // ranks HaloHeat first, so arrange one real alternative before the highest-
  // scoring result. No records are invented or removed.
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
}
