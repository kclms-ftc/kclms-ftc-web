// KCLMS VOLCANIX — interactive behaviour
// =======================================

// === HERO CAROUSEL ===
// Crossfade between slides (0.7s opacity handled in CSS).
document.addEventListener('DOMContentLoaded', function () {
  const slides = document.querySelectorAll('.hero-slide');
  if (slides.length < 2) return;
  let current = 0;
  setInterval(function () {
    slides[current].classList.remove('active');
    current = (current + 1) % slides.length;
    slides[current].classList.add('active');
  }, 5000);
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

const counterObserver = new IntersectionObserver(function (entries) {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    const target = parseInt(entry.target.getAttribute('data-target'), 10);
    if (!isNaN(target)) animateCounter(entry.target, target);
    counterObserver.unobserve(entry.target);
  });
}, { threshold: 0.4 });

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.stat-number[data-target]').forEach(el => counterObserver.observe(el));
});

// === ACTIVE NAV LINK ===
document.addEventListener('DOMContentLoaded', function () {
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(link => {
    if (link.getAttribute('href') === current) link.classList.add('active');
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
