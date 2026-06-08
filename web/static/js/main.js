document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll("[data-expandable-card]");

    cards.forEach((card) => {
        const button = card.querySelector("[data-expand-button]");

        if (!button) {
            return;
        }

        button.addEventListener("click", () => {
            const isExpanded = card.classList.toggle("is-fullscreen");
            document.body.classList.toggle("has-fullscreen-card", isExpanded);
            button.setAttribute("aria-expanded", String(isExpanded));
            button.textContent = isExpanded ? "Exit fullscreen" : "Expand";
        });
    });
});
