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

// === STICKER HUNT MINIGAME ===
// Four named mascot stickers are hidden across the site. Click
// all of them, erupt the volcano, then survive the cookie terms
// and conditions to claim your cookie. Fully static: progress is
// localStorage, the reward is document.cookie.
(function () {
  const TARGETS = ['m1', 'm2', 'm3', 'm4'];
  const NAMES = { m1: 'Volcy', m2: 'Happy', m3: 'Grumpy', m4: 'Orbitty' };
  const HINTS = {
    m1: 'hot-headed, near the machine',
    m2: 'watching the money',
    m3: 'with the crew',
    m4: 'orbiting this season'
  };
  const LS_FOUND = 'vx-hunt-found';
  const LS_DONE = 'vx-hunt-cookie';

  function load() {
    try { return JSON.parse(localStorage.getItem(LS_FOUND)) || []; }
    catch (e) { return []; }
  }
  function save(found) { localStorage.setItem(LS_FOUND, JSON.stringify(found)); }
  const cookieEarned = () => localStorage.getItem(LS_DONE) === '1';

  document.addEventListener('DOMContentLoaded', function () {
    let found = load().filter(id => TARGETS.includes(id));
    let hunt, tab, slots, statusEl;

    function buildWidget() {
      hunt = document.createElement('div');
      hunt.className = 'hunt';
      hunt.innerHTML =
        '<button class="hunt-tab" type="button" aria-expanded="false"><span></span></button>' +
        '<div class="hunt-panel" role="region" aria-label="Sticker hunt progress">' +
          '<h5>The Sticker Hunt</h5>' +
          '<p class="hunt-hint">Four mascot stickers are hidden across the site. Only one of each exists. Click them when you spot them.</p>' +
          '<div class="hunt-slots">' +
            TARGETS.map(id =>
              '<div class="hunt-slot" data-slot="' + id + '" title="' + HINTS[id] + '">' +
                '<img src="mascots/' + id + '-cut.png" alt="">' +
                '<span class="hunt-slot-name">' + NAMES[id] + '</span>' +
              '</div>').join('') +
          '</div>' +
          '<div class="hunt-status"></div>' +
          '<button class="hunt-reset" type="button">start the hunt again</button>' +
        '</div>';
      document.body.appendChild(hunt);

      tab = hunt.querySelector('.hunt-tab');
      slots = hunt.querySelectorAll('.hunt-slot');
      statusEl = hunt.querySelector('.hunt-status');

      tab.addEventListener('click', function () {
        hunt.classList.toggle('open');
        tab.setAttribute('aria-expanded', hunt.classList.contains('open'));
      });
      hunt.querySelector('.hunt-reset').addEventListener('click', function () {
        found = [];
        save(found);
        localStorage.removeItem(LS_DONE);
        render();
      });
      render();
    }

    function render() {
      tab.querySelector('span').textContent = 'Sticker Hunt ' + found.length + '/' + TARGETS.length;
      tab.classList.toggle('all-found', found.length === TARGETS.length && !cookieEarned());
      slots.forEach(slot => {
        slot.classList.toggle('found', found.includes(slot.getAttribute('data-slot')));
      });
      if (cookieEarned()) {
        statusEl.textContent = 'Volcano erupted. Cookie accepted. You are a legend.';
      } else if (found.length === TARGETS.length) {
        statusEl.innerHTML = '';
        const btn = document.createElement('button');
        btn.className = 'hunt-erupt';
        btn.type = 'button';
        btn.textContent = 'Erupt the volcano';
        btn.addEventListener('click', erupt);
        statusEl.appendChild(btn);
      } else {
        const left = TARGETS.filter(id => !found.includes(id));
        statusEl.textContent = 'Still hiding: ' + left.map(id => NAMES[id]).join(', ') + '.';
      }
    }

    document.querySelectorAll('[data-hunt]').forEach(el => {
      const id = el.getAttribute('data-hunt');
      if (!TARGETS.includes(id)) return;
      el.setAttribute('title', 'A wild sticker');
      el.addEventListener('click', function (e) {
        if (found.includes(id)) return; // already collected; links behave normally
        e.preventDefault();
        e.stopPropagation();
        found.push(id);
        save(found);
        el.classList.add('hunt-found-pop');
        setTimeout(() => el.classList.remove('hunt-found-pop'), 600);
        hunt.classList.add('open');
        render();
      });
    });

    // --- the cookie terms and conditions ---
    function tncHTML() {
      const sections = [
        ['1. Definitions', '"The Cookie" means one (1) virtual chocolate-chip cookie, freshly erupted. "You" means the person who clicked four stickers instead of doing something productive. "The Volcano" means the Volcano. "The Team" means KCLMS Volcanix, its members, mascots (Volcy, Happy, Grumpy and Orbitty), successors, and whichever parent is driving us to the qualifier.'],
        ['2. Grant of Cookie', 'Subject to your full and unconditional acceptance of these terms, the Volcano grants you a non-exclusive, non-transferable, non-refundable, non-edible licence to one Cookie. The Cookie may not be sublicensed, resold, or dunked in milk you do not own.'],
        ['3. Eruption Disclaimer', 'The eruption you witnessed was performed by a trained volcano. Do not attempt at home, at school, or inside the pit area at a FIRST Tech Challenge event, where open magma is a clear violation of the pit safety rules.'],
        ['4. Browser Cookie Clause', 'By accepting, you consent to us setting exactly one (1) real browser cookie named volcanix_cookie. It contains the word "earned". It does not track you. Frankly, it does not do anything. It is simply proud of you.'],
        ['5. Nutritional Information', 'The Cookie contains zero calories, zero grams of sugar, and zero cookies. Serving size: one screen. May contain traces of pixels and gracious professionalism.'],
        ['6. Warranty', 'THE COOKIE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF CRUNCHINESS, CHEWINESS, OR FITNESS FOR A PARTICULAR TEATIME.'],
        ['7. Mecanum Clause', 'You acknowledge that mecanum wheels allow omnidirectional movement and that this fact, while unrelated to cookies, is extremely cool and deserved a clause of its own.'],
        ['8. Odometry of the Heart', 'The Team accepts no liability for any drift, slippage, or loss of localisation you may experience upon realising the Cookie is not real. Recalibrate and carry on.'],
        ['9. Open Source Provision', 'Like everything else we make, the Cookie is open source. You may fork the Cookie. You may not eat the fork.'],
        ['10. Sticker Repatriation', 'Volcy, Happy, Grumpy and Orbitty remain the intellectual property of the Team. Clicking them does not constitute adoption, though they do appreciate the attention.'],
        ['11. Dispute Resolution', 'Any disputes arising from or relating to the Cookie shall be settled by a best-of-three match of rock, paper, scissors at the nearest available robotics venue. The robot referees. The robot is always right.'],
        ['12. Termination', 'This licence terminates automatically if you (a) clear your browser storage, (b) press "start the hunt again", or (c) claim the Cookie is a biscuit in a legally binding tone of voice.'],
        ['13. Severability', 'If any clause of these terms is found to be unenforceable, too silly, or eaten, the remaining clauses shall continue at full crunch.'],
        ['14. Entire Agreement', 'These terms constitute the entire agreement between you and the Volcano, superseding all prior eruptions, oral or written, including anything the Volcano may have promised you in a dream.']
      ];
      let html = sections.map(s => '<h6>' + s[0] + '</h6><p>' + s[1] + '</p>').join('');
      for (let i = 15; i <= 38; i++) {
        html += '<h6>' + i + '. Additional Provision ' + String.fromCharCode(64 + (i % 26 || 26)) + '</h6>' +
          '<p>The party of the first part (the Volcano) and the party of the second part (you, the sticker hunter) hereby further agree, affirm, ratify and generally nod along that provision ' + i +
          ' applies in full, notwithstanding provision ' + (i - 1) + ', except on competition days, during autonomous, or whenever the flywheel is spinning at target velocity, whichever occurs first.</p>';
      }
      html += '<p class="tnc-end">You reached the bottom. Legally impressive. The Accept button now works.</p>';
      return html;
    }

    function showTnc(overlay) {
      const tnc = document.createElement('div');
      tnc.className = 'tnc';
      tnc.innerHTML =
        '<div class="tnc-panel" role="dialog" aria-label="Cookie terms and conditions">' +
          '<h4>Cookie Terms &amp; Conditions</h4>' +
          '<p class="tnc-sub">Please read all 38 provisions carefully. Scroll to the bottom to unlock acceptance. This is the law.</p>' +
          '<div class="tnc-box">' + tncHTML() + '</div>' +
          '<div class="tnc-actions">' +
            '<button class="btn btn-primary tnc-accept" type="button" disabled><span>Accept cookies</span></button>' +
            '<button class="btn btn-ghost tnc-decline" type="button"><span>Decline</span></button>' +
          '</div>' +
          '<p class="tnc-note">By scrolling you agree that scrolling constitutes reading.</p>' +
        '</div>';
      overlay.appendChild(tnc);

      const box = tnc.querySelector('.tnc-box');
      const accept = tnc.querySelector('.tnc-accept');
      const decline = tnc.querySelector('.tnc-decline');

      box.addEventListener('scroll', function () {
        if (box.scrollTop + box.clientHeight >= box.scrollHeight - 12) {
          accept.removeAttribute('disabled');
        }
      });

      const refusals = ['Decline', 'Are you sure?', 'The Volcano is watching', 'Grumpy is disappointed', 'Fine. No cookie. Ever.', 'Decline'];
      let ri = 0;
      decline.addEventListener('click', function () {
        ri = (ri + 1) % refusals.length;
        decline.querySelector('span').textContent = refusals[ri];
      });

      accept.addEventListener('click', function () {
        if (accept.hasAttribute('disabled')) return;
        document.cookie = 'volcanix_cookie=earned; max-age=31536000; path=/; SameSite=Lax';
        localStorage.setItem(LS_DONE, '1');
        tnc.remove();
        const doneMsg = overlay.querySelector('.eruption-reward');
        doneMsg.innerHTML =
          '<img class="cookie-img" src="media/cookie-cut.png" alt="Your cookie">' +
          '<h3>Cookie accepted!!</h3>' +
          '<p>One browser cookie has been set, as per provision 4. Thank you for reading all 38 provisions. We both know you scrolled.</p>' +
          '<button class="btn btn-primary" type="button"><span>Return to the website</span></button>';
        doneMsg.querySelector('button').addEventListener('click', function () {
          overlay.remove();
          document.body.style.overflow = '';
          render();
        });
      });
    }

    // --- the eruption ---
    function erupt() {
      const overlay = document.createElement('div');
      overlay.className = 'eruption rumble';
      overlay.innerHTML = '<div class="crater-glow"></div><img class="volcano-img" src="media/volcano.png" alt="The volcano">';
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';

      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const colors = ['#facc57', '#f7b35b', '#e57c41', '#d93e36'];
      let stopped = false;

      function spawnLava() {
        if (stopped || reduced) return;
        const bit = document.createElement('div');
        bit.className = 'lava-bit';
        bit.style.background = colors[Math.floor(Math.random() * colors.length)];
        const s = 6 + Math.random() * 14;
        bit.style.width = s + 'px';
        bit.style.height = s + 'px';
        overlay.appendChild(bit);
        const dx = (Math.random() - 0.5) * window.innerWidth * 0.9;
        const up = 200 + Math.random() * (window.innerHeight * 0.5);
        const dur = 1100 + Math.random() * 900;
        bit.animate([
          { transform: 'translate(0, 0) rotate(0deg)', opacity: 1 },
          { transform: 'translate(' + dx * 0.5 + 'px, ' + (-up) + 'px) rotate(200deg)', opacity: 1, offset: 0.45 },
          { transform: 'translate(' + dx + 'px, 60px) rotate(420deg)', opacity: 0 }
        ], { duration: dur, easing: 'cubic-bezier(0.2, 0.8, 0.6, 1)' }).onfinish = () => bit.remove();
        setTimeout(spawnLava, 30 + Math.random() * 50);
      }
      spawnLava();

      setTimeout(function () {
        stopped = true;
        overlay.classList.remove('rumble');
        const reward = document.createElement('div');
        reward.className = 'eruption-reward';
        reward.innerHTML =
          '<img class="cookie-img" src="media/cookie-cut.png" alt="A cookie">' +
          '<h3>The volcano erupted!!</h3>' +
          '<p>It produced exactly one cookie. To claim it, you must first accept the cookie terms and conditions. All of them.</p>' +
          '<button class="btn btn-primary" type="button"><span>Claim the cookie</span></button>';
        overlay.appendChild(reward);
        requestAnimationFrame(() => reward.classList.add('show'));
        reward.querySelector('button').addEventListener('click', function () {
          showTnc(overlay);
        });
      }, reduced ? 600 : 4200);
    }

    buildWidget();
  });
})();
