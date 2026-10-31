(function () {
    const header = document.querySelector("[data-site-header]");
    const toggle = document.querySelector("[data-menu-toggle]");
    const menu = document.querySelector("[data-site-menu]");

    if (!toggle || !menu) {
        return;
    }

    const setMenuState = (isOpen) => {
        toggle.setAttribute("aria-expanded", String(isOpen));
        toggle.setAttribute("aria-label", isOpen ? "Закрыть меню" : "Открыть меню");
        menu.classList.toggle("is-open", isOpen);
        document.body.classList.toggle("is-menu-open", isOpen);
        menu.inert = window.matchMedia("(max-width: 1100px)").matches && !isOpen;
    };

    setMenuState(false);

    toggle.addEventListener("click", () => {
        setMenuState(toggle.getAttribute("aria-expanded") !== "true");
    });

    menu.addEventListener("click", (event) => {
        if (event.target.closest("a")) {
            setMenuState(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            if (toggle.getAttribute("aria-expanded") === "true") toggle.focus();
            setMenuState(false);
        }
    });

    window.matchMedia("(min-width: 1101px)").addEventListener("change", (event) => {
        setMenuState(false);
    });

    if (header) {
        const syncHeader = () => {
            header.classList.toggle("is-scrolled", window.scrollY > 8);
        };
        window.addEventListener("scroll", syncHeader, { passive: true });
        syncHeader();
    }
})();
