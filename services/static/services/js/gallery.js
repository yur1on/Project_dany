(function () {
    const links = Array.from(document.querySelectorAll("[data-gallery-photo]"));
    const dialog = document.querySelector(".work-dialog");
    if (!dialog || !dialog.showModal) return;
    const picture = dialog.querySelector("img");
    const caption = dialog.querySelector("p");
    let index = 0;
    let opener = null;
    const render = () => {
        const link = links[index];
        picture.src = link.href;
        picture.alt = link.dataset.caption;
        caption.textContent = link.dataset.caption;
        dialog.querySelector(".work-dialog__nav").hidden = links.length < 2;
        if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            picture.getAnimations().forEach(animation => animation.cancel());
            picture.animate([{ opacity: .65 }, { opacity: 1 }], { duration: 180, easing: "ease-out" });
        }
    };
    links.forEach((link, position) => link.addEventListener("click", event => {
        event.preventDefault();
        opener = link;
        index = position;
        render();
        dialog.showModal();
    }));
    dialog.querySelector(".work-dialog__close").addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => { if (opener && opener.isConnected) opener.focus(); });
    dialog.querySelector("[data-prev]").addEventListener("click", () => { index = (index - 1 + links.length) % links.length; render(); });
    dialog.querySelector("[data-next]").addEventListener("click", () => { index = (index + 1) % links.length; render(); });
    dialog.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener("keydown", event => {
        if (event.key === "ArrowLeft") dialog.querySelector("[data-prev]").click();
        if (event.key === "ArrowRight") dialog.querySelector("[data-next]").click();
    });
})();
