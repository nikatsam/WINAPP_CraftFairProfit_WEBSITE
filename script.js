"use strict";

const menuButton = document.querySelector(".menu-toggle");
const primaryNav = document.querySelector(".primary-nav");

if (menuButton && primaryNav) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    menuButton.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
    primaryNav.classList.toggle("is-open", !isOpen);
  });

  primaryNav.addEventListener("click", (event) => {
    if (event.target instanceof Element && event.target.closest("a")) {
      menuButton.setAttribute("aria-expanded", "false");
      menuButton.setAttribute("aria-label", "Open navigation");
      primaryNav.classList.remove("is-open");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || menuButton.getAttribute("aria-expanded") !== "true") return;
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.setAttribute("aria-label", "Open navigation");
    primaryNav.classList.remove("is-open");
    menuButton.focus();
  });
}

const revealTargets = document.querySelectorAll(".process-card, .feature-row, .screenshot, .people-card, .guide-card");
if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  document.documentElement.classList.add("reveal-ready");
  const revealObserver = new IntersectionObserver((entries, observer) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.12 });
  revealTargets.forEach((element) => {
    element.classList.add("reveal");
    revealObserver.observe(element);
  });
}

const calculator = document.querySelector("#mini-calculator");
if (calculator) {
  const fields = Object.fromEntries(["units", "price", "cost", "expenses", "fee"].map((name) => [name, calculator.elements.namedItem(name)]));
  const output = {
    gross: document.querySelector("#calc-gross"),
    profit: document.querySelector("#calc-profit"),
    breakEven: document.querySelector("#calc-break"),
    message: document.querySelector("#calc-message")
  };
  const integerFormat = new Intl.NumberFormat("en-GB");
  const toPence = (value, maximumPounds) => BigInt(Math.round(Math.max(0, Math.min(maximumPounds, Number(value) || 0)) * 100));
  const formatPence = (pence) => {
    const isNegative = pence < 0n;
    const absolute = isNegative ? -pence : pence;
    const wholePounds = integerFormat.format(absolute / 100n);
    const pennies = (absolute % 100n).toString().padStart(2, "0");
    return `${isNegative ? "−" : ""}£${wholePounds}.${pennies}`;
  };

  const updateEstimate = () => {
    const units = Math.max(0, Math.min(100000, Math.floor(Number(fields.units.value) || 0)));
    const price = toPence(fields.price.value, 100000);
    const cost = toPence(fields.cost.value, 100000);
    const expenses = toPence(fields.expenses.value, 1000000);
    const quantity = BigInt(units);
    const feeBasisPoints = BigInt(Math.round(Math.max(0, Math.min(100, Number(fields.fee.value) || 0)) * 100));
    const gross = quantity * price;
    const cogs = quantity * cost;
    const fee = (gross * feeBasisPoints + 5000n) / 10000n;
    const contribution = gross - cogs - fee;
    const profit = contribution - expenses;

    output.gross.textContent = formatPence(gross);
    output.profit.textContent = formatPence(profit);
    if (expenses === 0n && contribution > 0n) {
      output.breakEven.textContent = formatPence(0n);
      output.message.textContent = "There are no event costs in this example, so estimated break-even revenue is £0.00.";
    } else if (gross <= 0n || contribution <= 0n) {
      output.breakEven.textContent = "Not available";
      output.message.textContent = "This planned mix has no positive contribution; estimated break-even revenue is not available.";
    } else {
      const numerator = expenses * gross;
      const breakEven = (numerator + contribution - 1n) / contribution;
      output.breakEven.textContent = formatPence(breakEven);
      output.message.textContent = "Approximate break-even at the same planned product mix and fee assumption.";
    }
  };

  calculator.addEventListener("input", updateEstimate);
  calculator.addEventListener("change", updateEstimate);
  updateEstimate();
}
