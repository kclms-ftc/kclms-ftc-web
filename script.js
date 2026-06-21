// KCLMS VOLCANIX - Interactive behaviour
// ======================================

// === RACING-STRIPE LOADER ===
// A stripe streaks across the screen and "draws" KCLMS in volcanic red,
// then the overlay clears to reveal the page.
(function () {
  const loader = document.getElementById('loader');
  if (!loader) return;

  // Only on the very first visit ever; never again, including page-to-page nav.
  let seen = null;
  try { seen = localStorage.getItem('volcanixLoaderSeen'); } catch (e) { seen = null; }
  if (seen) { loader.remove(); return; }

  document.body.classList.add('loading');

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hold = reduce ? 200 : 2100;
  let done = false;

  function dismiss() {
    if (done) return;
    done = true;
    try { localStorage.setItem('volcanixLoaderSeen', '1'); } catch (e) { /* storage blocked */ }
    document.documentElement.setAttribute('data-loader', 'seen');
    loader.classList.add('is-done');
    document.body.classList.remove('loading');
    setTimeout(() => loader.remove(), 700);
  }

  window.addEventListener('load', () => setTimeout(dismiss, hold));
  // Safety net in case the load event already fired or is delayed
  setTimeout(dismiss, hold + 2500);
})();

// === THEME TOGGLE ===
// Initial theme is set by an inline <head> script to avoid a flash of the
// wrong theme. Here we just wire the toggle button and persist the choice.
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.querySelector('.theme-toggle');
  if (!toggle) return;
  // The navbar uses backdrop-filter, which traps position:fixed inside it.
  // Move the toggle out to <body> so it pins to the viewport's bottom-right.
  document.body.appendChild(toggle);
  toggle.addEventListener('click', function () {
    const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) { /* storage blocked */ }
  });
});

// === MOBILE MENU ===
document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.querySelector('.mobile-menu-toggle');
  const menu = document.querySelector('.navbar-menu');

  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      menu.classList.toggle('active');
      toggle.classList.toggle('active');
    });
    menu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        menu.classList.remove('active');
        toggle.classList.remove('active');
      });
    });
  }
});

// === NAVBAR SCROLL STATE ===
window.addEventListener('scroll', function () {
  const navbar = document.querySelector('.navbar');
  if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 40);
});

// === ANIMATED COUNTERS ===
function animateCounter(el, target, duration = 1800) {
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(tick);
    else el.textContent = target;
  }
  requestAnimationFrame(tick);
}

// === SCROLL REVEAL + COUNTER TRIGGER ===
const observer = new IntersectionObserver(function (entries) {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('active');
    if (entry.target.classList.contains('stat-number')) {
      const target = parseInt(entry.target.getAttribute('data-target'), 10);
      if (!isNaN(target)) animateCounter(entry.target, target);
    }
    observer.unobserve(entry.target);
  });
}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.reveal, .stat-number').forEach(el => observer.observe(el));
});

// === ACTIVE NAV LINK ===
document.addEventListener('DOMContentLoaded', function () {
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.navbar-menu a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === current || (current === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
});

// === SMOOTH SCROLL FOR ANCHORS ===
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (href === '#' || href === '') return;
    const target = document.querySelector(href);
    if (target) {
      e.preventDefault();
      window.scrollTo({ top: target.offsetTop - 80, behavior: 'smooth' });
    }
  });
});

// === HCB OPEN FINANCES (live) ===
document.addEventListener('DOMContentLoaded', function () {
  const card = document.querySelector('[data-hcb-slug]');
  if (!card) return;

  const slug = card.getAttribute('data-hcb-slug');
  const api = 'https://hcb.hackclub.com/api/v3/organizations/' + slug;
  const gbp = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' });
  const money = cents => gbp.format((cents || 0) / 100);

  const setStat = (key, text) => {
    const el = card.querySelector('[data-hcb="' + key + '"]');
    if (el) { el.textContent = text; el.classList.remove('is-loading'); }
  };

  const fmtDate = iso => {
    const d = new Date(iso);
    return isNaN(d) ? '' : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
  };

  fetch(api)
    .then(r => r.ok ? r.json() : Promise.reject(r.status))
    .then(org => {
      const b = org.balances || {};
      setStat('balance', money(b.balance_cents));
      setStat('raised', money(b.total_raised));
    })
    .catch(() => {
      setStat('balance', '—');
      setStat('raised', '—');
    });

  const feed = card.querySelector('[data-hcb="transactions"]');
  if (feed) {
    fetch(api + '/transactions?per_page=5')
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(txns => {
        if (!Array.isArray(txns) || !txns.length) {
          feed.innerHTML = '<li class="finance-feed-empty">No transactions yet.</li>';
          return;
        }
        feed.innerHTML = txns.map(t => {
          const incoming = (t.amount_cents || 0) > 0;
          const sign = incoming ? '+' : '−';
          const amount = sign + money(Math.abs(t.amount_cents));
          const memo = (t.memo || 'Transaction').replace(/[<>]/g, '');
          return '<li>' +
            '<span class="finance-feed-memo">' +
              '<span class="finance-feed-name">' + memo + '</span>' +
              '<span class="finance-feed-date">' + fmtDate(t.date) + '</span>' +
            '</span>' +
            '<span class="finance-feed-amount' + (incoming ? ' is-in' : '') + '">' + amount + '</span>' +
          '</li>';
        }).join('');
      })
      .catch(() => {
        feed.innerHTML = '<li class="finance-feed-empty">Live feed unavailable — view it on HCB.</li>';
      });
  }
});
