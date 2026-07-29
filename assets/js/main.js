/* ==========================================================================
   main.js ─ ヘッダー・メニュー・スクロール演出
   外部ライブラリなし。ラズパイのオフライン配信でもそのまま動きます。
   ========================================================================== */
(function () {
  'use strict';

  /* --- ヘッダーの背景切り替え（トップページのみ） --------------------- */
  var header = document.querySelector('.header');
  if (header && !header.classList.contains('header--static')) {
    var onScroll = function () {
      var trigger = Math.min(window.innerHeight * 0.6, 480);
      header.classList.toggle('is-solid', window.scrollY > trigger);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* --- ドロワーメニュー ----------------------------------------------- */
  var burger = document.querySelector('.burger');
  var drawer = document.getElementById('drawer');

  if (burger && drawer) {
    drawer.querySelectorAll('.drawer__list a').forEach(function (a, i) {
      a.style.setProperty('--i', String(i));
    });

    var setDrawer = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      drawer.classList.toggle('is-open', open);
      drawer.setAttribute('aria-hidden', String(!open));
      document.body.classList.toggle('is-locked', open);
    };

    setDrawer(false);

    burger.addEventListener('click', function () {
      setDrawer(burger.getAttribute('aria-expanded') !== 'true');
    });

    drawer.addEventListener('click', function (e) {
      if (e.target.closest('a')) setDrawer(false);
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) {
        setDrawer(false);
        burger.focus();
      }
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 860) setDrawer(false);
    });
  }

  /* --- スクロールで要素を出す ----------------------------------------- */
  var reveals = document.querySelectorAll('[data-reveal]');
  var showAll = function () {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  };

  if (!('IntersectionObserver' in window)) {
    showAll();
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

    try {
      reveals.forEach(function (el) {
        // 同じ親の中で並んでいる要素は少しずつ遅らせる
        var group = el.getAttribute('data-reveal-group');
        if (group !== null && group !== '') {
          el.style.setProperty('--d', (parseInt(group, 10) || 0) * 90 + 'ms');
        }
        io.observe(el);
      });
    } catch (e) {
      // 万一の失敗でも本文が隠れたままにならないようにする
      showAll();
    }
  }

  /* --- 現在の年をフッターに ------------------------------------------- */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* --- いま見ているURLを表示（ラズパイのアドレス案内用） -------------- */
  document.querySelectorAll('[data-host]').forEach(function (el) {
    el.textContent = window.location.host || 'localhost';
  });
})();
