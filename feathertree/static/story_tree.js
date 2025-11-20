document.addEventListener("DOMContentLoaded", function () {
  console.log("story_tree.js loaded");

  const toggles = document.querySelectorAll(".chapter-toggle");

  toggles.forEach((btn) => {
    const node = btn.closest(".chapter-tree-node");
    const childrenWrapper = node?.querySelector(".chapter-children");
    if (!childrenWrapper) return;

    // Derive initial state from the classes on the <ul>
    const isExpanded = childrenWrapper.classList.contains("is-expanded");

    btn.setAttribute("aria-expanded", isExpanded ? "true" : "false");
    btn.classList.toggle("is-open", isExpanded);
  });
});

function toggleChapterChildren(chapterId) {
  const list = document.getElementById(`children-${chapterId}`);
  if (!list) return;

  const isExpanded = list.classList.contains("is-expanded");

  // Toggle classes on the children list
  list.classList.toggle("is-expanded", !isExpanded);
  list.classList.toggle("is-collapsed", isExpanded);

  // Toggle aria + open state on the button
  const toggle = document.getElementById(`chapter-toggle-${chapterId}`);
  if (toggle) {
    toggle.setAttribute("aria-expanded", !isExpanded ? "true" : "false");
    toggle.classList.toggle("is-open", !isExpanded);
  }
}
