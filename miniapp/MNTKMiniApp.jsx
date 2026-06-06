import React, { useState, useMemo } from "react";
import {
  Search, Bookmark, Share2, ArrowLeft, ExternalLink,
  Newspaper, Flame, Send, Sparkles, Crown, Check, Lightbulb,
} from "lucide-react";

const C = {
  paper: "#FBFAF6",
  card: "#FFFFFF",
  ink: "#1A1A16",
  muted: "#6B6A62",
  faint: "#9D9B90",
  line: "rgba(26,26,22,0.08)",
  lineSoft: "rgba(26,26,22,0.05)",
  emerald: "#0F8A63",
  amber: "#B0700F",
  rose: "#B23A53",
  link: "#0F6E56",
  gold: "#9C7A2C",
};

const EVID = {
  meta: { label: "Высокий · мета-анализ", dot: C.emerald },
  rct: { label: "Высокий · РКИ", dot: C.emerald },
  observational: { label: "Средний · наблюдательное", dot: C.amber },
  case: { label: "Низкий · клинический случай", dot: C.amber },
  preprint: { label: "Препринт · не рецензирован", dot: C.amber },
};

const ARTICLES = [
  {
    id: 1, evidence: "rct", topic: "cataract", cited: 38, day: true,
    ruTitle: "Долгосрочная стабильность ИОЛ после фемто-факоэмульсификации",
    origTitle: "Long-term IOL stability after femtosecond phacoemulsification",
    summary: "РКИ на 240 глазах: смещение ИОЛ через 24 мес значимо ниже, чем при ручной технике.",
    abstract: "Рандомизированное исследование на 240 глазах сравнило фемто-ассистированную и ручную факоэмульсификацию. Через 24 месяца децентрация ИОЛ в фемто-группе была значимо ниже (p<0.01) при сопоставимой остроте зрения. Авторы отмечают преимущество для премиальных ИОЛ, чувствительных к положению.",
    journal: "Ophthalmology", year: "2025", source: "PubMed", authors: "Chen L. et al.",
  },
  {
    id: 2, evidence: "preprint", topic: "kerato", cited: 3, day: true,
    ruTitle: "Новый вискоэластик для профилактики отёка роговицы",
    origTitle: "Novel viscoelastic for corneal edema prevention",
    summary: "Пилотная серия, 18 пациентов. Требует подтверждения на большей выборке.",
    abstract: "Пилотное проспективное исследование 18 пациентов оценило новый когезивный вискоэластик. Отмечено снижение центральной толщины роговицы в первые сутки после операции. Малая выборка и отсутствие контроля ограничивают выводы; нужны рандомизированные данные.",
    journal: "medRxiv", year: "2025", source: "Crossref", authors: "Ivanov A. et al.",
  },
  {
    id: 3, evidence: "meta", topic: "refractive", cited: 51, day: true,
    ruTitle: "Сухой глаз после SMILE и femto-LASIK: сравнение",
    origTitle: "Dry eye after SMILE vs femto-LASIK: a meta-analysis",
    summary: "Меньшее снижение слёзопродукции после SMILE в первые 3 мес; к 6 мес различия сглаживаются.",
    abstract: "Мета-анализ 14 исследований показал меньшее снижение слёзопродукции после SMILE в ранний период за счёт сохранности роговичных нервов. К 6 месяцам различия между методами становятся статистически незначимыми.",
    journal: "J Refract Surg", year: "2025", source: "Europe PMC", authors: "Park S. et al.",
  },
  {
    id: 4, evidence: "rct", topic: "glaucoma", cited: 29, day: true,
    ruTitle: "Микроинвазивная хирургия глаукомы при катаракте: 3 года наблюдения",
    origTitle: "MIGS combined with cataract surgery: 3-year outcomes",
    summary: "Комбинированная MIGS+факоэмульсификация снижает ВГД и потребность в каплях стабильно на 3 года.",
    abstract: "Многоцентровое РКИ (312 глаз) показало устойчивое снижение ВГД и уменьшение числа гипотензивных препаратов через 36 месяцев в группе MIGS+факоэмульсификация против изолированной факоэмульсификации.",
    journal: "JAMA Ophthalmology", year: "2025", source: "PubMed", authors: "Müller K. et al.",
  },
  {
    id: 5, evidence: "observational", topic: "vitreo", cited: 12, day: true,
    ruTitle: "Исходы витрэктомии 27G при пролиферативной диабетической ретинопатии",
    origTitle: "27G vitrectomy outcomes in proliferative diabetic retinopathy",
    summary: "Когорта 96 глаз: меньшая травматичность, сопоставимая частота повторных вмешательств.",
    abstract: "Проспективная когорта 96 глаз оценила витрэктомию 27G. Отмечены меньшее время операции и послеоперационный дискомфорт при сопоставимой с 25G частотой реопераций. Дизайн наблюдательный, без рандомизации.",
    journal: "Retina", year: "2025", source: "Europe PMC", authors: "Tanaka H. et al.",
  },
  {
    id: 6, evidence: "case", topic: "kerato", cited: 5, day: false,
    ruTitle: "DMEK после неудачной сквозной кератопластики: серия случаев",
    origTitle: "DMEK after failed penetrating keratoplasty: a case series",
    summary: "8 глаз: восстановление прозрачности роговицы при тщательном отборе пациентов.",
    abstract: "Серия из 8 глаз описывает DMEK у пациентов с декомпенсацией трансплантата после сквозной кератопластики. Достигнуто восстановление прозрачности в большинстве случаев; уровень доказательности низкий из-за дизайна.",
    journal: "Cornea", year: "2025", source: "PubMed", authors: "Rossi G. et al.",
  },
];

const TOPICS = [
  { key: "all", label: "Сегодня" },
  { key: "hot", label: "Горячее" },
  { key: "cataract", label: "Катаракта" },
  { key: "glaucoma", label: "Глаукома" },
  { key: "refractive", label: "Рефракционная" },
  { key: "vitreo", label: "Витреоретина" },
  { key: "kerato", label: "Кератопластика" },
];

const font = {
  serif: "'Newsreader', Georgia, serif",
  sans: "'Plus Jakarta Sans', system-ui, sans-serif",
};

function EvidenceTag({ evidence }) {
  const e = EVID[evidence];
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: C.muted, fontFamily: font.sans }}>
      <span style={{ width: 7, height: 7, borderRadius: 999, background: e.dot, flexShrink: 0 }} />
      {e.label}
    </span>
  );
}

function Card({ a, idx, saved, onToggle, onOpen }) {
  return (
    <article
      onClick={() => onOpen(a)}
      style={{
        background: C.card, border: `0.5px solid ${C.line}`, borderRadius: 18,
        padding: "15px 16px", cursor: "pointer",
        animation: "fadeUp .5s ease both", animationDelay: `${idx * 60}ms`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <EvidenceTag evidence={a.evidence} />
        <span style={{ display: "flex", gap: 14, color: C.faint }}>
          <Bookmark
            size={19} onClick={(e) => { e.stopPropagation(); onToggle(a.id); }}
            fill={saved ? C.ink : "none"} color={saved ? C.ink : C.faint}
          />
          <Share2 size={19} onClick={(e) => e.stopPropagation()} />
        </span>
      </div>
      <h3 style={{ fontFamily: font.serif, fontSize: 17, fontWeight: 500, lineHeight: 1.32, margin: "0 0 6px", color: C.ink, letterSpacing: "-0.01em" }}>
        {a.ruTitle}
      </h3>
      <p style={{ fontFamily: font.sans, fontSize: 13, color: C.muted, lineHeight: 1.5, margin: "0 0 12px" }}>
        {a.summary}
      </p>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontFamily: font.sans, fontSize: 11, background: C.paper, color: C.muted, borderRadius: 6, padding: "3px 8px", border: `0.5px solid ${C.lineSoft}` }}>{a.journal}</span>
        <span style={{ fontFamily: font.sans, fontSize: 12, color: C.faint }}>{a.year} · {a.source}</span>
      </div>
    </article>
  );
}

function Detail({ a, saved, onToggle, onBack }) {
  const e = EVID[a.evidence];
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: C.card }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 18px", borderBottom: `0.5px solid ${C.line}` }}>
        <ArrowLeft size={20} color={C.muted} onClick={onBack} style={{ cursor: "pointer" }} />
        <span style={{ display: "flex", gap: 16, color: C.muted }}>
          <Bookmark size={20} fill={saved ? C.ink : "none"} color={saved ? C.ink : C.muted} onClick={() => onToggle(a.id)} style={{ cursor: "pointer" }} />
          <Share2 size={20} style={{ cursor: "pointer" }} />
        </span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "18px" }}>
        <div style={{ marginBottom: 12 }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, color: C.muted, fontFamily: font.sans }}>
            <span style={{ width: 7, height: 7, borderRadius: 999, background: e.dot }} />
            {e.label.replace("·", "уровень доказательности ·")}
          </span>
        </div>
        <h2 style={{ fontFamily: font.serif, fontSize: 21, fontWeight: 500, lineHeight: 1.28, margin: "0 0 4px", color: C.ink, letterSpacing: "-0.015em" }}>{a.ruTitle}</h2>
        <p style={{ fontFamily: font.sans, fontSize: 13, color: C.faint, margin: "0 0 16px" }}>{a.origTitle}</p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 18 }}>
          {[a.journal, a.year, a.source, a.authors].map((t) => (
            <span key={t} style={{ fontFamily: font.sans, fontSize: 11, background: C.paper, color: C.muted, borderRadius: 6, padding: "4px 9px", border: `0.5px solid ${C.lineSoft}` }}>{t}</span>
          ))}
        </div>
        <p style={{ fontFamily: font.sans, fontSize: 13, fontWeight: 500, color: C.muted, margin: "0 0 6px" }}>Кратко</p>
        <p style={{ fontFamily: font.sans, fontSize: 14, lineHeight: 1.65, color: C.ink, margin: "0 0 20px" }}>{a.abstract}</p>
        <a href="#" onClick={(e2) => e2.preventDefault()} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontFamily: font.sans, fontSize: 14, color: C.link, textDecoration: "none", border: `0.5px solid ${C.line}`, borderRadius: 12, padding: "11px" }}>
          Открыть оригинал <ExternalLink size={16} />
        </a>
      </div>
    </div>
  );
}

function SearchView() {
  const [q, setQ] = useState("");
  const [asked, setAsked] = useState(null);
  const sources = useMemo(() => ARTICLES.slice(0, 3), []);
  const ask = () => setAsked(q || "demo");
  return (
    <div style={{ padding: "18px 16px" }}>
      <h1 style={{ fontFamily: font.serif, fontSize: 22, fontWeight: 500, margin: "0 0 4px", color: C.ink, letterSpacing: "-0.015em" }}>Спросить библиотеку</h1>
      <p style={{ fontFamily: font.sans, fontSize: 13, color: C.muted, margin: "0 0 16px" }}>Ответ только по проверенным источникам, со ссылками. Сейчас — бесплатно и без лимитов.</p>
      <div style={{ display: "flex", gap: 8, marginBottom: 18 }}>
        <input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="Напр.: SMILE или femto-LASIK при сухом глазу?"
          style={{ flex: 1, fontFamily: font.sans, fontSize: 14, padding: "11px 14px", borderRadius: 12, border: `0.5px solid ${C.line}`, background: C.card, color: C.ink, outline: "none" }}
        />
        <button onClick={ask} style={{ background: C.ink, color: "#fff", border: "none", borderRadius: 12, width: 46, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
          <Send size={17} />
        </button>
      </div>
      {asked && (
        <div style={{ background: C.card, border: `0.5px solid ${C.line}`, borderRadius: 16, padding: 16, animation: "fadeUp .4s ease both" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 10 }}>
            <Sparkles size={15} color={C.link} />
            <span style={{ fontFamily: font.sans, fontSize: 12, color: C.muted }}>Ответ по базе</span>
          </div>
          <p style={{ fontFamily: font.sans, fontSize: 14, lineHeight: 1.65, color: C.ink, margin: "0 0 14px" }}>
            По мета-анализу 2025 г. SMILE даёт меньшее снижение слёзопродукции в первые 3 месяца за счёт сохранности роговичных нервов <b style={{ color: C.link, fontWeight: 500 }}>[1]</b>. К 6 месяцам различия сглаживаются <b style={{ color: C.link, fontWeight: 500 }}>[2]</b>. РКИ подтверждает более быстрое восстановление чувствительности роговицы после SMILE <b style={{ color: C.link, fontWeight: 500 }}>[3]</b>.
          </p>
          <p style={{ fontFamily: font.sans, fontSize: 12, color: C.muted, margin: "0 0 6px" }}>Источники</p>
          {sources.map((s, i) => (
            <div key={s.id} style={{ display: "flex", gap: 8, padding: "6px 0", borderTop: i ? `0.5px solid ${C.lineSoft}` : "none" }}>
              <span style={{ fontFamily: font.sans, fontSize: 13, color: C.link, fontWeight: 500 }}>[{i + 1}]</span>
              <span style={{ fontFamily: font.sans, fontSize: 13, color: C.ink, lineHeight: 1.4 }}>{s.ruTitle} <span style={{ color: C.faint }}>— {s.journal}, {s.year}</span></span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Premium({ onBack }) {
  const feats = [
    ["Глубокие ответы и мини-обзоры", "Синтез по нескольким статьям и обзор темы за год."],
    ["Вопросы по полному тексту", "Анализ полной статьи и загрузка своих PDF в библиотеку."],
    ["Оповещения по темам", "Мгновенный пинг о новых РКИ по твоим темам."],
    ["Экспорт и цитирование", "PDF, BibTeX/RIS для статей и подборок."],
    ["История и подборки", "Сохранение диалогов и папки для статей."],
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: C.card }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "16px 18px", borderBottom: `0.5px solid ${C.line}` }}>
        <ArrowLeft size={20} color={C.muted} onClick={onBack} style={{ cursor: "pointer" }} />
        <span style={{ fontFamily: font.sans, fontSize: 15, fontWeight: 500, color: C.ink }}>О боте</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
        <div style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 44, height: 44, borderRadius: 12, background: "rgba(15,138,99,0.1)", marginBottom: 14 }}>
          <Check size={22} color={C.emerald} />
        </div>
        <h2 style={{ fontFamily: font.serif, fontSize: 24, fontWeight: 500, margin: "0 0 6px", color: C.ink, letterSpacing: "-0.015em" }}>Сейчас всё бесплатно</h2>
        <p style={{ fontFamily: font.sans, fontSize: 14, color: C.muted, lineHeight: 1.55, margin: "0 0 22px" }}>Бот работает без лимитов: ежедневный дайджест, «Факт дня» и вопросы к библиотеке. Платные тарифы появятся позже, когда наберём аудиторию.</p>

        <div style={{ display: "inline-flex", alignItems: "center", gap: 6, marginBottom: 14 }}>
          <Crown size={14} color={C.gold} />
          <span style={{ fontFamily: font.sans, fontSize: 12, color: C.gold, fontWeight: 600, letterSpacing: "0.04em" }}>ПОЯВИТСЯ ПОЗЖЕ</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {feats.map(([t, d]) => (
            <div key={t} style={{ display: "flex", gap: 11 }}>
              <Crown size={16} color={C.gold} style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <p style={{ fontFamily: font.sans, fontSize: 14, fontWeight: 500, color: C.ink, margin: 0 }}>{t}</p>
                <p style={{ fontFamily: font.sans, fontSize: 13, color: C.muted, margin: "2px 0 0", lineHeight: 1.45 }}>{d}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ padding: 16, borderTop: `0.5px solid ${C.line}`, background: C.card }}>
        <a href="https://t.me/codexa_support" target="_blank" rel="noreferrer" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, width: "100%", boxSizing: "border-box", background: C.ink, color: "#fff", borderRadius: 14, padding: "14px", fontFamily: font.sans, fontSize: 15, fontWeight: 500, textDecoration: "none" }}>
          <Send size={16} /> Вопросы и предложения
        </a>
        <p style={{ fontFamily: font.sans, fontSize: 12, color: C.faint, textAlign: "center", margin: "10px 0 0" }}>Разработчик · <a href="https://t.me/codexa_support" target="_blank" rel="noreferrer" style={{ color: C.link, textDecoration: "none" }}>@codexa_support</a></p>
      </div>
    </div>
  );
}

function FactCard() {
  return (
    <div style={{ background: "#FBF6EA", border: "0.5px solid rgba(156,122,44,0.25)", borderRadius: 18, padding: "15px 16px", animation: "fadeUp .5s ease both" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
        <Lightbulb size={15} color={C.gold} />
        <span style={{ fontFamily: font.sans, fontSize: 11, color: C.gold, fontWeight: 600, letterSpacing: "0.06em" }}>ФАКТ ДНЯ</span>
      </div>
      <p style={{ fontFamily: font.serif, fontSize: 16, lineHeight: 1.42, color: C.ink, margin: "0 0 7px" }}>
        Интракамеральный моксифлоксацин в конце факоэмульсификации снижает риск эндофтальмита в несколько раз по данным крупных регистров.
      </p>
      <span style={{ fontFamily: font.sans, fontSize: 12, color: C.muted }}>ESCRS Endophthalmitis Study · регистровые данные</span>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("feed");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState(null);
  const [saved, setSaved] = useState(() => new Set());
  const [showPremium, setShowPremium] = useState(false);

  const toggle = (id) =>
    setSaved((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  const feed = useMemo(() => {
    if (filter === "hot") return [...ARTICLES].sort((a, b) => b.cited - a.cited);
    if (filter === "all") return ARTICLES;
    return ARTICLES.filter((a) => a.topic === filter);
  }, [filter]);

  const savedList = ARTICLES.filter((a) => saved.has(a.id));

  const tabs = [
    { key: "feed", label: "Лента", icon: Newspaper },
    { key: "hot", label: "Горячее", icon: Flame },
    { key: "search", label: "Поиск", icon: Search },
    { key: "saved", label: "Моё", icon: Bookmark },
  ];

  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "20px 12px", background: "#EFEDE6", minHeight: "100%", fontFamily: font.sans }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');
        @keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
        *{box-sizing:border-box}::-webkit-scrollbar{width:0}`}</style>

      <div style={{ width: "100%", maxWidth: 412, height: 740, background: C.paper, borderRadius: 28, border: `0.5px solid ${C.line}`, overflow: "hidden", display: "flex", flexDirection: "column", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}>

        {showPremium ? (
          <Premium onBack={() => setShowPremium(false)} />
        ) : selected ? (
          <Detail a={selected} saved={saved.has(selected.id)} onToggle={toggle} onBack={() => setSelected(null)} />
        ) : (
          <>
            <header style={{ padding: "18px 16px 12px", flexShrink: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h1 style={{ fontFamily: font.serif, fontSize: 21, fontWeight: 500, margin: 0, color: C.ink, letterSpacing: "-0.015em" }}>
                    {tab === "saved" ? "Сохранённое" : tab === "search" ? "Поиск" : "Микрохирургия глаза"}
                  </h1>
                  {tab === "feed" && <p style={{ fontFamily: font.sans, fontSize: 13, color: C.muted, margin: "3px 0 0" }}>Сегодня · 5 новых · 71 отсеяно</p>}
                  {tab === "hot" && <p style={{ fontFamily: font.sans, fontSize: 13, color: C.muted, margin: "3px 0 0" }}>Топ недели по цитируемости</p>}
                  {tab === "saved" && <p style={{ fontFamily: font.sans, fontSize: 13, color: C.muted, margin: "3px 0 0" }}>{savedList.length} статей</p>}
                </div>
                <span onClick={() => setShowPremium(true)} style={{ display: "inline-flex", alignItems: "center", gap: 5, fontFamily: font.sans, fontSize: 12, color: C.muted, background: C.card, border: `0.5px solid ${C.line}`, borderRadius: 999, padding: "5px 11px", cursor: "pointer", marginTop: 2, flexShrink: 0 }}>О боте</span>
              </div>

              {(tab === "feed") && (
                <div style={{ display: "flex", gap: 7, marginTop: 14, flexWrap: "wrap" }}>
                  {TOPICS.filter((t) => t.key !== "hot").map((t) => {
                    const active = filter === t.key;
                    return (
                      <span key={t.key} onClick={() => setFilter(t.key)} style={{
                        fontFamily: font.sans, fontSize: 13, borderRadius: 999, padding: "6px 13px", cursor: "pointer",
                        background: active ? C.ink : C.card, color: active ? "#fff" : C.muted,
                        border: active ? "none" : `0.5px solid ${C.line}`,
                      }}>{t.label}</span>
                    );
                  })}
                </div>
              )}
            </header>

            <main style={{ flex: 1, overflowY: "auto", padding: "4px 16px 16px" }}>
              {tab === "search" ? (
                <SearchView />
              ) : tab === "saved" ? (
                savedList.length ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {savedList.map((a, i) => <Card key={a.id} a={a} idx={i} saved onToggle={toggle} onOpen={setSelected} />)}
                  </div>
                ) : (
                  <div style={{ textAlign: "center", color: C.faint, fontFamily: font.sans, fontSize: 14, marginTop: 80 }}>
                    <Bookmark size={28} style={{ opacity: 0.4 }} />
                    <p>Пока пусто. Жми закладку на карточке.</p>
                  </div>
                )
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {tab === "feed" && <FactCard />}
                  {(tab === "hot" ? [...ARTICLES].sort((a, b) => b.cited - a.cited) : feed).map((a, i) => (
                    <Card key={a.id} a={a} idx={i} saved={saved.has(a.id)} onToggle={toggle} onOpen={setSelected} />
                  ))}
                </div>
              )}
            </main>

            <nav style={{ display: "flex", justifyContent: "space-around", alignItems: "center", padding: "10px 0", borderTop: `0.5px solid ${C.line}`, background: C.card, flexShrink: 0 }}>
              {tabs.map((t) => {
                const Icon = t.icon;
                const active = tab === t.key;
                return (
                  <span key={t.key} onClick={() => setTab(t.key)} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3, cursor: "pointer", color: active ? C.ink : C.faint }}>
                    <Icon size={21} />
                    <span style={{ fontFamily: font.sans, fontSize: 11 }}>{t.label}</span>
                  </span>
                );
              })}
            </nav>
          </>
        )}
      </div>
    </div>
  );
}
