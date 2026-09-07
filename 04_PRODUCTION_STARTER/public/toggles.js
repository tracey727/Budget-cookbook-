(() => {
  "use strict";

  document.querySelectorAll(".panel-head").forEach((head) => {
    const btn = head.querySelector(".toggle-btn");
    if (!btn) return;
    const body = document.getElementById(btn.getAttribute("aria-controls"));
    if (!body) return;
    head.addEventListener("click", () => {
      const collapsed = body.classList.toggle("collapsed");
      btn.setAttribute("aria-expanded", String(!collapsed));
      btn.textContent = collapsed ? "Show ▸" : "Hide ▾";
    });
  });

  const rankBtn = document.getElementById("rankBtn");
  const resultsSection = document.querySelector(".results-panel");
  if (rankBtn && resultsSection) {
    rankBtn.addEventListener("click", () => {
      // Deferred so this runs after engine.js's own click handler has
      // finished re-rendering #results for the click that triggered this.
      setTimeout(() => {
        const resultsBody = document.getElementById("resultsBody");
        const resultsToggle = resultsSection.querySelector(".toggle-btn");
        if (resultsBody && resultsBody.classList.contains("collapsed")) {
          resultsBody.classList.remove("collapsed");
          if (resultsToggle) {
            resultsToggle.setAttribute("aria-expanded", "true");
            resultsToggle.textContent = "Hide ▾";
          }
        }
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 50);
    });
  }
})();
