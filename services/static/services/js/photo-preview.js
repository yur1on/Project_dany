(function () {
    const input = document.querySelector("[data-photo-input]");
    const preview = document.querySelector("[data-photo-preview]");
    if (!input || !preview) return;
    let url;
    input.addEventListener("change", () => {
        if (url) URL.revokeObjectURL(url);
        const file = input.files[0];
        preview.hidden = !file;
        if (file) {
            url = URL.createObjectURL(file);
            preview.src = url;
        }
    });
})();
