// Small progressive enhancements; every page works without JavaScript.
document.addEventListener("submit", (e) => {
  const msg = e.target.getAttribute("data-confirm");
  if (msg && !window.confirm(msg)) e.preventDefault();
});
document.querySelectorAll("select[data-autosubmit]").forEach((s) =>
  s.addEventListener("change", () => s.form.submit()));
document.querySelectorAll("[data-select-all]").forEach((box) =>
  box.addEventListener("change", () => {
    document.querySelectorAll('input[name="ids"][form="bulk"]').forEach((c) => (c.checked = box.checked));
  }));
// Live character count. X counts each link as 23 characters; other platforms count characters.
document.querySelectorAll("textarea[data-limit]").forEach((t) => {
  const counter = t.parentElement.querySelector("[data-counter]");
  const limit = parseInt(t.dataset.limit, 10);
  const count = () => {
    let text = t.value;
    if (t.dataset.platform === "x") text = text.replace(/https?:\/\/\S+/g, "x".repeat(23));
    const n = [...text].length;
    if (counter) {
      counter.textContent = n;
      counter.classList.toggle("over", n > limit);
    }
  };
  t.addEventListener("input", count);
  count();
});
