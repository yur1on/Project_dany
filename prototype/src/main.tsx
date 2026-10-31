import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { ArrowDown, ArrowRight, ArrowUpRight, Menu, X, Wrench, Disc3, Activity, Cog } from "lucide-react";
import "./styles.css";

const djangoUrl = import.meta.env.VITE_DJANGO_URL || "http://127.0.0.1:8015";
const callback = `${djangoUrl}/appointment/`;
const services = [
  { title: "Диагностика", text: "Поиск неисправностей перед ремонтом и оценка состояния автомобиля.", icon: Activity },
  { title: "Ремонт подвески", text: "Ремонт ходовой части: рычаги, сайлентблоки, амортизаторы и другие узлы.", icon: Wrench },
  { title: "Тормозная система", text: "Обслуживание тормозов, замена колодок и дисков, ремонт суппортов.", icon: Disc3 },
  { title: "Двигатель и ГРМ", text: "Замена ГРМ, ремонт двигателя, прокладки ГБЦ и маслосъемных колпачков.", icon: Cog },
];
const links = [{ label: "Услуги", href: "#services" }, { label: "О мастерской", href: "#about" }, { label: "Работы", href: "#work" }, { label: "Контакты", href: "#contacts" }];

function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <>
      <header className="header">
        <div className="wrap header-inner">
          <a className="wordmark" href="#top" aria-label="AVTOMOD — на главную"><span>AVTO<span>MOD</span></span><small>АВТОСЕРВИС / ГОМЕЛЬ</small></a>
          <nav className={menuOpen ? "navigation is-open" : "navigation"} aria-label="Основная навигация" id="navigation">
            {links.map((link) => <a key={link.href} href={link.href} onClick={() => setMenuOpen(false)}>{link.label}</a>)}
            <a className="mobile-phone" href="tel:+375295325752">+375 29 532-57-52</a>
            <a className="mobile-action" href={callback}>Заказать звонок <ArrowUpRight size={17}/></a>
          </nav>
          <a className="header-phone" href="tel:+375295325752">+375 29 532-57-52</a>
          <a className="header-action" href={callback}>Заказать звонок <ArrowUpRight size={16}/></a>
          <button className="menu-button" type="button" aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"} aria-expanded={menuOpen} aria-controls="navigation" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X size={21}/> : <Menu size={21}/>}</button>
        </div>
      </header>
      <main id="top">
        <section className="hero">
          <div className="wrap hero-inner">
            <div className="hero-main">
              <div className="hero-topline"><span className="marker"/> <span>АВТОСЕРВИС В ГОМЕЛЕ</span><span className="hero-topline__rule"/></div>
              <p className="hero-brand">AVTOMOD <span>/ AUTO SERVICE</span></p>
              <h1>Вернем автомобилю<br/><span>уверенность</span><br/>на дороге<span className="hero-dot">.</span></h1>
              <p className="hero-description">Диагностика, обслуживание и ремонт. От замены масла до ремонта двигателя.</p>
              <div className="hero-actions"><a className="button button-accent" href={callback}>Заказать звонок <ArrowUpRight size={19}/></a><a className="hero-link" href="#services">Посмотреть услуги <ArrowDown size={16}/></a></div>
            </div>
            <div className="hero-aside" aria-label="Контакты мастерской">
              <p className="aside-label">ИНФОРМАЦИЯ / 01</p>
              <div><span>АДРЕС</span><strong>ул. Чонгарской дивизии,<br/>5/1</strong></div>
              <div><span>ГРАФИК РАБОТЫ</span><strong>Пн–Пт / 09:00–18:00</strong></div>
              <div><span>ТЕЛЕФОН</span><a href="tel:+375295325752">+375 29 532-57-52</a></div>
            </div>
          </div>
          <div className="hero-bottom wrap"><span>РЕМОНТ И ОБСЛУЖИВАНИЕ АВТОМОБИЛЕЙ</span><span>ГОМЕЛЬ / BY</span></div>
        </section>

        <section className="services section" id="services">
          <div className="wrap">
            <div className="section-heading">
              <div><p className="section-index"><span>01</span> / УСЛУГИ</p><h2>Поможем вашему<br/>автомобилю<span className="accent-dot">.</span></h2></div>
              <div className="heading-side"><p>Диагностика, обслуживание и ремонт вашего автомобиля.</p><a href={`${djangoUrl}/services/`}>Все услуги <ArrowUpRight size={17}/></a></div>
            </div>
            <div className="service-grid">{services.map((service, index) => {
              const Icon = service.icon;
              return <article className="service-card" key={service.title}><div className="service-card__top"><span>0{index + 1} / SERVICE</span><Icon size={23} strokeWidth={1.4}/></div><h3>{service.title}</h3><p>{service.text}</p><a href={`${djangoUrl}/services/`}>Подробнее <ArrowUpRight size={17}/></a></article>;
            })}</div>
          </div>
        </section>

        <section className="about section" id="about">
          <div className="wrap about-grid"><div><p className="section-index"><span>02</span> / О МАСТЕРСКОЙ</p><h2>Ремонт с понятным<br/>подходом<span className="accent-dot">.</span></h2></div><div className="about-copy"><p>Диагностика, обслуживание и ремонт. От замены масла до ремонта двигателя.</p><div className="about-row"><span>01</span><strong>Диагностика перед ремонтом</strong></div><div className="about-row"><span>02</span><strong>Согласование стоимости</strong></div></div></div>
        </section>

        <section className="work section" id="work">
          <div className="wrap">
            <div className="section-heading"><div><p className="section-index"><span>03</span> / НАШИ РАБОТЫ</p><h2>В мастерской<span className="accent-dot">.</span></h2></div><div className="heading-side"><p>Фотографии выполненных работ.</p><a href={`${djangoUrl}/gallery/`}>Открыть галерею <ArrowUpRight size={17}/></a></div></div>
            <div className="work-layout"><div className="work-image"><img src="/work.jpg" alt="Работа с двигателем в мастерской AVTOMOD" /></div><div className="work-caption"><p>AVTOMOD / WORKSHOP</p><strong>Ремонт и обслуживание автомобилей</strong><span>Фото из галереи мастерской</span><a href={`${djangoUrl}/gallery/`} aria-label="Открыть галерею" title="Открыть галерею"><ArrowUpRight size={21}/></a></div></div>
          </div>
        </section>

        <section className="contact" id="contacts"><div className="wrap contact-grid"><div><p className="section-index"><span>04</span> / КОНТАКТЫ</p><h2>Есть вопрос по<br/>автомобилю<span className="accent-dot">?</span></h2><p>Оставьте контакты, и мы перезвоним вам.</p><a className="button button-accent" href={callback}>Заказать звонок <ArrowUpRight size={19}/></a></div><div className="contact-details"><div><span>АДРЕС</span><strong>Гомель, ул. Чонгарской дивизии, 5/1</strong></div><div><span>ГРАФИК РАБОТЫ</span><strong>Пн–Пт: 09:00–18:00</strong></div><div><span>ТЕЛЕФОН</span><a href="tel:+375295325752">+375 29 532-57-52 <ArrowUpRight size={16}/></a></div><a className="map-link" href="https://yandex.ru/maps/-/CPhCbWPu" target="_blank" rel="noreferrer">Построить маршрут <ArrowRight size={17}/></a></div></div></section>
      </main>
      <footer className="footer"><div className="wrap footer-inner"><div><a className="footer-brand" href="#top">AVTO<span>MOD</span></a><p>Ремонт и обслуживание автомобилей.</p></div><div className="footer-links">{links.map(link=><a key={link.href} href={link.href}>{link.label}</a>)}</div><div className="footer-end"><span>© {new Date().getFullYear()} AVTOMOD</span><span>ПРОТОТИП ДИЗАЙНА</span></div></div></footer>
    </>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
