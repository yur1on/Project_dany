(function () {
    const form = document.querySelector(".appointment-booking__form");
    const summary = document.querySelector(".appointment-booking__summary");

    if (!form || !summary) {
        return;
    }

    const fields = {
        name: form.querySelector("#id_name"),
        phone: form.querySelector("#id_phone"),
        carMake: form.querySelector("#id_car_make"),
        carModel: form.querySelector("#id_car_model"),
        carYear: form.querySelector("#id_car_year"),
        service: form.querySelector("#id_service_type"),
        comment: form.querySelector("#id_comment"),
    };

    const targets = {
        car: summary.querySelector('[data-appointment-summary="car"]'),
        service: summary.querySelector('[data-appointment-summary="service"]'),
        comment: summary.querySelector('[data-appointment-summary="comment"]'),
        contact: summary.querySelector('[data-appointment-summary="contact"]'),
    };

    const getValue = (field) => (field && field.value ? field.value.trim() : "");
    const getLabel = (field) => {
        if (!field) {
            return "";
        }

        if (field.tagName === "SELECT" && field.selectedOptions.length) {
            return field.selectedOptions[0].textContent.trim();
        }

        return getValue(field);
    };

    const updateSummary = () => {
        const carParts = [getValue(fields.carMake), getValue(fields.carModel)].filter(Boolean);
        const year = getValue(fields.carYear);
        const service = getLabel(fields.service);
        const comment = getValue(fields.comment);
        const name = getValue(fields.name);
        const phone = getValue(fields.phone);

        targets.car.textContent = carParts.length
            ? `${carParts.join(" ")}${year ? `, ${year}` : ""}`
            : "Марка, модель и год выпуска";

        targets.service.textContent = service || "Выберите услугу";
        targets.comment.textContent = comment || "Опишите симптомы, чтобы мастер быстрее понял задачу.";

        if (name && phone) {
            targets.contact.textContent = `${name}, ${phone}`;
        } else if (phone) {
            targets.contact.textContent = phone;
        } else if (name) {
            targets.contact.textContent = name;
        } else {
            targets.contact.textContent = "Мастер перезвонит по указанному номеру";
        }
    };

    Object.values(fields).forEach((field) => {
        if (!field) {
            return;
        }

        field.addEventListener("input", updateSummary);
        field.addEventListener("change", updateSummary);
    });

    updateSummary();
})();
