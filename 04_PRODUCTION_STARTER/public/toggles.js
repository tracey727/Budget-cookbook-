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
})();
