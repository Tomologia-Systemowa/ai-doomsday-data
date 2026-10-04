/* AI Doomsday dashboard.
 *
 * htmx does all loading and swapping: every request goes through the "json-view" extension,
 * which parses the JSON response, builds a view model and renders it with a Mustache template
 * from index.html. Mustache escapes every value, so no raw data ever reaches innerHTML.
 */
(function () {
  'use strict';

  // ---- Configuration -------------------------------------------------------------------------

  // Where the data comes from:
  // - localhost and GitHub Pages serve the repo, so data/ sits next to dashboard/ ('../data/');
  // - anywhere else (own hosting, a file opened from disk) reads straight from GitHub (RAW_BASE),
  //   so the page stays current with the daily routine without copying data/.
  // To force one source, replace the expression with '../data/' or RAW_BASE.
  const RAW_BASE = 'https://raw.githubusercontent.com/Tomologia-Systemowa/ai-doomsday-data/main/data/';
  const LOCAL_DATA_HOSTS = /^(localhost|127\.0\.0\.1|\[::1\])$|\.github\.io$/;
  const DATA_BASE = LOCAL_DATA_HOSTS.test(window.location.hostname) ? '../data/' : RAW_BASE;
  const REPO_URL = 'https://github.com/Tomologia-Systemowa/ai-doomsday-data';
  const ALLOWED_HOSTS = [new URL(RAW_BASE).host];
  const LANG_KEY = 'ai-doomsday-lang';

  // ---- Dictionary ----------------------------------------------------------------------------

  const I18N = {
    pl: {
      locale: 'pl-PL',
      skip: 'Przejdź do raportu',
      slogan: 'Dzień Sądu: kiedy taniej jest skończyć z ludzkością, niż spłacić dług.',
      tagline: 'Stan bańki AI na dziś',
      lastReport: 'Ostatni raport',
      trend: 'Historia wyniku', fullReport: 'Pełny raport', loading: 'Ładowanie…',
      pickDay: 'Wybierz kropkę na wykresie (kliknięcie lub Enter), aby zobaczyć dany dzień.',
      repo: 'Repozytorium danych', updated: 'Aktualizacja danych', notAdvice: 'To nie jest porada inwestycyjna.',
      categories: 'Punkty kategorii', category: 'Kategoria', pointsBudget: 'Punkty / budżet',
      reserve: 'Zapas do 1000', heavyCredit: 'Ciężkie zdarzenie kredytowe', trigger: 'Wyzwalacz',
      skippedSignals: 'Pominięte sygnały', nearBoundary: 'Na granicy przedziałów',
      noPrev: 'brak poprzedniego raportu', vsPrev: 'vs poprzedni',
      noHistory: 'Brak danych historycznych.', dayReport: 'Raport dzienny', baseline: 'Punkt odniesienia',
      date: 'Data', score: 'Wynik', band: 'Przedział', kind: 'Rodzaj',
      kinds: { full: 'pełny', short: 'krótki', baseline: 'punkt odniesienia' },
      noEntry: 'Tego dnia nie było raportu – tylko zdarzenia.', events: 'Zdarzenia dnia', jsonData: 'Dane JSON',
      noSummary: 'Brak opisu dla tego dnia.',
      severity: { info: 'info', light: 'lekkie', medium: 'średnie', heavy: 'ciężkie', trigger: 'wyzwalacz' },
      summary: 'Podsumowanie', weekly: 'Analiza tygodniowa', curve: 'Komentarz do krzywej rentowności',
      signals: 'Sygnały', signal: 'Sygnał', value: 'Wartość', asOf: 'Odczyt', status: 'Status',
      points: 'Punkty', source: 'Źródło', preliminary: 'wstępny', coi: 'konflikt interesów',
      licensed: 'dane licencjonowane',
      statuses: { green: 'zielony', yellow: 'żółty', red: 'czerwony', skipped: 'pominięty' },
      quality: 'ocena jakościowa',
      adjustments: 'Korekty', noAdjustments: 'Brak korekt.', pts: 'pkt', floor: 'próg',
      calendar: 'Kalendarz', noCalendar: 'Brak zaplanowanych wydarzeń.',
      reportTypes: { full: 'raport pełny', short: 'raport krótki' },
      noDaily: 'Brak pełnego tekstu raportu dla tego dnia – pokazano dane z latest.json.',
      errNotFound: 'Nie znaleziono pliku z danymi.', errNetwork: 'Błąd sieci – nie udało się pobrać danych.',
      errParse: 'Plik z danymi jest uszkodzony lub ma nieoczekiwany format.', errTitle: 'Nie udało się wyświetlić tej sekcji',
      trendAria: 'Wykres liniowy wyniku AI Doomsday w czasie, skala 0–1000. Dane w tabeli poniżej.',
      donutAria: 'Wykres pierścieniowy: wynik {score} z 1000, przedział {band}. ',
    },
    en: {
      locale: 'en-GB',
      skip: 'Skip to report',
      slogan: 'Judgment Day: when ending humanity is cheaper than paying off the debt.',
      tagline: 'State of the AI bubble today',
      lastReport: 'Latest report',
      trend: 'Score history', fullReport: 'Full report', loading: 'Loading…',
      pickDay: 'Pick a dot on the chart (click or Enter) to see that day.',
      repo: 'Data repository', updated: 'Data updated', notAdvice: 'This is not investment advice.',
      categories: 'Category points', category: 'Category', pointsBudget: 'Points / budget',
      reserve: 'Headroom to 1000', heavyCredit: 'Heavy credit event', trigger: 'Trigger',
      skippedSignals: 'Skipped signals', nearBoundary: 'Near a band boundary',
      noPrev: 'no previous report', vsPrev: 'vs previous',
      noHistory: 'No history yet.', dayReport: 'Daily report', baseline: 'Baseline',
      date: 'Date', score: 'Score', band: 'Band', kind: 'Kind',
      kinds: { full: 'full', short: 'short', baseline: 'baseline' },
      noEntry: 'No report on this day – events only.', events: 'Events of the day', jsonData: 'JSON data',
      noSummary: 'No description for this day.',
      severity: { info: 'info', light: 'light', medium: 'medium', heavy: 'heavy', trigger: 'trigger' },
      summary: 'Summary', weekly: 'Weekly analysis', curve: 'Yield curve comment',
      signals: 'Signals', signal: 'Signal', value: 'Value', asOf: 'As of', status: 'Status',
      points: 'Points', source: 'Source', preliminary: 'preliminary', coi: 'conflict of interest',
      licensed: 'licensed data',
      statuses: { green: 'green', yellow: 'yellow', red: 'red', skipped: 'skipped' },
      quality: 'qualitative',
      adjustments: 'Adjustments', noAdjustments: 'No adjustments.', pts: 'pts', floor: 'floor',
      calendar: 'Calendar', noCalendar: 'No scheduled events.',
      reportTypes: { full: 'full report', short: 'short report' },
      noDaily: 'The full report text for this day is missing – showing data from latest.json.',
      errNotFound: 'Data file not found.', errNetwork: 'Network error – could not fetch the data.',
      errParse: 'The data file is damaged or has an unexpected format.', errTitle: 'Could not display this section',
      trendAria: 'Line chart of the AI Doomsday score over time, scale 0–1000. Data in the table below.',
      donutAria: 'Donut chart: score {score} of 1000, band {band}. ',
    },
  };

  const CAT_KEYS = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

  const state = {
    lang: 'pl',
    scale: null,
    latest: null,
    selectedFile: null,
  };

  // ---- Small helpers -------------------------------------------------------------------------

  function t() { return I18N[state.lang]; }

  // A saved choice wins; otherwise Polish for a Polish browser, English for everyone else.
  function readLang() {
    try {
      const v = window.localStorage.getItem(LANG_KEY);
      if (v === 'pl' || v === 'en') return v;
    } catch (e) { /* storage unavailable */ }
    const pref = (navigator.languages && navigator.languages[0]) || navigator.language || '';
    return /^pl(-|$)/i.test(pref) ? 'pl' : 'en';
  }

  function saveLang(lang) {
    try { window.localStorage.setItem(LANG_KEY, lang); } catch (e) { /* storage unavailable */ }
  }

  // Text field in the current language; falls back to Polish when the _en field is missing.
  function pick(obj, key) {
    if (!obj) return '';
    if (state.lang === 'en') {
      const en = obj[key + '_en'];
      if (typeof en === 'string' && en.trim() !== '') return en;
      if (Array.isArray(en) && en.length) return en;
    }
    const v = obj[key];
    return v == null ? '' : v;
  }

  function fmtNum(n, maxDigits) {
    if (typeof n !== 'number' || !isFinite(n)) return '—';
    return new Intl.NumberFormat(t().locale, { maximumFractionDigits: maxDigits == null ? 2 : maxDigits }).format(n);
  }

  function fmtSigned(n) {
    const s = fmtNum(Math.abs(n), 1);
    return n > 0 ? '+' + s : n < 0 ? '−' + s : s;
  }

  function parseIsoDate(iso) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || ''));
    return m ? new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])) : null;
  }

  function fmtDate(iso, style) {
    const d = parseIsoDate(iso);
    if (!d) return iso ? String(iso) : '—';
    const opts = style === 'short' ? { day: '2-digit', month: '2-digit' }
      : style === 'medium' ? { day: 'numeric', month: 'short', year: 'numeric' }
        : { day: 'numeric', month: 'long', year: 'numeric' };
    opts.timeZone = 'UTC';
    return d.toLocaleDateString(t().locale, opts);
  }

  function fmtDateTime(iso) {
    const d = new Date(iso);
    if (!iso || isNaN(d)) return '—';
    return d.toLocaleString(t().locale, { dateStyle: 'long', timeStyle: 'short', timeZone: 'Europe/Warsaw' });
  }

  // Only http(s) links from the data are rendered as links.
  function safeLink(u) {
    if (typeof u !== 'string') return null;
    try {
      const url = new URL(u);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') return null;
      return { href: url.href, host: url.hostname.replace(/^www\./, '') };
    } catch (e) { return null; }
  }

  // Paths taken from the data (report_file, index file names) are whitelisted before use.
  function dataUrl(path) {
    if (typeof path !== 'string' || !/^(history\/)?history-\d{2}-\d{2}-\d{4}\.json$/.test(path)) return null;
    return DATA_BASE + path;
  }

  function githubJsonUrl(file) {
    return REPO_URL + '/blob/main/data/history/' + file;
  }

  function bandLabel(plName, score) {
    const bands = (state.scale && state.scale.bands) || [];
    let band = bands.find(function (b) { return b.band === plName; });
    if (!band && typeof score === 'number') {
      band = bands.find(function (b) { return score >= b.min && score <= b.max; });
    }
    if (!band) return plName || '—';
    return state.lang === 'en' && band.band_en ? band.band_en : band.band;
  }

  // band_en when present, otherwise translated through scale.json (older files have no _en).
  function bandOf(obj, score) {
    if (state.lang === 'en' && obj.band_en) return obj.band_en;
    return bandLabel(obj.band, score);
  }

  function changeInfo(v) {
    if (typeof v !== 'number') return { cls: 'chg-none', arrow: '', text: t().noPrev };
    if (v > 0) return { cls: 'chg-up', arrow: '▲', text: fmtSigned(v) + ' ' + t().vsPrev };
    if (v < 0) return { cls: 'chg-down', arrow: '▼', text: fmtSigned(v) + ' ' + t().vsPrev };
    return { cls: 'chg-none', arrow: '■', text: '0 ' + t().vsPrev };
  }

  function statusInfo(status) {
    const q = /^q(0|25|50|75|100)$/.exec(status || '');
    if (q) {
      const pct = +q[1];
      const color = pct === 0 ? 'green' : pct <= 50 ? 'yellow' : 'red';
      return { color: color, label: t().quality + ' ' + pct + '%' };
    }
    if (['green', 'yellow', 'red', 'skipped'].indexOf(status) >= 0) {
      return { color: status === 'skipped' ? 'gray' : status, label: t().statuses[status] };
    }
    return { color: 'gray', label: status || '—' };
  }

  function categoryInfo(key) {
    const c = (state.scale && state.scale.categories && state.scale.categories[key]) || {};
    return { name: pick(c, 'name') || key, budget: typeof c.budget === 'number' ? c.budget : null };
  }

  function categoryPoints(latest) {
    const sums = {};
    CAT_KEYS.forEach(function (k) { sums[k] = 0; });
    (latest.signals || []).forEach(function (s) {
      if (s && sums[s.category] != null && typeof s.points === 'number') sums[s.category] += s.points;
    });
    (latest.adjustments || []).forEach(function (a) {
      if (a && sums[a.category] != null && typeof a.points === 'number') sums[a.category] += a.points;
    });
    CAT_KEYS.forEach(function (k) { sums[k] = Math.round(sums[k] * 10) / 10; });
    return sums;
  }

  function paragraphs(text) {
    if (typeof text !== 'string' || !text.trim()) return [];
    const parts = text.split(/\n\s*\n/);
    return (parts.length > 1 ? parts : text.split(/\n/)).map(function (p) { return p.trim(); }).filter(Boolean);
  }

  function template(id) {
    const el = document.getElementById(id);
    return el ? el.innerHTML : '';
  }

  function render(id, view) {
    view.t = t();
    return window.Mustache.render(template(id), view);
  }

  // ---- Donut geometry ------------------------------------------------------------------------

  function arcPath(cx, cy, R, r, a0, a1) {
    if (a1 - a0 >= Math.PI * 2) a1 = a0 + Math.PI * 2 - 0.0001;
    const large = a1 - a0 > Math.PI ? 1 : 0;
    function pt(rad, ang) { return (cx + rad * Math.sin(ang)).toFixed(2) + ' ' + (cy - rad * Math.cos(ang)).toFixed(2); }
    return 'M' + pt(R, a0) + ' A' + R + ' ' + R + ' 0 ' + large + ' 1 ' + pt(R, a1) +
      ' L' + pt(r, a1) + ' A' + r + ' ' + r + ' 0 ' + large + ' 0 ' + pt(r, a0) + ' Z';
  }

  // Flames along the filled part of the ring: the further the score goes round, the more fire,
  // and the higher the score, the taller each flame.
  function flames(heat) {
    const count = Math.round(heat * 72);
    const out = [];
    for (let i = 0; i < count; i++) {
      const r1 = frac(Math.sin(i * 12.9898) * 43758.5453);
      const r2 = frac(Math.sin(i * 78.233) * 12345.678);
      out.push({
        deg: (((i + 0.5) / count) * heat * 360).toFixed(1),
        scale: ((0.45 + heat * 1.4) * (0.7 + 0.6 * r1)).toFixed(2),
        delay: (r2 * 1.6).toFixed(2),
      });
    }
    return out;
  }

  function frac(x) { return x - Math.floor(x); }

  // ---- Views: JSON -> view model -> HTML ------------------------------------------------------

  const VIEWS = {
    overview: function (latest) {
      if (!latest || typeof latest !== 'object') throw new Error('parse');
      state.latest = latest;
      const sums = categoryPoints(latest);
      let angle = 0;
      let total = 0;
      const slices = [];
      const legend = [];
      CAT_KEYS.forEach(function (k, i) {
        const info = categoryInfo(k);
        const pts = sums[k];
        const label = k + ' · ' + info.name + ': ' + fmtNum(pts, 1) + ' / ' + (info.budget == null ? '—' : info.budget);
        legend.push({
          key: k, name: info.name, points: fmtNum(pts, 1), budget: info.budget == null ? '—' : info.budget, cls: 'cat-' + (i + 1),
          pct: info.budget ? Math.round(Math.max(0, Math.min(1, pts / info.budget)) * 100) : 0,
        });
        if (pts > 0) {
          const a1 = angle + (pts / 1000) * Math.PI * 2;
          slices.push({ d: arcPath(200, 200, 148, 104, angle, a1), cls: 'cat-' + (i + 1), label: label });
          angle = a1;
        }
        total += Math.max(0, pts);
      });
      if (total < 1000) {
        slices.push({ d: arcPath(200, 200, 148, 104, angle, Math.PI * 2), cls: 'reserve', label: t().reserve + ': ' + fmtNum(1000 - total, 1) });
      }
      const heat = Math.max(0, Math.min(1, total / 1000));
      document.documentElement.style.setProperty('--heat', heat.toFixed(3));
      const score = typeof latest.score === 'number' ? latest.score : null;
      const band = bandOf(latest, score);
      const triggers = pick(latest, 'triggers');
      const skipped = Array.isArray(latest.skipped_signals) ? latest.skipped_signals.map(String) : [];
      const reportUrl = dataUrl(latest.report_file);
      const aria = t().donutAria.replace('{score}', score == null ? '—' : score).replace('{band}', band) +
        legend.map(function (l) { return l.key + ' ' + l.name + ' ' + l.points + '/' + l.budget; }).join('; ');
      if (!reportUrl) setTimeout(function () { showReport(null); }, 0);
      return render('tpl-overview', {
        dateLong: fmtDate(latest.date),
        score: score == null ? '—' : score,
        band: band,
        change: changeInfo(latest.change_vs_previous),
        slices: slices,
        flames: flames(heat),
        legend: legend,
        aria: aria,
        heavyCredit: latest.heavy_credit_event === true,
        triggers: Array.isArray(triggers) ? triggers.map(String) : [],
        skipped: skipped,
        skippedText: skipped.join(', '),
        headline: pick(latest, 'headline'),
        reportUrl: reportUrl,
      });
    },

    trend: function (index, elt) {
      if (!index || !Array.isArray(index.files)) throw new Error('parse');
      const files = index.files
        .filter(function (f) { return f && parseIsoDate(f.date); })
        .slice()
        .sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
      const updatedAt = fmtDateTime(index.updated_at);
      if (!files.length) return render('tpl-trend', { empty: true, updatedAt: updatedAt });

      const w = Math.max(320, Math.min(1040, Math.round(elt.clientWidth || 720)));
      const h = w < 520 ? 240 : 300;
      // Wide: band names to the right of the plot. Narrow: inside the plot, top-left of each band.
      const narrow = w < 520;
      const m = { l: 40, r: narrow ? 10 : 112, t: 12, b: 30 };
      const pw = w - m.l - m.r;
      const ph = h - m.t - m.b;
      const n = files.length;
      const xOf = function (i) { return m.l + (n === 1 ? pw / 2 : 12 + (i * (pw - 24)) / (n - 1)); };
      const yOf = function (s) { return m.t + (1 - Math.max(0, Math.min(1000, s)) / 1000) * ph; };

      const bands = ((state.scale && state.scale.bands) || []).map(function (b, i) {
        const yTop = yOf(b.max);
        const yBot = yOf(i === 0 ? b.min : b.min - 1);
        return {
          i: i, x: m.l, y: yTop.toFixed(1), width: pw, height: (yBot - yTop).toFixed(1),
          name: state.lang === 'en' && b.band_en ? b.band_en : b.band,
          labelX: narrow ? m.l + 4 : m.l + pw + 6, labelY: (narrow ? yTop + 12 : (yTop + yBot) / 2 + 4).toFixed(1),
        };
      });
      const yTicks = [0, 200, 400, 600, 800, 1000].map(function (v) {
        const y = yOf(v);
        return { x1: m.l, x2: m.l + pw, y: y.toFixed(1), tx: m.l - 6, ty: (y + 4).toFixed(1), label: v };
      });
      const maxLabels = Math.max(2, Math.floor(pw / 64));
      const step = Math.max(1, Math.ceil(n / maxLabels));
      const xTicks = [];
      files.forEach(function (f, i) {
        if (i % step === 0 || i === n - 1) {
          if (i === n - 1 && i % step !== 0 && n - 1 - (i - (i % step)) < step / 2) xTicks.pop();
          xTicks.push({ x: xOf(i).toFixed(1), y: h - 8, label: fmtDate(f.date, 'short') });
        }
      });

      const line = [];
      const dots = [];
      const rows = [];
      let last = null;
      files.forEach(function (f, i) {
        const hasScore = typeof f.score === 'number';
        const x = xOf(i);
        const y = hasScore ? yOf(f.score) : m.t + ph;
        const band = hasScore ? bandLabel(f.band, f.score) : '—';
        const kind = t().kinds[f.kind] || f.kind || '';
        if (hasScore) {
          line.push(x.toFixed(1) + ',' + y.toFixed(1));
          last = { x: x, y: y, score: f.score };
        }
        const file = typeof f.file === 'string' && /^history-\d{2}-\d{2}-\d{4}\.json$/.test(f.file) ? f.file : null;
        const label = fmtDate(f.date) + ': ' + (hasScore ? f.score + '/1000, ' + band : '—') + (kind ? ' (' + kind + ')' : '');
        dots.push({
          x: x.toFixed(1), y: y.toFixed(1), rx: (x - 5.5).toFixed(1), ry: (y - 5.5).toFixed(1),
          baseline: f.kind === 'baseline', noScore: !hasScore, label: label,
          file: file || '', url: file ? DATA_BASE + 'history/' + file : '',
          selected: file && file === state.selectedFile,
        });
        rows.push({ date: fmtDate(f.date), score: hasScore ? f.score : '—', band: band, kind: kind });
      });
      if (last) {
        const nearRight = last.x > m.l + pw - 40;
        last = { x: (nearRight ? last.x - 10 : last.x + 10).toFixed(1), y: (last.y - 10).toFixed(1), anchor: nearRight ? 'end' : 'start', score: last.score };
      }
      return render('tpl-trend', {
        empty: false, updatedAt: updatedAt, w: w, h: h, aria: t().trendAria,
        bands: bands, yTicks: yTicks, xTicks: xTicks, line: line.join(' '), last: last, dots: dots, rows: rows,
      });
    },

    day: function (day, elt) {
      if (!day || typeof day !== 'object') throw new Error('parse');
      const file = elt.getAttribute('data-file');
      const entry = day.entry && typeof day.entry === 'object' ? day.entry : null;
      const report = day.report && typeof day.report === 'object' ? day.report : null;
      const score = entry && typeof entry.score === 'number' ? entry.score : null;
      const text = (report && pick(report, 'summary')) || (entry && pick(entry, 'headline')) || (entry ? t().noSummary : '');
      const events = (Array.isArray(day.events) ? day.events : []).filter(Boolean).map(function (ev) {
        const link = safeLink(ev.source);
        return {
          severity: /^[a-z_]+$/.test(ev.severity || '') ? ev.severity : 'info',
          severityLabel: t().severity[ev.severity] || ev.severity || ev.type || '',
          signal: ev.signal || '', title: pick(ev, 'title') || ev.type || '',
          source: link && link.href, host: link && link.host,
        };
      });
      return render('tpl-day', {
        dateLong: fmtDate(day.date),
        score: score == null ? '—' : score,
        band: entry ? bandOf(entry, score) : '—',
        kindLabel: entry ? (t().kinds[entry.kind] || entry.kind || '') : '',
        noEntry: !entry,
        text: text,
        events: events,
        jsonUrl: githubJsonUrl(file),
      });
    },

    report: function (daily) {
      return reportHtml(daily, false);
    },
  };

  function reportHtml(daily, missingDaily) {
    const latest = state.latest || {};
    const rep = daily && daily.report && typeof daily.report === 'object' ? daily.report : null;
    const comments = (rep && rep.category_comments) || {};
    const signals = Array.isArray(latest.signals) ? latest.signals : (rep && Array.isArray(rep.signals) ? rep.signals : []);
    const sums = categoryPoints({ signals: signals, adjustments: latest.adjustments });

    const groups = CAT_KEYS.map(function (k, i) {
      const info = categoryInfo(k);
      const rows = signals.filter(function (s) { return s && s.category === k; }).map(function (s) {
        const link = safeLink(s.source);
        const hasValue = s.value !== null && s.value !== undefined && s.value !== '';
        const value = hasValue ? (typeof s.value === 'number' ? fmtNum(s.value) : String(s.value)) + (s.unit ? ' ' + s.unit : '') : '—';
        const coi = s.conflict_of_interest;
        return {
          id: s.id, name: pick(s, 'name') || s.id,
          value: value, licensed: !hasValue && s.status !== 'skipped',
          asOf: fmtDate(s.as_of, 'medium'),
          status: statusInfo(s.status), skipped: s.status === 'skipped',
          points: fmtNum(s.points, 1), max: fmtNum(s.max_points, 1),
          source: link && link.href, host: link && link.host,
          note: pick(s, 'note'),
          preliminary: s.preliminary === true,
          coi: !!coi, coiText: typeof coi === 'string' ? coi : t().coi,
        };
      });
      const c = comments[k];
      return {
        key: k, name: info.name, cls: 'cat-' + (i + 1),
        points: fmtNum(sums[k], 1), budget: info.budget == null ? '—' : info.budget,
        comment: c ? (typeof c === 'string' ? c : pick(c, 'comment')) : '',
        rows: rows,
      };
    }).filter(function (g) { return g.rows.length || g.comment; });

    const adjustments = (Array.isArray(latest.adjustments) ? latest.adjustments : []).filter(Boolean).map(function (a) {
      return {
        category: a.category, name: categoryInfo(a.category).name,
        points: fmtSigned(a.points), floor: typeof a.floor === 'number' ? fmtNum(a.floor) : '',
        reason: pick(a, 'reason'),
      };
    });
    const calendar = (Array.isArray(latest.calendar) ? latest.calendar : []).filter(Boolean).map(function (c) {
      return { iso: c.date, date: fmtDate(c.date, 'medium'), title: pick(c, 'title') };
    });
    const score = typeof latest.score === 'number' ? latest.score : null;

    // The boundary badge lives in the overview card; it arrives as an out-of-band swap.
    return render('tpl-boundary', { near: !!(rep && rep.near_boundary === true) }) + render('tpl-report', {
      dateLong: fmtDate(latest.date),
      typeLabel: t().reportTypes[latest.report_type] || '',
      score: score == null ? '—' : score,
      band: bandOf(latest, score),
      change: changeInfo(latest.change_vs_previous),
      headline: pick(latest, 'headline'),
      missingDaily: missingDaily || !rep,
      summary: pick(latest, 'summary') || (rep && pick(rep, 'summary')) || t().noSummary,
      weekly: rep ? paragraphs(pick(rep, 'weekly_analysis')) : [],
      curve: rep ? pick(rep, 'curve_comment') : '',
      groups: groups,
      adjustments: adjustments,
      calendar: calendar,
      disclaimer: pick(latest, 'disclaimer') || t().notAdvice,
    });
  }

  function errorHtml(kind, url) {
    const msg = kind === 'notfound' ? t().errNotFound : kind === 'network' ? t().errNetwork : t().errParse;
    return render('tpl-error', { title: t().errTitle, detail: msg, url: url || '' });
  }

  // Render outside a request (fallbacks, errors). Still goes through htmx.swap, so oob parts work.
  function swapInto(target, html) {
    if (!target) return;
    window.htmx.swap({ text: html, target: target, sourceElement: target, swap: 'innerHTML' });
  }

  // The report is built on latest.json, so it cannot be shown when that file fails.
  function reportFailed(kind, url) {
    state.latest = null;
    setTimeout(function () { swapInto(document.getElementById('report'), errorHtml(kind, url)); }, 0);
  }

  function showReport(daily) {
    swapInto(document.getElementById('report'), reportHtml(daily, true));
  }

  // ---- htmx extension ------------------------------------------------------------------------

  // Turns the JSON response into HTML before htmx swaps it in.
  window.htmx.registerExtension('json-view', {
    htmx_after_request: function (elt, detail) {
      const ctx = detail.ctx;
      if (ctx.response.status >= 400) return; // handled in htmx:response:error
      const view = elt.getAttribute('data-view');
      if (!VIEWS[view]) return;
      try {
        ctx.text = VIEWS[view](JSON.parse(ctx.text), elt);
      } catch (e) {
        console.error('[ai-doomsday]', view, e);
        if (view === 'report') ctx.text = reportHtml(null, true);
        else {
          if (view === 'overview') reportFailed('parse', ctx.request.action);
          ctx.text = errorHtml('parse', ctx.request.action);
        }
      }
    },
  });

  // The error body (e.g. GitHub's 404 page) is never shown: htmx swaps nothing for 4xx / 5xx.
  function onRequestFailed(kind, ctx) {
    const elt = ctx.sourceElement;
    const url = ctx.request && ctx.request.action || '';
    const view = elt && elt.getAttribute('data-view');
    if (view === 'report') { showReport(null); return; }
    if (view === 'overview') reportFailed(kind, url);
    swapInto(ctx.target, errorHtml(kind, url));
  }

  document.addEventListener('htmx:response:error', function (evt) {
    evt.detail.ctx.text = ''; // otherwise htmx would take document.title from the error page
    onRequestFailed(evt.detail.ctx.response.status === 404 ? 'notfound' : 'network', evt.detail.ctx);
  });
  // Network failure, timeout or abort. Errors without a request (e.g. in a swap) are only logged by htmx.
  document.addEventListener('htmx:error', function (evt) {
    const ctx = evt.detail.ctx;
    if (ctx && ctx.request && !ctx.response) onRequestFailed('network', ctx);
  });

  document.addEventListener('htmx:config:request', function (evt) {
    const ctx = evt.detail.ctx;
    let url;
    try {
      url = new URL(ctx.request.action, document.baseURI);
    } catch (e) {
      evt.preventDefault();
      return;
    }
    // Only same-origin requests and raw.githubusercontent.com are allowed.
    if (url.origin !== window.location.origin && ALLOWED_HOSTS.indexOf(url.host) < 0) evt.preventDefault();
  });

  document.addEventListener('htmx:before:request', function (evt) {
    const ctx = evt.detail.ctx;
    const elt = ctx.sourceElement;
    // Cross-origin: drop htmx headers (HX-Request-Type is added after config:request), so the GET
    // stays a simple CORS request without a preflight.
    if (new URL(ctx.request.action, document.baseURI).origin !== window.location.origin) ctx.request.headers = {};
    if (elt && elt.getAttribute('data-view') === 'day') {
      state.selectedFile = elt.getAttribute('data-file');
      document.querySelectorAll('.dot.is-selected').forEach(function (d) { d.classList.remove('is-selected'); });
      elt.classList.add('is-selected');
      ctx.target.setAttribute('aria-busy', 'true');
    }
  });

  document.addEventListener('htmx:after:swap', function (evt) {
    const target = evt.detail.ctx.target;
    if (target) target.removeAttribute('aria-busy');
  });

  // After a re-render of the chart (language change, resize) reopen the selected day.
  // after:settle: by then htmx has attached its triggers to the new dots.
  document.addEventListener('htmx:after:settle', function (evt) {
    const target = evt.target;
    if (target && target.id === 'trend' && state.selectedFile) {
      const dot = target.querySelector('.dot[data-file="' + CSS.escape(state.selectedFile) + '"]');
      if (dot) window.htmx.trigger(dot, 'activate');
    }
  });

  // Enter / Space on a focused chart dot.
  document.addEventListener('keydown', function (evt) {
    const dot = evt.target && evt.target.closest && evt.target.closest('.dot[hx-get]');
    if (!dot || (evt.key !== 'Enter' && evt.key !== ' ')) return;
    evt.preventDefault();
    window.htmx.trigger(dot, 'activate');
  });

  // ---- Language ------------------------------------------------------------------------------

  function applyStaticTexts() {
    document.documentElement.lang = state.lang;
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      const v = t()[el.getAttribute('data-i18n')];
      if (typeof v === 'string') el.textContent = v;
    });
    document.querySelectorAll('.lang button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === state.lang));
    });
  }

  function setLang(lang) {
    if (lang === state.lang) return;
    state.lang = lang;
    saveLang(lang);
    applyStaticTexts();
    if (state.scale) window.htmx.trigger(document.body, 'langchange');
  }

  document.querySelectorAll('.lang button').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.getAttribute('data-lang')); });
  });

  // ---- Start ---------------------------------------------------------------------------------

  // Data URLs are set here (one constant) before htmx processes the page (see start()).
  document.querySelectorAll('[data-src]').forEach(function (el) {
    el.setAttribute('hx-get', DATA_BASE + el.getAttribute('data-src'));
  });

  state.lang = readLang();
  applyStaticTexts();

  let lastWidth = 0;
  window.addEventListener('resize', (function () {
    let timer = null;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        const el = document.getElementById('trend');
        if (state.scale && el && Math.abs(el.clientWidth - lastWidth) > 40) {
          lastWidth = el.clientWidth;
          window.htmx.trigger(el, 'redraw');
        }
      }, 250);
    };
  }()));

  function start() {
    lastWidth = (document.getElementById('trend') || {}).clientWidth || 0;
    fetch(DATA_BASE + 'scale.json')
      .then(function (r) {
        if (!r.ok) throw new Error(r.status === 404 ? 'notfound' : 'network');
        return r.json().catch(function () { throw new Error('parse'); });
      })
      .then(function (scale) {
        if (!scale || !Array.isArray(scale.bands) || !scale.categories) throw new Error('parse');
        state.scale = scale;
        // htmx 4 initializes itself from a setTimeout, which may run after DOMContentLoaded.
        // process() is idempotent, so make sure the triggers exist before the event is fired.
        window.htmx.process(document.body);
        window.htmx.trigger(document.body, 'dataready');
      })
      .catch(function (e) {
        const kind = ['notfound', 'parse'].indexOf(e.message) >= 0 ? e.message : 'network';
        ['overview', 'trend', 'report'].forEach(function (id) {
          swapInto(document.getElementById(id), errorHtml(kind, DATA_BASE + 'scale.json'));
        });
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
}());
