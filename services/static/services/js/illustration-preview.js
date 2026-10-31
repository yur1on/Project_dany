(function () {
    const select = document.querySelector('[name="illustration"]');
    const preview = document.querySelector('[data-illustration-preview]');
    const upload = document.querySelector('[data-photo-input]');
    if (!select || !preview) return;
    const allowed = new Set(['diagnostics', 'timing', 'exhaust', 'engine', 'suspension', 'steering', 'brakes', 'wheel']);
    let objectUrl;
    const update = () => {
        if (objectUrl) { URL.revokeObjectURL(objectUrl); objectUrl = null; }
        const file = upload && upload.files[0];
        if (file) {
            objectUrl = URL.createObjectURL(file);
            preview.src = objectUrl;
        } else if (select.value === 'photo' && preview.dataset.customUrl) {
            preview.src = preview.dataset.customUrl;
        } else {
            preview.src = preview.dataset.artBase + (allowed.has(select.value) ? select.value : 'generic') + '.svg';
        }
    };
    select.addEventListener('change', update);
    if (upload) upload.addEventListener('change', update);
})();
