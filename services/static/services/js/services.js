const servicesPage = document.querySelector(".services-page");

if (servicesPage) {
    const searchInput = servicesPage.querySelector("#serviceSearch");
    const filterButtons = [...servicesPage.querySelectorAll("[data-service-filter]")];
    const rows = [...servicesPage.querySelectorAll("[data-service-row]")];
    const emptyState = servicesPage.querySelector("[data-services-empty]");
    const countLabel = servicesPage.querySelector("[data-services-count]");
    let activeFilter = "all";
    let galleryItems = [];
    let galleryIndex = 0;

    const normalize = (value) => value.toLowerCase().trim();

    const lightbox = document.createElement("div");
    lightbox.className = "gallery-lightbox";
    lightbox.hidden = true;
    lightbox.innerHTML = `
        <div class="gallery-lightbox__dialog" role="dialog" aria-modal="true" aria-label="Галерея услуги">
            <button class="gallery-lightbox__close" type="button" aria-label="Закрыть">×</button>
            <button class="gallery-lightbox__nav gallery-lightbox__nav--prev" type="button" aria-label="Предыдущее фото">‹</button>
            <div class="gallery-lightbox__image-wrap">
                <img class="gallery-lightbox__image" src="" alt="">
            </div>
            <button class="gallery-lightbox__nav gallery-lightbox__nav--next" type="button" aria-label="Следующее фото">›</button>
            <p class="gallery-lightbox__caption"></p>
        </div>
    `;
    document.body.appendChild(lightbox);

    const lightboxImage = lightbox.querySelector(".gallery-lightbox__image");
    const lightboxCaption = lightbox.querySelector(".gallery-lightbox__caption");
    const previousButton = lightbox.querySelector(".gallery-lightbox__nav--prev");
    const nextButton = lightbox.querySelector(".gallery-lightbox__nav--next");

    const renderLightbox = () => {
        const item = galleryItems[galleryIndex];
        if (!item) return;

        lightboxImage.src = item.src;
        lightboxImage.alt = item.caption;
        lightboxCaption.textContent = item.caption;
        const hasMultipleItems = galleryItems.length > 1;
        previousButton.hidden = !hasMultipleItems;
        nextButton.hidden = !hasMultipleItems;
    };

    const openLightbox = (items, index) => {
        galleryItems = items;
        galleryIndex = index;
        renderLightbox();
        lightbox.hidden = false;
        document.body.style.overflow = "hidden";
    };

    const closeLightbox = () => {
        lightbox.hidden = true;
        lightboxImage.src = "";
        document.body.style.overflow = "";
    };

    const showRelativeImage = (step) => {
        if (!galleryItems.length) return;

        galleryIndex = (galleryIndex + step + galleryItems.length) % galleryItems.length;
        renderLightbox();
    };

    const setDetails = (row, open, immediate = false) => {
        const toggle = row.querySelector("[data-toggle-details]");
        const details = row.querySelector(".service-row__details");
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        details.getAnimations().forEach((animation) => animation.cancel());
        toggle.setAttribute("aria-expanded", String(open));
        toggle.textContent = open ? "Свернуть" : "Подробнее";
        row.classList.toggle("is-expanded", open);
        if (immediate || reduced) {
            details.hidden = !open;
            return;
        }
        if (open) {
            details.hidden = false;
            details.animate([{ height: "0px", opacity: 0, overflow: "hidden" }, { height: `${details.scrollHeight}px`, opacity: 1, overflow: "hidden" }], { duration: 220, easing: "ease-out" });
        } else if (!details.hidden) {
            const animation = details.animate([{ height: `${details.scrollHeight}px`, opacity: 1, overflow: "hidden" }, { height: "0px", opacity: 0, overflow: "hidden" }], { duration: 220, easing: "ease-in" });
            animation.finished.then(() => { if (toggle.getAttribute("aria-expanded") === "false") details.hidden = true; }).catch(() => {});
        }
    };

    const updateRows = () => {
        const query = normalize(searchInput.value);
        let visibleCount = 0;

        rows.forEach((row) => {
            const matchesFilter = activeFilter === "all" || row.dataset.category === activeFilter;
            const matchesQuery = normalize(row.dataset.search || "").includes(query);
            const isVisible = matchesFilter && matchesQuery;
            if (!isVisible && row.querySelector("[data-toggle-details]").getAttribute("aria-expanded") === "true") {
                setDetails(row, false, true);
            }
            row.hidden = !isVisible;
            if (isVisible) visibleCount += 1;
        });

        if (emptyState) {
            emptyState.hidden = visibleCount !== 0;
        }
        if (countLabel) {
            const lastTwo = visibleCount % 100;
            const last = visibleCount % 10;
            const word = lastTwo >= 11 && lastTwo <= 14 ? "услуг" : last === 1 ? "услуга" : last >= 2 && last <= 4 ? "услуги" : "услуг";
            countLabel.textContent = `${visibleCount} ${word} ${word === "услуга" ? "доступна" : word === "услуги" ? "доступны" : "доступно"}`;
        }
    };

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeFilter = button.dataset.serviceFilter;
            filterButtons.forEach((item) => item.classList.toggle("is-active", item === button));
            updateRows();
        });
    });

    servicesPage.addEventListener("click", (event) => {
        const toggle = event.target.closest("[data-toggle-details]");
        const galleryButton = event.target.closest("[data-gallery-image]");

        if (galleryButton) {
            const gallery = galleryButton.closest(".service-gallery");
            const buttons = [...gallery.querySelectorAll("[data-gallery-image]")];
            const items = buttons.map((button) => ({
                src: button.dataset.galleryImage,
                caption: button.dataset.galleryCaption || "Фото услуги",
            }));
            openLightbox(items, buttons.indexOf(galleryButton));
            return;
        }

        if (!toggle) return;

        const row = toggle.closest("[data-service-row]");
        const shouldOpen = toggle.getAttribute("aria-expanded") !== "true";
        if (shouldOpen) {
            rows.forEach((other) => {
                if (other !== row && other.querySelector("[data-toggle-details]").getAttribute("aria-expanded") === "true") setDetails(other, false);
            });
        }
        setDetails(row, shouldOpen);
    });

    lightbox.addEventListener("click", (event) => {
        if (event.target === lightbox || event.target.closest(".gallery-lightbox__close")) {
            closeLightbox();
            return;
        }

        if (event.target.closest(".gallery-lightbox__nav--prev")) {
            showRelativeImage(-1);
            return;
        }

        if (event.target.closest(".gallery-lightbox__nav--next")) {
            showRelativeImage(1);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (lightbox.hidden) return;

        if (event.key === "Escape") {
            closeLightbox();
        }
        if (event.key === "ArrowLeft") {
            showRelativeImage(-1);
        }
        if (event.key === "ArrowRight") {
            showRelativeImage(1);
        }
    });

    searchInput.addEventListener("input", updateRows);
    updateRows();
}
