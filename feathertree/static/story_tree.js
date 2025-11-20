document.addEventListener("DOMContentLoaded", function () {
    console.log("story_tree.js loaded");

    const toggles = document.querySelectorAll(".chapter-toggle");

    toggles.forEach((btn) => {
        const node = btn.closest(".chapter-tree-node");
        const childrenWrapper = node?.querySelector(".chapter-children");
        if (!childrenWrapper) return;

        // Default expanded/collapsed state
        const initiallyExpanded = btn.dataset.initialExpanded === "true";

        if (initiallyExpanded) {
            childrenWrapper.classList.remove("is-collapsed");
            childrenWrapper.classList.add("is-expanded");
            btn.classList.add("is-open");
        } else {
            childrenWrapper.classList.remove("is-expanded");
            childrenWrapper.classList.add("is-collapsed");
            btn.classList.remove("is-open");
        }

        // Toggle click event
        btn.addEventListener("click", () => {
            childrenWrapper.classList.toggle("is-expanded");
            childrenWrapper.classList.toggle("is-collapsed");
            btn.classList.toggle("is-open");
        });
    });
});
