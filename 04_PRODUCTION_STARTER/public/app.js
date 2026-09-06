/**
 * Phase 7 -- production data bootstrap.
 *
 * engine.js (renamed from the prototype's engine.prototype.js, content
 * unchanged) expects `window.GENEVIEVE_DATA` to already be set before it
 * runs, and to hold the exact { recipes, swapMap, ingredientUnitPairs }
 * shape the old bundled data.prototype.js provided -- see
 * src/api/catalogue.ts's module comment. This script is the only thing
 * that changed: instead of a static bundle (which would have shipped all
 * 800 recipes, including the 415 still HELD_FOR_KITCHEN_TEST, as a public
 * static asset regardless of any script tag referencing it), it fetches
 * the same shape from the Worker's /api/catalogue endpoint, which only
 * ever returns the Phase 2.8 launch-approved recipes.
 *
 * engine.js is loaded dynamically, after the fetch resolves, so its
 * top-level `rank()` call always has real data to work with.
 */
(() => {
  "use strict";

  function setStatus(message) {
    const status = document.getElementById("loadStatus");
    if (status) status.textContent = message;
  }

  function showError(message) {
    const status = document.getElementById("loadStatus");
    if (status) status.hidden = true;
    const error = document.getElementById("loadError");
    if (error) {
      error.textContent = message;
      error.hidden = false;
    }
  }

  function loadEngine() {
    const status = document.getElementById("loadStatus");
    if (status) status.hidden = true;
    const script = document.createElement("script");
    script.src = "engine.js";
    script.onerror = () => showError("The recipe engine failed to load. Please refresh the page.");
    document.body.appendChild(script);
  }

  setStatus("Loading the recipe catalogue…");

  fetch("/api/catalogue")
    .then((response) => {
      if (!response.ok) {
        throw new Error(`catalogue request failed with status ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (!data || !Array.isArray(data.recipes) || !data.swapMap || !Array.isArray(data.ingredientUnitPairs)) {
        throw new Error("catalogue response was missing an expected field");
      }
      window.GENEVIEVE_DATA = data;
      loadEngine();
    })
    .catch((error) => {
      console.error("catalogue_load_failed", error);
      showError(
        "We couldn't load the recipe catalogue right now. Please check your connection and refresh the page.",
      );
    });
})();
