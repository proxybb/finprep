document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll("[data-expandable-card]");
    const tabGroups = document.querySelectorAll("[data-tabs]");
    const uploadForms = document.querySelectorAll("[data-upload-form]");

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

    tabGroups.forEach((group) => {
        const buttons = group.querySelectorAll("[data-tab-button]");
        const panels = group.querySelectorAll("[data-tab-panel]");

        buttons.forEach((button) => {
            button.addEventListener("click", () => {
                const target = button.dataset.tabButton;

                buttons.forEach((tabButton) => {
                    const isActive = tabButton === button;
                    tabButton.classList.toggle("is-active", isActive);
                    tabButton.setAttribute("aria-selected", String(isActive));
                });

                panels.forEach((panel) => {
                    const isActive = panel.dataset.tabPanel === target;
                    panel.classList.toggle("is-active", isActive);
                    panel.hidden = !isActive;
                });
            });
        });
    });

    uploadForms.forEach((form) => {
        const fileInputs = form.querySelectorAll("input[type='file']");
        const submitButton = form.querySelector("[data-submit-label]");

        fileInputs.forEach((input) => {
            input.addEventListener("change", () => {
                const filenameLabel = input
                    .closest(".upload-card__dropzone")
                    ?.querySelector("[data-selected-filename]");

                if (!filenameLabel) {
                    return;
                }

                filenameLabel.textContent = input.files?.[0]?.name || "No file selected.";
            });
        });

        form.addEventListener("submit", () => {
            if (!submitButton) {
                return;
            }

            submitButton.textContent = submitButton.dataset.submitLabel;
        });
    });
});
