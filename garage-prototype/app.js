const toggle = document.querySelector('.menu-toggle');
const menu = document.querySelector('.navigation');

function setMenu(open) {
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
  menu.classList.toggle('is-open', open);
}

toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
menu.addEventListener('click', (event) => { if (event.target.closest('a')) setMenu(false); });
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
    setMenu(false);
    toggle.focus();
  }
});
window.matchMedia('(min-width: 901px)').addEventListener('change', (event) => { if (event.matches) setMenu(false); });

const search = document.querySelector('[data-service-search]');
if (search) {
  const services = [...document.querySelectorAll('[data-service]')];
  const empty = document.querySelector('[data-search-empty]');
  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase('ru');
    let visible = 0;
    services.forEach((service) => {
      const matches = service.textContent.toLocaleLowerCase('ru').includes(query);
      service.hidden = !matches;
      if (matches) visible += 1;
    });
    empty.hidden = visible !== 0;
  });
}
