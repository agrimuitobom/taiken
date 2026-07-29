/* ==========================================================================
   files.js ─ 配布ファイル一覧の描画
   --------------------------------------------------------------------------
   ファイル一覧の取得順:
     1. /api/files          … server.py で配信している場合（files/ を自動で読む）
     2. files/manifest.json … 静的配信の場合（tools/make_manifest.py で生成）
   どちらも取れないときは、その場で案内を出します。
   ========================================================================== */
(function () {
  'use strict';

  var root = document.querySelector('[data-filelist]');
  if (!root) return;

  var elList   = root.querySelector('[data-fl-list]');
  var elChips  = root.querySelector('[data-fl-chips]');
  var elSearch = root.querySelector('[data-fl-search]');
  var elCount  = root.querySelector('[data-fl-count]');
  var elZip    = root.querySelector('[data-fl-zip]');
  var limit    = parseInt(root.getAttribute('data-limit') || '0', 10);

  var ICON_DOWN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v12"/><path d="M6.5 11.5 12 17l5.5-5.5"/><path d="M4.5 20h15"/></svg>';

  var state = { items: [], category: '*', query: '', source: null };

  /* --- 表示用の小道具 -------------------------------------------------- */
  function formatSize(bytes) {
    if (typeof bytes !== 'number' || isNaN(bytes) || bytes < 0) return '';
    if (bytes < 1024) return bytes + ' B';
    var units = ['KB', 'MB', 'GB'];
    var v = bytes / 1024;
    var i = 0;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
    return (v >= 100 ? Math.round(v) : v.toFixed(1)) + ' ' + units[i];
  }

  function formatDate(value) {
    if (!value) return '';
    var d = new Date(value);
    if (isNaN(d.getTime())) return '';
    var p = function (n) { return n < 10 ? '0' + n : String(n); };
    return d.getFullYear() + '.' + p(d.getMonth() + 1) + '.' + p(d.getDate());
  }

  function extOf(name) {
    var m = /\.([A-Za-z0-9]{1,6})$/.exec(name || '');
    return m ? m[1].toLowerCase() : 'file';
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function encodePath(path) {
    return String(path).split('/').map(encodeURIComponent).join('/');
  }

  /* --- 描画 ------------------------------------------------------------ */
  function fileRow(item) {
    var name = item.title || item.name;
    var meta = [];
    if (item.size) meta.push(formatSize(item.size));
    if (item.mtime) meta.push(formatDate(item.mtime));
    if (item.note) meta.push('<span class="jp">' + escapeHtml(item.note) + '</span>');

    return '<a class="file" href="' + escapeHtml(encodePath(item.path)) + '" download>' +
      '<span class="file__ext" aria-hidden="true">' + escapeHtml(extOf(item.name)) + '</span>' +
      '<span class="file__name">' + escapeHtml(name) + '</span>' +
      '<span class="file__meta">' + meta.join('<span aria-hidden="true">·</span>') + '</span>' +
      '<span class="file__go" aria-hidden="true">' + ICON_DOWN + '</span>' +
      '</a>';
  }

  function render() {
    var q = state.query.trim().toLowerCase();
    var items = state.items.filter(function (it) {
      if (state.category !== '*' && (it.category || 'その他') !== state.category) return false;
      if (!q) return true;
      return ((it.title || '') + ' ' + it.name + ' ' + (it.category || '')).toLowerCase().indexOf(q) >= 0;
    });

    if (elCount) {
      elCount.textContent = items.length ? items.length + ' 件' : '';
    }

    if (!items.length) {
      elList.innerHTML = '<p class="state">該当するファイルがありません。<br>キーワードを変えてお試しください。</p>';
      return;
    }

    var shown = limit > 0 ? items.slice(0, limit) : items;
    var html = '';

    if (state.category === '*' && !q) {
      // カテゴリ（files/ 直下のフォルダ）ごとにまとめて出す
      var order = [];
      var groups = {};
      shown.forEach(function (it) {
        var key = it.category || 'その他';
        if (!groups[key]) { groups[key] = []; order.push(key); }
        groups[key].push(it);
      });
      order.forEach(function (key) {
        if (order.length > 1) {
          html += '<p class="filelist__group-ttl">' + escapeHtml(key) + '</p>';
        }
        html += groups[key].map(fileRow).join('');
      });
    } else {
      html = shown.map(fileRow).join('');
    }

    elList.innerHTML = html;
  }

  function renderChips() {
    if (!elChips) return;
    var cats = [];
    state.items.forEach(function (it) {
      var c = it.category || 'その他';
      if (cats.indexOf(c) < 0) cats.push(c);
    });
    if (cats.length < 2) { elChips.innerHTML = ''; return; }

    elChips.innerHTML = ['*'].concat(cats).map(function (c) {
      var label = c === '*' ? 'すべて' : c;
      return '<button type="button" class="chip" data-cat="' + escapeHtml(c) + '" aria-pressed="' +
        (state.category === c) + '">' + escapeHtml(label) + '</button>';
    }).join('');

    elChips.querySelectorAll('.chip').forEach(function (btn) {
      btn.addEventListener('click', function () {
        state.category = btn.getAttribute('data-cat');
        elChips.querySelectorAll('.chip').forEach(function (b) {
          b.setAttribute('aria-pressed', String(b === btn));
        });
        render();
      });
    });
  }

  function showGuide() {
    var isFile = window.location.protocol === 'file:';
    elList.innerHTML = '<div class="state">' +
      '<b>配布ファイルの一覧を取得できませんでした</b>' +
      (isFile
        ? 'HTMLファイルを直接開いている（file://）ため、一覧を読み込めません。<br>' +
          '<code>python3 server.py</code> を実行し、表示されたアドレスから開いてください。'
        : 'このページは <code>server.py</code> を通さずに配信されています。<br>' +
          '<code>files/</code> にファイルを置いたあと、<code>python3 tools/make_manifest.py</code> を実行して<br>' +
          '<code>files/manifest.json</code> を更新してください。' +
          '（GitHubへのpush時は自動更新されます）') +
      '</div>';
    if (elCount) elCount.textContent = '';
  }

  /* --- 取得 ------------------------------------------------------------ */
  function normalize(data) {
    var items = (data && data.items) || [];
    return items.filter(function (it) { return it && it.name && it.path; });
  }

  function load() {
    var sources = ['api/files', 'files/manifest.json'];

    var tryNext = function (i) {
      if (i >= sources.length) { showGuide(); return; }
      fetch(sources[i], { cache: 'no-store' })
        .then(function (res) {
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return res.json();
        })
        .then(function (data) {
          var items = normalize(data);
          if (!items.length) {
            elList.innerHTML = '<div class="state"><b>配布ファイルは準備中です</b>' +
              '当日までにこのページへ資料が並びます。</div>';
            if (elCount) elCount.textContent = '';
            return;
          }
          state.items = items;
          state.source = sources[i];
          // server.py 配信のときだけ「まとめてダウンロード」を出す
          if (elZip && data.zip) {
            elZip.hidden = false;
            elZip.setAttribute('href', data.zip);
          }
          renderChips();
          render();
        })
        .catch(function () { tryNext(i + 1); });
    };

    tryNext(0);
  }

  if (elSearch) {
    var timer = null;
    elSearch.addEventListener('input', function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        state.query = elSearch.value;
        render();
      }, 120);
    });
  }

  load();
})();
