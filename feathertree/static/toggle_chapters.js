function toggleChapters(storyId) {
    const list = document.getElementById(`chapters-${storyId}`);
    if (!list) return;

    const opened = list.classList.toggle("open");

    const toggle = document.getElementById(`story-toggle-${storyId}`);
    if (toggle) {
        toggle.setAttribute("aria-expanded", opened ? "true" : "false");
        const icon = toggle.querySelector(".story-card-toggle-icon");
        if (icon) {
            icon.classList.toggle("is-open", opened);
        }
    }
}
