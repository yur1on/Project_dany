(function () {
    const form = document.querySelector(".appointment-booking__form");
    if (!form) return;
    const button = form.querySelector('[type="submit"]');
    const originalText = button ? button.textContent : "";
    form.addEventListener("submit", (event) => {
        if (!button) return;
        if (button.disabled) { event.preventDefault(); return; }
        button.disabled = true;
        button.textContent = "Отправляем заявку…";
        button.setAttribute("aria-busy", "true");
    });
    window.addEventListener("pageshow", () => {
        if (!button) return;
        button.disabled = false;
        button.textContent = originalText;
        button.removeAttribute("aria-busy");
    });
})();
