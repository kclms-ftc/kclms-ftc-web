// KCLMS VOLCANIX - interactive behaviour
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

// === SCROLL REVEAL ===
// Directional entrances for anything tagged .reveal.
document.addEventListener('DOMContentLoaded', function () {
  const items = document.querySelectorAll('.reveal');
  if (!items.length) return;
  if (!('IntersectionObserver' in window)) {
    items.forEach(el => el.classList.add('in'));
    return;
  }
  const revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('in');
      revealObserver.unobserve(entry.target);
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
  items.forEach(el => revealObserver.observe(el));
});

// === HCB OPEN FINANCES (live) ===
document.addEventListener('DOMContentLoaded', function () {
  const card = document.querySelector('[data-hcb-slug]');
  if (!card) return;

  const slug = card.getAttribute('data-hcb-slug');
  const api = 'https://hcb.hackclub.com/api/v3/organizations/' + slug;
  // HCB amounts are in USD cents
  const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
  const money = cents => usd.format((cents || 0) / 100);

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
      setStat('balance', '…');
      setStat('raised', '…');
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
          const sign = incoming ? '+' : '-';
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
        feed.innerHTML = '<li class="finance-feed-empty">Live feed unavailable. View it on HCB.</li>';
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
  const NAMES = { m1: 'The Blaze', m2: 'The Warmth', m3: 'The Smoulder', m4: 'The Spark' };
  const HINTS = {
    m1: 'hot-headed, next to the paperwork',
    m2: 'watching the money',
    m3: 'at the bottom of everything',
    m4: 'orbiting this season'
  };
  // The four hidden stickers are not four mascots — they are the four
  // MOODS Fireboy's flame burns in. Collect all four and the flame is
  // whole again. Bestiary entries for the Codex.
  const LORE = {
    m1: { epithet: 'Fireboy at full burn', domain: 'the machine when it runs hot', creed: '"Run it hotter. Then check your wiring."' },
    m2: { epithet: 'Fireboy at his kindest', domain: 'the team, the books, the morale', creed: '"Accounted for &mdash; and cheerfully so."' },
    m3: { epithet: 'Fireboy banked low', domain: 'the long grind, the foundation', creed: '"Level starts at the base, not the top."' },
    m4: { epithet: 'Fireboy catching', domain: "this season's orbit", creed: '"I go around, so the team goes forward."' }
  };
  const LS_FOUND = 'vx-hunt-found';
  const LS_DONE = 'vx-hunt-cookie';
  const LS_ALIGNED = 'vx-aligned';

  // Every tilted "sticker" on the site. The wonk toggle straightens
  // these one at a time; winning the calibration straightens the lot.
  const WONK_SELECTOR = '.block-media img, .team-card, .gallery img, .sponsor-logos li';

  function load() {
    try { return JSON.parse(localStorage.getItem(LS_FOUND)) || []; }
    catch (e) { return []; }
  }
  function save(found) { localStorage.setItem(LS_FOUND, JSON.stringify(found)); }
  const cookieEarned = () => localStorage.getItem(LS_DONE) === '1';
  const worldAligned = () => localStorage.getItem(LS_ALIGNED) === '1';

  // --- humorous toast, bottom-centre, auto-dismiss ---
  function toast(msg) {
    const t = document.createElement('div');
    t.className = 'vx-toast';
    t.innerHTML = msg;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => {
      t.classList.remove('show');
      setTimeout(() => t.remove(), 400);
    }, 5200);
  }

  // Snap (or release) every crooked frame on the page. Reuses the
  // wonk toggle's .straightened class so hover/press states still work.
  function setAligned(on) {
    document.body.classList.toggle('world-aligned', on);
    document.querySelectorAll(WONK_SELECTOR).forEach(el => {
      el.classList.toggle('straightened', on);
    });
  }
  function alignWorld() {
    localStorage.setItem(LS_ALIGNED, '1');
    setAligned(true);
    toast('&#127777; <b>Reality recalibrated.</b> Odometry error: 0.0&deg;. You may now gaze upon straight things without discomfort.');
  }
  function driftWorld() {
    localStorage.removeItem(LS_ALIGNED);
    setAligned(false);
    toast('&#127756; <b>The Great Wonk returns.</b> Every line drifts 1&deg; off true, as nature intended.');
  }

  // --- Volcano Arcade state: best scores + the Grand Aligner unlock ---
  const LS_SCORES = 'vx-arcade';
  const LS_GRAND = 'vx-grand';
  function loadScores() {
    try { return JSON.parse(localStorage.getItem(LS_SCORES)) || {}; }
    catch (e) { return {}; }
  }
  function saveScores(s) { localStorage.setItem(LS_SCORES, JSON.stringify(s)); }
  // Booleans latch true; numbers keep the best.
  function recordScore(key, val) {
    const s = loadScores();
    if (typeof val === 'boolean') s[key] = s[key] || val;
    else s[key] = Math.max(s[key] || 0, val);
    saveScores(s);
    checkGrand();
    return s;
  }
  const SIMON_CLEAR = 5, WHACK_CLEAR = 20, FLAME_CLEAR = 22;
  function clears() {
    const s = loadScores();
    return {
      calib: worldAligned(),
      rps: !!s.rps,
      simon: (s.simon || 0) >= SIMON_CLEAR,
      whack: (s.whack || 0) >= WHACK_CLEAR,
      flame: (s.flame || 0) >= FLAME_CLEAR
    };
  }
  function allCleared() {
    const c = clears();
    return c.calib && c.rps && c.simon && c.whack && c.flame;
  }
  const grandAligner = () => localStorage.getItem(LS_GRAND) === '1';
  function checkGrand() {
    if (allCleared() && !grandAligner()) {
      localStorage.setItem(LS_GRAND, '1');
      return true;
    }
    return false;
  }

  document.addEventListener('DOMContentLoaded', function () {
    let found = load().filter(id => TARGETS.includes(id));
    let hunt, tab, slots, statusEl;

    // If reality was calibrated on a previous visit, keep it level.
    if (worldAligned()) setAligned(true);

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
      tab.classList.toggle('grand', grandAligner());
      if (cookieEarned()) {
        statusEl.innerHTML = '';
        const line = document.createElement('p');
        line.className = 'hunt-done-line';
        line.textContent = grandAligner()
          ? 'Keeper of the Flame. Every game cleared.'
          : worldAligned()
            ? 'Cookie claimed. Reality calibrated to 0.0°.'
            : 'Cookie claimed. Reality still drifts 1° off true.';
        statusEl.appendChild(line);

        const arcade = document.createElement('button');
        arcade.className = 'hunt-erupt';
        arcade.type = 'button';
        arcade.textContent = 'Open the Volcano Arcade';
        arcade.addEventListener('click', function () { showArcade(); });
        statusEl.appendChild(arcade);

        const codex = document.createElement('button');
        codex.className = 'hunt-reset';
        codex.type = 'button';
        codex.textContent = 'read the Volcanix Codex';
        codex.addEventListener('click', showCodex);
        statusEl.appendChild(codex);

        if (worldAligned()) {
          const drift = document.createElement('button');
          drift.className = 'hunt-reset';
          drift.type = 'button';
          drift.textContent = 'let reality drift again';
          drift.addEventListener('click', function () { driftWorld(); render(); });
          statusEl.appendChild(drift);
        } else {
          const recal = document.createElement('button');
          recal.className = 'hunt-erupt';
          recal.type = 'button';
          recal.textContent = 'Re-run the calibration';
          recal.addEventListener('click', function () {
            const overlay = openStage();
            showCalibration(overlay);
          });
          statusEl.appendChild(recal);
        }
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
        ['1. Definitions', '"The Cookie" means one (1) virtual chocolate-chip cookie, freshly erupted. "You" means the person who found and clicked all four stickers. "The Volcano" means the Volcano. "The Team" means KCLMS Volcanix, its members, Fireboy (in all four of his moods), successors, and whichever parent is driving us to the qualifier.'],
        ['2. Grant of Cookie', 'Subject to your full and unconditional acceptance of these terms, the Volcano grants you a non-exclusive, non-transferable, non-refundable, non-edible licence to one Cookie. The Cookie may not be sublicensed, resold, or dunked in milk you do not own.'],
        ['3. Eruption Disclaimer', 'The eruption you witnessed was performed by a trained volcano. Do not attempt at home, at school, or inside the pit area at a FIRST Tech Challenge event, where open magma is a clear violation of the pit safety rules.'],
        ['4. Browser Cookie Clause', 'By accepting, you consent to us setting exactly one (1) real browser cookie named volcanix_cookie. Its value is the word "earned". It stores nothing else and is not used for tracking.'],
        ['5. Nutritional Information', 'The Cookie contains zero calories, zero grams of sugar, and zero cookies. Serving size: one screen. May contain traces of pixels and gracious professionalism.'],
        ['6. Warranty', 'THE COOKIE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF CRUNCHINESS, CHEWINESS, OR FITNESS FOR A PARTICULAR TEATIME.'],
        ['7. Mecanum Clause', 'You acknowledge that mecanum wheels allow omnidirectional movement, a fact recorded here for completeness despite having no bearing on the Cookie.'],
        ['8. Odometry of the Heart', 'The Team accepts no liability for any drift, slippage, or loss of localisation you may experience upon realising the Cookie is not real.'],
        ['9. Open Source Provision', 'Like everything else we make, the Cookie is open source and may be forked under the same licence as our code.'],
        ['10. Sticker Repatriation', 'Fireboy and all four of his moods remain the intellectual property of the Team. Clicking them does not constitute adoption, though they do appreciate the attention.'],
        ['11. Dispute Resolution', 'Any disputes arising from or relating to the Cookie shall be settled by a best-of-three match of rock, paper, scissors at the nearest available robotics venue, refereed by the robot.'],
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
      html += '<p class="tnc-end">You have reached the bottom. The Accept button is now enabled.</p>';
      return html;
    }

    function showTnc(overlay) {
      const tnc = document.createElement('div');
      tnc.className = 'tnc';
      tnc.innerHTML =
        '<div class="tnc-panel" role="dialog" aria-label="Cookie terms and conditions">' +
          '<h4>Cookie Terms &amp; Conditions</h4>' +
          '<p class="tnc-sub">Please read all 38 provisions carefully. Acceptance unlocks once you have scrolled to the bottom.</p>' +
          '<div class="tnc-box">' + tncHTML() + '</div>' +
          '<div class="tnc-actions">' +
            '<button class="btn solid tnc-accept" type="button" disabled><span>Accept cookies</span></button>' +
            '<button class="btn ghost tnc-decline" type="button"><span>Decline</span></button>' +
          '</div>' +
          '<p class="tnc-note">Scrolling to the bottom is treated as reading in full.</p>' +
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

      const refusals = ['Decline', 'Are you sure?', 'The Volcano is watching', 'The Smoulder is disappointed', 'Provision 11 may apply', 'Decline'];
      let ri = 0, disputeShown = false;
      decline.addEventListener('click', function () {
        ri = (ri + 1) % refusals.length;
        decline.querySelector('span').textContent = refusals[ri];
        if (!disputeShown && ri >= 2) {
          disputeShown = true;
          const dispute = document.createElement('button');
          dispute.className = 'btn ghost tnc-dispute';
          dispute.type = 'button';
          dispute.innerHTML = '<span>Settle it &mdash; Provision 11</span>';
          dispute.addEventListener('click', function () { showDispute(overlay, tnc); });
          tnc.querySelector('.tnc-actions').appendChild(dispute);
        }
      });

      accept.addEventListener('click', function () {
        if (accept.hasAttribute('disabled')) return;
        grantCookie();
        showCalibration(overlay, tnc);
      });
    }

    // Set the one real browser cookie (Provision 4) + mark done.
    function grantCookie() {
      document.cookie = 'volcanix_cookie=earned; max-age=31536000; path=/; SameSite=Lax';
      localStorage.setItem(LS_DONE, '1');
    }

    // A bare dark stage, used when re-running the calibration later
    // (no eruption needed the second time around).
    function openStage() {
      const overlay = document.createElement('div');
      overlay.className = 'eruption';
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';
      return overlay;
    }

    function closeStage(overlay) {
      overlay.remove();
      document.body.style.overflow = '';
      render();
    }

    // --- PROVISION 11: dispute resolution, best-of-three rock/paper/
    // scissors, refereed by the robot. Declining the cookie invokes it. ---
    function showDispute(overlay, tnc, back) {
      if (tnc) tnc.remove();
      const leaveTo = back || function () { closeStage(overlay); };
      const wrap = document.createElement('div');
      wrap.className = 'tnc rps';
      const MOVES = { rock: 'Rock', paper: 'Paper', scissors: 'Scissors' };
      const BEATS = { rock: 'scissors', paper: 'rock', scissors: 'paper' };
      const ICON = { rock: '&#9994;', paper: '&#9995;', scissors: '&#9986;' };
      let you = 0, bot = 0;
      wrap.innerHTML =
        '<div class="tnc-panel rps-panel" role="dialog" aria-label="Provision 11 dispute">' +
          '<h4>Provision 11 &mdash; Dispute Resolution</h4>' +
          '<p class="tnc-sub">Best of three. Rock, paper, scissors. The robot referees, and also plays. Yes, that is a conflict of interest.</p>' +
          '<div class="rps-score"><span class="rps-you">You 0</span><span class="rps-bot">Robot 0</span></div>' +
          '<div class="rps-stage"><span class="rps-hand rps-hand-you">&#9994;</span><span class="rps-vs">vs</span><span class="rps-hand rps-hand-bot">&#9994;</span></div>' +
          '<p class="rps-call">Throw a move.</p>' +
          '<div class="rps-moves">' +
            Object.keys(MOVES).map(m => '<button class="btn ghost rps-move" type="button" data-move="' + m + '"><span>' + ICON[m] + ' ' + MOVES[m] + '</span></button>').join('') +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);

      const scoreYou = wrap.querySelector('.rps-you');
      const scoreBot = wrap.querySelector('.rps-bot');
      const handYou = wrap.querySelector('.rps-hand-you');
      const handBot = wrap.querySelector('.rps-hand-bot');
      const call = wrap.querySelector('.rps-call');
      const moves = wrap.querySelectorAll('.rps-move');

      function finish(win) {
        wrap.querySelector('.rps-moves').innerHTML = '';
        const btn = document.createElement('button');
        btn.className = 'btn solid';
        btn.type = 'button';
        if (win) {
          grantCookie();
          recordScore('rps', true);
          call.innerHTML = '<b>The robot concedes.</b> The dispute is resolved in your favour. The cookie is yours after all.';
          if (back) {
            btn.innerHTML = '<span>&larr; Arcade</span>';
            btn.addEventListener('click', back);
          } else {
            btn.innerHTML = '<span>Claim the cookie</span>';
            btn.addEventListener('click', function () { showCalibration(overlay, wrap); });
          }
        } else {
          call.innerHTML = '<b>The robot keeps the cookie.</b> The Smoulder nods slowly. Reality remains 1&deg; off true.';
          btn.innerHTML = '<span>Try the dispute again</span>';
          btn.addEventListener('click', function () { showDispute(overlay, wrap, back); });
        }
        wrap.querySelector('.rps-moves').appendChild(btn);
        const leave = document.createElement('button');
        leave.className = 'btn ghost';
        leave.type = 'button';
        leave.innerHTML = back ? '<span>&larr; Arcade</span>' : '<span>Return to the website</span>';
        leave.addEventListener('click', leaveTo);
        wrap.querySelector('.rps-moves').appendChild(leave);
      }

      moves.forEach(mv => mv.addEventListener('click', function () {
        const pick = mv.getAttribute('data-move');
        const keys = Object.keys(MOVES);
        const robo = keys[Math.floor(Math.random() * keys.length)];
        handYou.innerHTML = ICON[pick];
        handBot.innerHTML = ICON[robo];
        handYou.classList.remove('shake'); void handYou.offsetWidth; handYou.classList.add('shake');
        handBot.classList.remove('shake'); void handBot.offsetWidth; handBot.classList.add('shake');
        let line;
        if (pick === robo) line = 'A tie. The robot recalculates.';
        else if (BEATS[pick] === robo) { you++; line = 'You take the round.'; }
        else { bot++; line = 'The robot takes the round.'; }
        scoreYou.textContent = 'You ' + you;
        scoreBot.textContent = 'Robot ' + bot;
        call.textContent = line;
        if (you === 2) finish(true);
        else if (bot === 2) finish(false);
      }));
    }

    // --- THE CALIBRATION: freeze a wobbling level bar near 0deg.
    // Two hits out of three within tolerance recalibrates reality. ---
    function showCalibration(overlay, prev, back) {
      if (prev) prev.remove();
      const leaveTo = back || function () { closeStage(overlay); };
      const TOL = 6;        // degrees of slack for a "level" hit
      const NEED = 2;       // hits required
      const ROUNDS = 3;
      const wrap = document.createElement('div');
      wrap.className = 'tnc calib';
      wrap.innerHTML =
        '<div class="tnc-panel calib-panel" role="dialog" aria-label="The Calibration">' +
          '<h4>The Calibration</h4>' +
          '<p class="tnc-sub">The cookie is zeroed odometry. Spend it: freeze the level bar within ' + TOL + '&deg; of true. ' + NEED + ' of ' + ROUNDS + ' hits recalibrates reality.</p>' +
          '<div class="calib-gauge">' +
            '<div class="calib-zone"></div>' +
            '<div class="calib-bar"></div>' +
            '<div class="calib-readout">&mdash;&deg;</div>' +
          '</div>' +
          '<p class="calib-progress">Round 1 of ' + ROUNDS + ' &middot; hits 0/' + NEED + '</p>' +
          '<div class="calib-actions">' +
            '<button class="btn solid calib-lock" type="button"><span>Level it</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);

      const bar = wrap.querySelector('.calib-bar');
      const readout = wrap.querySelector('.calib-readout');
      const progress = wrap.querySelector('.calib-progress');
      const lock = wrap.querySelector('.calib-lock');
      const zone = wrap.querySelector('.calib-zone');
      zone.style.setProperty('--tol', TOL);

      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      let round = 1, hits = 0, running = true, raf = 0;
      const AMP = 42;       // swing amplitude in degrees
      const speed = () => 0.0016 + round * 0.0004;   // gets harder each round
      const start = performance.now();
      let phase = Math.random() * Math.PI * 2;

      function angle(now) { return AMP * Math.sin((now - start) * speed() + phase); }

      function tick(now) {
        if (!running) return;
        const a = angle(now);
        bar.style.transform = 'rotate(' + a.toFixed(1) + 'deg)';
        bar.classList.toggle('level', Math.abs(a) <= TOL);
        raf = requestAnimationFrame(tick);
      }
      if (reduced) {
        // No animation: give a click-timed pseudo-random angle instead.
        bar.style.transform = 'rotate(0deg)';
      } else {
        raf = requestAnimationFrame(tick);
      }

      function outcome(win) {
        running = false;
        cancelAnimationFrame(raf);
        wrap.querySelector('.calib-actions').innerHTML = '';
        const cont = document.createElement('button');
        cont.className = 'btn solid';
        cont.type = 'button';
        if (win) {
          alignWorld();
          bar.style.transform = 'rotate(0deg)';
          bar.classList.add('level');
          progress.innerHTML = '<b>Calibrated.</b> The drift is gone.';
          wrap.querySelector('.tnc-sub').innerHTML =
            'Every crooked frame on this site just snapped to true &mdash; and will stay that way across every page until you choose to let it drift again. Provision 4 cookie: set. Gracious professionalism: level.';
          cont.innerHTML = back ? '<span>&larr; Arcade</span>' : '<span>Enter the Volcano Arcade</span>';
          cont.addEventListener('click', back || function () { showArcade(overlay, wrap); });
          wrap.querySelector('.calib-actions').appendChild(cont);
          if (!back) {
            const behold = document.createElement('button');
            behold.className = 'btn ghost';
            behold.type = 'button';
            behold.innerHTML = '<span>Behold the straight world</span>';
            behold.addEventListener('click', function () { closeStage(overlay); });
            wrap.querySelector('.calib-actions').appendChild(behold);
          }
        } else {
          progress.innerHTML = '<b>Not level.</b> The Smoulder exhales through his nose.';
          wrap.querySelector('.tnc-sub').innerHTML =
            'The cookie holds. You keep it &mdash; but reality stays 1&deg; off true. You can straighten frames by hand (click them), or try the calibration again.';
          cont.innerHTML = '<span>Try again</span>';
          cont.addEventListener('click', function () { showCalibration(overlay, wrap, back); });
          wrap.querySelector('.calib-actions').appendChild(cont);
          const leave = document.createElement('button');
          leave.className = 'btn ghost';
          leave.type = 'button';
          leave.innerHTML = back ? '<span>&larr; Arcade</span>' : '<span>Keep the wonk, return</span>';
          leave.addEventListener('click', leaveTo);
          wrap.querySelector('.calib-actions').appendChild(leave);
        }
      }

      lock.addEventListener('click', function () {
        if (!running) return;
        const a = reduced ? (Math.random() * AMP * 2 - AMP) : angle(performance.now());
        readout.innerHTML = (a >= 0 ? '+' : '') + a.toFixed(1) + '&deg;';
        const good = Math.abs(a) <= TOL;
        readout.classList.toggle('good', good);
        readout.classList.toggle('bad', !good);
        if (good) hits++;
        if (round >= ROUNDS || hits >= NEED) {
          setTimeout(() => outcome(hits >= NEED), 650);
          running = false;
          cancelAnimationFrame(raf);
          return;
        }
        round++;
        phase = Math.random() * Math.PI * 2;
        progress.textContent = 'Round ' + round + ' of ' + ROUNDS + ' · hits ' + hits + '/' + NEED;
      });
    }

    // --- THE VOLCANIX CODEX: an illuminated, chaptered field manual.
    // Gracious professionalism is its spine; the Great Wonk is only
    // the excuse to get you reading it. ---
    function showCodex() {
      const bestiary = TARGETS.map(id => {
        const l = LORE[id];
        const got = found.includes(id);
        return '<figure class="codex-beast' + (got ? ' got' : '') + '">' +
            '<img src="mascots/' + id + '-cut.png" alt="' + NAMES[id] + '">' +
            '<figcaption>' +
              '<span class="codex-beast-name">' + NAMES[id] + '</span>' +
              '<span class="codex-beast-epi">' + l.epithet + '</span>' +
              '<span class="codex-beast-dom">Keeps: ' + l.domain + '</span>' +
              '<span class="codex-beast-creed">' + l.creed + '</span>' +
            '</figcaption>' +
          '</figure>';
      }).join('');

      const whole = found.length === TARGETS.length;
      const trophyBlock = grandAligner()
        ? '<figure class="codex-trophy"><img src="media/fireboy-cut.gif" alt="Fireboy, whole again"><figcaption>Fireboy &mdash; whole, and yours.</figcaption></figure>' +
          '<p>You cleared every game in the Volcano Arcade. The flame is steady, the frames are level, and Fireboy stands complete on your shelf. There is no higher honour we can hand out. There is no shelf, either. Enjoy him anyway.</p>' +
          '<p class="codex-creed">Keeper of the Flame.</p>'
        : '<figure class="codex-trophy locked"><div class="codex-trophy-lock">&#128274;</div><figcaption>Trophy locked</figcaption></figure>' +
          '<p>Clear all five games in the <b>Volcano Arcade</b> and Fireboy &mdash; the whole animated mascot &mdash; becomes your trophy, displayed here forever. So far you have lit ' + (whole ? 'every' : 'some of the') + ' moods and started the work. Finish it.</p>';

      const chapters = [
        { tab: 'I · Fireboy', title: 'Fireboy', html:
          '<figure class="codex-hero"><img src="media/fireboy-cut.gif" alt="Fireboy, the mascot"></figure>' +
          '<p><span class="codex-drop">F</span>ireboy is the mascot. One small robot, built by the team, with a head that is not metal but living <b>flame</b>. The fire has burned since the first build season and it has never once gone out. He is the figure in our logo, and everything on this site belongs, in the end, to him.</p>' +
          '<p>The flame does not stay the same. It burns in <b>four moods</b>, and when Fireboy is at rest those moods wander off on their own &mdash; drifting across these pages as four small stickers, each the same fire wearing a different face. Find all four and the flame is whole again. That is the hunt you just finished.</p>' +
          '<p class="codex-aside">Yes, the whole site also leans one degree off true. Fireboy calls that <i>character</i>. The perfectionists on the team call it a bug. Both are right.</p>' },

        { tab: 'II · Moods', title: 'The Four Moods of the Flame', html:
          '<p>These are not four mascots. They are one flame in four tempers &mdash; the faces Fireboy&rsquo;s fire wears depending on the day, the deadline, and the score. You hunted them as stickers; here they are named.</p>' +
          '<div class="codex-bestiary">' + bestiary + '</div>' +
          '<p class="codex-aside">Grey faces are moods you have not yet found on the site. Go click them &mdash; the flame is not whole without all four.</p>' },

        { tab: 'III · The Creed', title: 'Gracious Professionalism', html:
          '<blockquote class="codex-quote">&ldquo;Gracious professionalism&hellip; a way of doing things that encourages high-quality work, emphasises the value of others, and respects individuals and the community.&rdquo;<cite>&mdash; Aichen Su, <span>KCLMS Volcanix</span></cite></blockquote>' +
          '<p>This is the north star of every FIRST team, and it is the real subject of this entire Codex. Everything else &mdash; Fireboy, the volcano, the cookie, the thirty-eight provisions &mdash; was theatre to bring you here.</p>' +
          '<p>Notice what the games actually asked of you. None of them handed you an attack button. You <i>straighten</i> a crooked frame; you <i>steady</i> a flame; you <i>repeat</i> a pattern with care. The lean was never a flaw to mock &mdash; it was an <b>invitation</b>. You fix a thing quietly, with a steady hand, and you leave it better than you found it. You compete fiercely and you stay kind. You beat the robot at rock-paper-scissors and you shake its hand anyway.</p>' +
          '<p><b>That is the whole game.</b> Fireboy&rsquo;s flame does not burn to destroy anything. It burns to keep the team warm. Carry that.</p>' +
          '<p class="codex-aside">Gracious professionalism is not being soft. It is being excellent <i>and</i> generous at the same time, on purpose, especially when no one is watching &mdash; which, on a hidden Easter egg, no one is.</p>' },

        { tab: 'IV · The Cookie', title: 'The Calibration Cookie', html:
          '<p>The volcano erupts exactly one cookie, and it is not for eating. It is <b>zeroed odometry</b> &mdash; a single perfect reading of true, pressed into chocolate-chip form &mdash; and Fireboy hands it to you personally. You spend it by swinging the level bar to 0.0&deg; with your own timing. Skill, not luck. Grace, not force.</p>' +
          '<p>The thirty-eight provisions you scrolled were real, in the sense that reading them was the point. Patience is the entry fee to precision. Provision 4 set one honest browser cookie named <code>volcanix_cookie</code>; it tracks nothing and it never will. Provision 11 let the robot referee its own dispute, which it lost graciously, as is tradition.</p>' +
          '<p class="codex-aside">Nutritional information: zero calories, zero sugar, zero cookies. Contains traces of pixels and gracious professionalism.</p>' },

        { tab: 'V · Trophy', title: 'The Trophy', html: trophyBlock +
          '<p class="codex-sign">Keep the flame steady.<br>Keep the frames level.<br>Stay kind while you win.<br>&mdash; KCLMS Volcanix</p>' }
      ];

      const overlay = document.createElement('div');
      overlay.className = 'eruption';
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';

      const badges =
        '<span class="codex-badge' + (found.length === TARGETS.length ? ' on' : '') + '">Moods ' + found.length + '/' + TARGETS.length + '</span>' +
        '<span class="codex-badge' + (cookieEarned() ? ' on' : '') + '">' + (cookieEarned() ? 'Cookie claimed' : 'Cookie pending') + '</span>' +
        '<span class="codex-badge' + (worldAligned() ? ' on' : '') + '">' + (worldAligned() ? 'Reality 0.0&deg;' : 'Reality 1.0&deg;') + '</span>';

      const wrap = document.createElement('div');
      wrap.className = 'tnc codex';
      wrap.innerHTML =
        '<div class="tnc-panel codex-panel" role="dialog" aria-label="The Volcanix Codex">' +
          '<div class="codex-head">' +
            '<div><h4>The Volcanix Codex</h4><div class="codex-badges">' + badges + '</div></div>' +
            '<button class="codex-close" type="button" aria-label="Close the Codex">&times;</button>' +
          '</div>' +
          '<div class="codex-body">' +
            '<nav class="codex-nav">' + chapters.map((c, i) =>
              '<button class="codex-chap" type="button" data-i="' + i + '">' + c.tab + '</button>').join('') + '</nav>' +
            '<div class="codex-page"></div>' +
          '</div>' +
          '<div class="codex-foot">' +
            '<button class="btn ghost codex-prev" type="button"><span>&larr; Prev</span></button>' +
            '<span class="codex-count"></span>' +
            '<button class="btn solid codex-next" type="button"><span>Next &rarr;</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);

      const page = wrap.querySelector('.codex-page');
      const chaps = wrap.querySelectorAll('.codex-chap');
      const count = wrap.querySelector('.codex-count');
      const prev = wrap.querySelector('.codex-prev');
      const next = wrap.querySelector('.codex-next');
      let idx = 0;

      function draw() {
        const c = chapters[idx];
        page.innerHTML = '<h5 class="codex-page-title">' + c.title + '</h5>' + c.html;
        page.classList.remove('turn'); void page.offsetWidth; page.classList.add('turn');
        page.scrollTop = 0;
        chaps.forEach((b, i) => b.classList.toggle('active', i === idx));
        count.innerHTML = 'Chapter ' + (idx + 1) + ' of ' + chapters.length;
        prev.disabled = idx === 0;
        // On the final chapter the "Next" button becomes the way out,
        // so the last page is never a dead end.
        const last = idx === chapters.length - 1;
        next.querySelector('span').innerHTML = last ? 'Close the Codex &#10003;' : 'Next &rarr;';
        next.disabled = false;
      }
      function go(i) { idx = Math.max(0, Math.min(chapters.length - 1, i)); draw(); }

      chaps.forEach(b => b.addEventListener('click', () => go(+b.getAttribute('data-i'))));
      prev.addEventListener('click', () => go(idx - 1));
      next.addEventListener('click', function () {
        if (idx === chapters.length - 1) close();
        else go(idx + 1);
      });

      function close() {
        document.removeEventListener('keydown', onKey);
        overlay.remove();
        document.body.style.overflow = '';
      }
      function onKey(e) {
        if (e.key === 'ArrowRight') { if (idx < chapters.length - 1) go(idx + 1); }
        else if (e.key === 'ArrowLeft') go(idx - 1);
        else if (e.key === 'Escape') close();
      }
      document.addEventListener('keydown', onKey);
      wrap.querySelector('.codex-close').addEventListener('click', close);
      overlay.addEventListener('click', e => { if (e.target === overlay) close(); });

      draw();
    }

    // === THE VOLCANO ARCADE =============================================
    // Hub for every minigame. Clearing all four unlocks Grand Aligner.
    function showArcade(overlay, prev) {
      if (prev) prev.remove();
      if (!overlay) overlay = openStage();
      // Clear any game panel we came back from.
      overlay.querySelectorAll('.tnc').forEach(n => n.remove());
      const back = function () { showArcade(overlay); };
      const c = clears();
      const s = loadScores();
      const grand = grandAligner();

      const GAMES = [
        { key: 'calib', icon: '&#128207;', name: 'The Calibration', blurb: 'Freeze the level bar at 0.0&deg;. Aligns reality.',
          status: c.calib ? 'Reality aligned' : 'Not yet level', play: () => showCalibration(overlay, arcadeWrap, back) },
        { key: 'rps', icon: '&#9994;', name: 'Provision 11', blurb: 'Rock, paper, scissors against the robot referee.',
          status: c.rps ? 'Dispute won' : 'Undisputed', play: () => showDispute(overlay, arcadeWrap, back) },
        { key: 'simon', icon: '&#128293;', name: 'Mood Sequence', blurb: 'Repeat Fireboy&rsquo;s growing pattern of moods from memory.',
          status: 'Best level ' + (s.simon || 0) + (c.simon ? ' ✓' : ' / ' + SIMON_CLEAR), play: () => gameSimon(overlay, back) },
        { key: 'whack', icon: '&#128296;', name: 'Wonk Patrol', blurb: 'Straighten crooked frames before they drift away. 30s.',
          status: 'Best ' + (s.whack || 0) + (c.whack ? ' ✓' : ' / ' + WHACK_CLEAR), play: () => gameWhack(overlay, back) },
        { key: 'flame', icon: '&#128293;', name: 'Stoke the Flame', blurb: 'Keep Fireboy&rsquo;s flame in the steady zone for ' + FLAME_CLEAR + 's.',
          status: 'Best ' + (s.flame || 0) + 's' + (c.flame ? ' ✓' : ' / ' + FLAME_CLEAR + 's'), play: () => gameFlame(overlay, back) }
      ];

      const arcadeWrap = document.createElement('div');
      arcadeWrap.className = 'tnc arcade';
      arcadeWrap.innerHTML =
        '<div class="tnc-panel arcade-panel" role="dialog" aria-label="The Volcano Arcade">' +
          '<div class="arcade-head">' +
            '<div><h4>The Volcano Arcade</h4>' +
              '<p class="arcade-sub">' + (grand
                ? 'You are the <b>Keeper of the Flame</b>. Every game cleared. Fireboy is whole.'
                : 'Clear all five games and win Fireboy, whole, as your trophy.') + '</p></div>' +
            '<button class="codex-close" type="button" aria-label="Leave the arcade">&times;</button>' +
          '</div>' +
          '<div class="arcade-grid">' +
            GAMES.map((g, i) =>
              '<button class="arcade-tile' + (c[g.key] ? ' cleared' : '') + '" type="button" data-g="' + i + '">' +
                '<span class="arcade-ico">' + g.icon + '</span>' +
                '<span class="arcade-name">' + g.name + '</span>' +
                '<span class="arcade-blurb">' + g.blurb + '</span>' +
                '<span class="arcade-status">' + g.status + '</span>' +
              '</button>').join('') +
            '<button class="arcade-tile arcade-trophy' + (grand ? ' won' : ' locked') + '" type="button" data-trophy="1">' +
              (grand
                ? '<img class="arcade-trophy-img" src="media/fireboy-cut.gif" alt="Fireboy trophy">'
                : '<span class="arcade-ico">&#128274;</span>') +
              '<span class="arcade-name">Fireboy Trophy</span>' +
              '<span class="arcade-blurb">' + (grand ? 'Whole again. Click to admire.' : 'Locked until all five games are cleared.') + '</span>' +
              '<span class="arcade-status">' + (grand ? 'Keeper of the Flame' : 'Locked') + '</span>' +
            '</button>' +
          '</div>' +
          '<div class="arcade-foot">' +
            '<button class="btn ghost arcade-codex" type="button"><span>Read the Codex</span></button>' +
            '<button class="btn solid arcade-leave" type="button"><span>Back to the website</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(arcadeWrap);

      if (grand) arcadeWrap.querySelector('.arcade-panel').classList.add('is-grand');
      arcadeWrap.querySelectorAll('.arcade-tile[data-g]').forEach(t =>
        t.addEventListener('click', () => GAMES[+t.getAttribute('data-g')].play()));
      arcadeWrap.querySelector('.arcade-trophy').addEventListener('click', function () { showTrophy(overlay, arcadeWrap, back); });
      arcadeWrap.querySelector('.arcade-codex').addEventListener('click', showCodex);
      const leave = function () { closeStage(overlay); };
      arcadeWrap.querySelector('.arcade-leave').addEventListener('click', leave);
      arcadeWrap.querySelector('.codex-close').addEventListener('click', leave);
    }

    // The trophy: the whole animated Fireboy, awarded for clearing the arcade.
    function showTrophy(overlay, prev, back) {
      if (prev) prev.remove();
      if (!overlay) overlay = openStage();
      const won = grandAligner();
      const wrap = document.createElement('div');
      wrap.className = 'tnc trophy';
      wrap.innerHTML =
        '<div class="tnc-panel trophy-panel' + (won ? ' won' : '') + '" role="dialog" aria-label="Fireboy trophy">' +
          '<h4>' + (won ? 'Fireboy &mdash; whole again' : 'The Fireboy Trophy') + '</h4>' +
          (won
            ? '<figure class="trophy-stage"><img src="media/fireboy-cut.gif" alt="Fireboy, whole"></figure>' +
              '<p class="tnc-sub">You cleared every game in the Volcano Arcade and relit all four moods. The flame is whole and Fireboy is yours. Title earned: <b>Keeper of the Flame</b>.</p>'
            : '<figure class="trophy-stage locked"><div class="trophy-lock">&#128274;</div></figure>' +
              '<p class="tnc-sub">Fireboy, whole and animated, is the arcade&rsquo;s highest reward. Clear all five games to win him. You are not there yet &mdash; but the fire is patient.</p>') +
          '<div class="calib-actions">' +
            '<button class="btn solid trophy-back" type="button"><span>&larr; Arcade</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);
      wrap.querySelector('.trophy-back').addEventListener('click', back || function () { closeStage(overlay); });
    }

    // Celebrate the moment all five games are first cleared.
    function maybeGrand() {
      if (checkGrand()) {
        toast('&#128293; <b>Keeper of the Flame.</b> Every game cleared &mdash; Fireboy is whole, and yours. Open the Fireboy Trophy in the arcade.');
      }
    }

    // --- STABILISER SEQUENCE: a Simon-style memory game with the four
    // mascot spirits. Repeat the growing pattern; reach level 5 to clear. ---
    function gameSimon(overlay, back) {
      const wrap = document.createElement('div');
      wrap.className = 'tnc simon';
      wrap.innerHTML =
        '<div class="tnc-panel simon-panel" role="dialog" aria-label="Stabiliser Sequence">' +
          '<h4>Stabiliser Sequence</h4>' +
          '<p class="tnc-sub">Watch the spirits light up, then repeat the order. It grows by one each round. Reach level ' + SIMON_CLEAR + ' to clear.</p>' +
          '<p class="simon-status">Level 1 &middot; watch closely&hellip;</p>' +
          '<div class="simon-pads">' +
            TARGETS.map(id => '<button class="simon-pad" type="button" data-pad="' + id + '" disabled>' +
              '<img src="mascots/' + id + '-cut.png" alt="' + NAMES[id] + '"></button>').join('') +
          '</div>' +
          '<div class="calib-actions">' +
            '<button class="btn solid simon-go" type="button"><span>Start</span></button>' +
            '<button class="btn ghost simon-back" type="button"><span>&larr; Arcade</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);

      const pads = wrap.querySelectorAll('.simon-pad');
      const status = wrap.querySelector('.simon-status');
      const go = wrap.querySelector('.simon-go');
      const padById = {};
      pads.forEach(p => padById[p.getAttribute('data-pad')] = p);

      let seq = [], expect = 0, accepting = false;
      const timers = [];
      const T = (fn, ms) => { const h = setTimeout(fn, ms); timers.push(h); return h; };
      function stop() { timers.forEach(clearTimeout); }

      function flash(id, ms) {
        const p = padById[id];
        p.classList.add('lit');
        T(() => p.classList.remove('lit'), ms);
      }
      function playback() {
        accepting = false;
        pads.forEach(p => p.disabled = true);
        status.textContent = 'Level ' + seq.length + ' · watch closely…';
        seq.forEach((id, i) => T(() => flash(id, 380), 300 + i * 620));
        T(() => {
          accepting = true; expect = 0;
          pads.forEach(p => p.disabled = false);
          status.textContent = 'Level ' + seq.length + ' · your turn';
        }, 300 + seq.length * 620 + 120);
      }
      function nextRound() {
        seq.push(TARGETS[Math.floor(Math.random() * TARGETS.length)]);
        playback();
      }
      function over(win) {
        accepting = false; stop();
        pads.forEach(p => p.disabled = true);
        const best = recordScore('simon', seq.length - (win ? 0 : 1)).simon;
        wrap.querySelector('.calib-actions').innerHTML = '';
        const again = document.createElement('button');
        again.className = 'btn solid'; again.type = 'button';
        again.innerHTML = '<span>Play again</span>';
        again.addEventListener('click', function () { stop(); wrap.remove(); gameSimon(overlay, back); });
        const bk = document.createElement('button');
        bk.className = 'btn ghost'; bk.type = 'button';
        bk.innerHTML = '<span>&larr; Arcade</span>';
        bk.addEventListener('click', function () { stop(); back(); });
        wrap.querySelector('.calib-actions').append(again, bk);
        if (win) {
          status.innerHTML = '<b>Cleared!</b> You held the pattern to level ' + SIMON_CLEAR + '. Best: ' + best + '.';
          maybeGrand();
        } else {
          status.innerHTML = '<b>Pattern broken</b> at level ' + seq.length + '. Best: ' + best + '.';
        }
      }

      pads.forEach(p => p.addEventListener('click', function () {
        if (!accepting) return;
        const id = p.getAttribute('data-pad');
        flash(id, 200);
        if (id === seq[expect]) {
          expect++;
          if (expect === seq.length) {
            accepting = false;
            if (seq.length >= SIMON_CLEAR) { over(true); return; }
            status.textContent = 'Good. Next…';
            T(nextRound, 700);
          }
        } else {
          over(false);
        }
      }));

      go.addEventListener('click', function () {
        go.disabled = true;
        go.parentElement.querySelector('.simon-back').remove();
        nextRound();
      });
      wrap.querySelector('.simon-back').addEventListener('click', function () { stop(); back(); });
    }

    // --- WONK PATROL: whack-a-mole. Crooked frames pop across a grid;
    // click to straighten before they drift away. 30s, score to clear. ---
    function gameWhack(overlay, back) {
      const COLS = 3, ROWS = 3, CELLS = COLS * ROWS, DUR = 30;
      const wrap = document.createElement('div');
      wrap.className = 'tnc whack';
      wrap.innerHTML =
        '<div class="tnc-panel whack-panel" role="dialog" aria-label="Wonk Patrol">' +
          '<h4>Wonk Patrol</h4>' +
          '<p class="tnc-sub">Crooked frames keep appearing. Click each to straighten it before it drifts off. ' + DUR + ' seconds. Score ' + WHACK_CLEAR + ' to clear.</p>' +
          '<div class="whack-hud"><span class="whack-score">Straightened 0</span><span class="whack-time">' + DUR + 's</span></div>' +
          '<div class="whack-grid">' +
            Array.from({ length: CELLS }, (_, i) => '<button class="whack-cell" type="button" data-c="' + i + '"></button>').join('') +
          '</div>' +
          '<div class="calib-actions">' +
            '<button class="btn solid whack-go" type="button"><span>Start patrol</span></button>' +
            '<button class="btn ghost whack-back" type="button"><span>&larr; Arcade</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);

      const cells = wrap.querySelectorAll('.whack-cell');
      const scoreEl = wrap.querySelector('.whack-score');
      const timeEl = wrap.querySelector('.whack-time');
      const go = wrap.querySelector('.whack-go');
      const MASC = TARGETS.slice();
      let score = 0, left = DUR, spawnT = 0, tickT = 0, active = null, running = false;

      function clearTimers() { clearTimeout(spawnT); clearInterval(tickT); }
      function tilt() { return (Math.random() < 0.5 ? -1 : 1) * (8 + Math.random() * 8); }

      function spawn() {
        if (!running) return;
        if (active) { active.el.classList.remove('up'); active.el.innerHTML = ''; }
        const i = Math.floor(Math.random() * cells.length);
        const el = cells[i];
        const id = MASC[Math.floor(Math.random() * MASC.length)];
        el.innerHTML = '<img src="mascots/' + id + '-cut.png" alt="" style="transform:rotate(' + tilt().toFixed(1) + 'deg)">';
        el.classList.add('up');
        active = { el: el, i: i };
        const life = 780 - Math.min(score, 15) * 28;   // speeds up as you score
        spawnT = setTimeout(function () {
          if (active && active.i === i) { el.classList.remove('up'); el.innerHTML = ''; active = null; }
          spawn();
        }, Math.max(360, life));
      }
      function end() {
        running = false; clearTimers();
        cells.forEach(c => { c.classList.remove('up'); c.innerHTML = ''; c.disabled = true; });
        const best = recordScore('whack', score).whack;
        const cleared = score >= WHACK_CLEAR;
        wrap.querySelector('.tnc-sub').innerHTML = cleared
          ? '<b>Patrol cleared!</b> ' + score + ' frames set true. Best: ' + best + '.'
          : 'Time. ' + score + ' frames straightened &mdash; need ' + WHACK_CLEAR + '. Best: ' + best + '.';
        wrap.querySelector('.calib-actions').innerHTML = '';
        const again = document.createElement('button');
        again.className = 'btn solid'; again.type = 'button';
        again.innerHTML = '<span>Patrol again</span>';
        again.addEventListener('click', function () { clearTimers(); wrap.remove(); gameWhack(overlay, back); });
        const bk = document.createElement('button');
        bk.className = 'btn ghost'; bk.type = 'button';
        bk.innerHTML = '<span>&larr; Arcade</span>';
        bk.addEventListener('click', function () { clearTimers(); back(); });
        wrap.querySelector('.calib-actions').append(again, bk);
        if (cleared) maybeGrand();
      }

      cells.forEach(c => c.addEventListener('click', function () {
        if (!running || !active || active.el !== c) return;
        score++;
        scoreEl.textContent = 'Straightened ' + score;
        c.classList.add('hit');
        setTimeout(() => c.classList.remove('hit'), 200);
        c.classList.remove('up'); c.innerHTML = '';
        active = null;
        clearTimeout(spawnT);
        spawn();
      }));

      go.addEventListener('click', function () {
        go.disabled = true;
        wrap.querySelector('.whack-back').remove();
        running = true;
        tickT = setInterval(function () {
          left--; timeEl.textContent = left + 's';
          if (left <= 0) end();
        }, 1000);
        spawn();
      });
      wrap.querySelector('.whack-back').addEventListener('click', function () { clearTimers(); back(); });
    }

    // --- STOKE THE FLAME: keep Fireboy's flame in the steady zone.
    // It cools on its own and flares at random; tap Stoke to add heat.
    // Too cold (0) or too hot (100) and the flame breaks. Survive to clear. ---
    function gameFlame(overlay, back) {
      const wrap = document.createElement('div');
      wrap.className = 'tnc flame';
      wrap.innerHTML =
        '<div class="tnc-panel flame-panel" role="dialog" aria-label="Stoke the Flame">' +
          '<h4>Stoke the Flame</h4>' +
          '<p class="tnc-sub">Fireboy&rsquo;s flame cools on its own and flares without warning. Tap <b>Stoke</b> to feed it. Keep it in the steady band &mdash; let it die or overheat and the run ends. Last ' + FLAME_CLEAR + 's to clear.</p>' +
          '<div class="flame-hud"><span class="flame-time">0.0s</span><span class="flame-state">Steady</span></div>' +
          '<div class="flame-gauge">' +
            '<div class="flame-zone"></div>' +
            '<div class="flame-fill"></div>' +
            '<div class="flame-marker"></div>' +
          '</div>' +
          '<div class="calib-actions">' +
            '<button class="btn solid flame-stoke" type="button"><span>&#128293; Stoke</span></button>' +
            '<button class="btn ghost flame-back" type="button"><span>&larr; Arcade</span></button>' +
          '</div>' +
        '</div>';
      overlay.appendChild(wrap);

      const fill = wrap.querySelector('.flame-fill');
      const marker = wrap.querySelector('.flame-marker');
      const stoke = wrap.querySelector('.flame-stoke');
      const timeEl = wrap.querySelector('.flame-time');
      const stateEl = wrap.querySelector('.flame-state');
      const LOW = 38, HIGH = 78;              // steady band
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      let heat = 58, cool = 12, elapsed = 0, running = false, raf = 0, flareT = 0, last = 0;

      // paint the steady zone once
      wrap.querySelector('.flame-zone').style.cssText =
        'bottom:' + LOW + '%;height:' + (HIGH - LOW) + '%;';

      function paint() {
        fill.style.height = heat + '%';
        marker.style.bottom = heat + '%';
        const steady = heat >= LOW && heat <= HIGH;
        wrap.querySelector('.flame-gauge').classList.toggle('danger', !steady);
        stateEl.textContent = heat < LOW ? 'Cooling…' : heat > HIGH ? 'Overheating!' : 'Steady';
      }
      function stop(win) {
        running = false; cancelAnimationFrame(raf); clearTimeout(flareT);
        stoke.disabled = true;
        const secs = Math.floor(elapsed);
        const best = recordScore('flame', secs).flame;
        wrap.querySelector('.tnc-sub').innerHTML = win
          ? '<b>Flame held!</b> ' + FLAME_CLEAR + 's of steady fire. Best: ' + best + 's.'
          : (heat <= 0 ? '<b>The flame went out.</b> ' : '<b>The flame overheated.</b> ') + 'Lasted ' + secs + 's. Best: ' + best + 's.';
        wrap.querySelector('.calib-actions').innerHTML = '';
        const again = document.createElement('button');
        again.className = 'btn solid'; again.type = 'button';
        again.innerHTML = '<span>Again</span>';
        again.addEventListener('click', function () { cancelAnimationFrame(raf); clearTimeout(flareT); wrap.remove(); gameFlame(overlay, back); });
        const bk = document.createElement('button');
        bk.className = 'btn ghost'; bk.type = 'button';
        bk.innerHTML = '<span>&larr; Arcade</span>';
        bk.addEventListener('click', function () { cancelAnimationFrame(raf); clearTimeout(flareT); back(); });
        wrap.querySelector('.calib-actions').append(again, bk);
        if (win) maybeGrand();
      }
      function flare() {
        if (!running) return;
        // random shove up or down, harder over time
        heat += (Math.random() < 0.5 ? -1 : 1) * (8 + Math.random() * 10 + elapsed * 0.4);
        flareT = setTimeout(flare, 900 + Math.random() * 1300);
      }
      function tick(now) {
        if (!running) return;
        const dt = Math.min((now - last) / 1000, 0.05); last = now;
        elapsed += dt;
        heat -= (cool + elapsed * 0.5) * dt;   // cooling accelerates
        heat = Math.max(-1, Math.min(101, heat));
        timeEl.textContent = elapsed.toFixed(1) + 's';
        paint();
        if (heat <= 0 || heat >= 100) return stop(false);
        if (elapsed >= FLAME_CLEAR) { heat = Math.min(heat, 100); return stop(true); }
        raf = requestAnimationFrame(tick);
      }

      function addHeat() { if (running) { heat = Math.min(100, heat + 9); paint(); } }

      function start() {
        wrap.querySelector('.flame-back').remove();
        running = true; last = performance.now(); elapsed = 0; heat = 58;
        paint();
        raf = requestAnimationFrame(tick);
        if (!reduced) flareT = setTimeout(flare, 1100);
      }
      // First press of Stoke starts the run; every press after feeds the flame.
      let started = false;
      stoke.addEventListener('click', function () {
        if (!started) { started = true; start(); }
        else addHeat();
      });
      paint();
      wrap.querySelector('.flame-back').addEventListener('click', function () { cancelAnimationFrame(raf); clearTimeout(flareT); back(); });
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
          '<img class="fireboy-rise" src="media/fireboy-cut.gif" alt="Fireboy rising from the crater">' +
          '<h3>Fireboy rises from the crater!</h3>' +
          '<p>The four moods clicked back together and Fireboy climbed out of the volcano, holding exactly one cookie. To claim it, you must first accept the cookie terms and conditions, all of them.</p>' +
          '<button class="btn solid" type="button"><span>Claim the cookie</span></button>';
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

// === WONK TOGGLE ===
// Tilted "sticker" elements straighten up on click and go wonky
// again on the next. Hunt stickers and the footer mascot are
// exempt - their clicks belong to the sticker-hunt minigame.
document.addEventListener('DOMContentLoaded', function () {
  document
    .querySelectorAll('.block-media img, .team-card, .gallery img, .sponsor-logos li')
    .forEach(function (el) {
      el.addEventListener('click', function () {
        el.classList.toggle('straightened');
      });
    });
});
