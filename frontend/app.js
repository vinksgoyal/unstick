// For Render, replace this value with the deployed unstick-api URL.
const API_BASE_URL = window.API_URL || "";

const form = document.querySelector("#unstick-form");
const goal = document.querySelector("#goal");
const button = document.querySelector("#unstick");
const cards = document.querySelector("#cards");
const errorMessage = document.querySelector("#error");

form.addEventListener("submit", async (event) => {
  console.log("Submitting unstick request");
  event.preventDefault();
  button.disabled = true;
  button.textContent = "…";
  errorMessage.textContent = "";
  cards.textContent = "Finding one leaf...";
  const payload = {
    goal: goal.value,
    minutes: Number(document.querySelector("#minutes").value),
    energy: Number(document.querySelector("#energy").value),
    location: document.querySelector("#location").value,
    time: document.querySelector("#time").value || "day",
  };
  try {
    const response = await fetch(`${API_BASE_URL}/api/unstick`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The model could not respond.");
    cards.innerHTML = `<article class="card"><h2>Start here</h2><p>${escapeHtml(data.start_here.text)}</p></article><article class="card"><h2>If you have 15 minutes</h2><p>${escapeHtml(data.if_you_have_15.text)}</p></article><article class="card not-today"><h2>Not today</h2><p>${escapeHtml(data.not_today.message)}</p></article>`;
  } catch (error) {
    cards.textContent = "";
    errorMessage.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Show me one leaf";
  }
});
function escapeHtml(text) { const node = document.createElement("span"); node.textContent = text; return node.innerHTML; }
// Deliberately no progress bar, step counter, roadmap, or total-time estimate.
