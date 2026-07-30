/* ==========================================================================
   zip.js ─ ブラウザの中でZIPファイルを組み立てる（外部ライブラリなし）
   --------------------------------------------------------------------------
   server.py を通さない配信（GitHub Pages など）でも
   「まとめてダウンロード」を使えるようにするためのもの。

   ・無圧縮（store方式）で束ねるだけなので、処理が軽く実装も小さい
   ・日本語ファイル名に対応（UTF-8フラグを立てています）
   ・使い方: TaikenZip.build([{ name: "01_資料/a.pdf", data: Uint8Array, date: Date }])
             → Blob を返します
   ========================================================================== */
window.TaikenZip = (function () {
  'use strict';

  /* --- CRC32 ----------------------------------------------------------- */
  var TABLE = (function () {
    var t = new Uint32Array(256);
    for (var i = 0; i < 256; i++) {
      var c = i;
      for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[i] = c >>> 0;
    }
    return t;
  })();

  function crc32(bytes) {
    var c = 0xFFFFFFFF;
    for (var i = 0; i < bytes.length; i++) {
      c = TABLE[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
    }
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  /* --- 書き込みの小道具 ------------------------------------------------ */
  function Writer(size) {
    this.buf = new Uint8Array(size);
    this.view = new DataView(this.buf.buffer);
    this.pos = 0;
  }
  Writer.prototype.u16 = function (v) { this.view.setUint16(this.pos, v, true); this.pos += 2; };
  Writer.prototype.u32 = function (v) { this.view.setUint32(this.pos, v >>> 0, true); this.pos += 4; };
  Writer.prototype.bytes = function (b) { this.buf.set(b, this.pos); this.pos += b.length; };

  /* --- MS-DOS形式の日付時刻 -------------------------------------------- */
  function dosTime(d) {
    if (!(d instanceof Date) || isNaN(d.getTime())) d = new Date();
    var year = d.getFullYear();
    if (year < 1980) return { time: 0, date: 33 };  // 1980-01-01
    return {
      time: (d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1),
      date: ((year - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()
    };
  }

  var encoder = new TextEncoder();

  /* --- 本体 ------------------------------------------------------------ */
  function build(entries) {
    var items = entries.map(function (e) {
      var name = encoder.encode(String(e.name).replace(/\\/g, '/').replace(/^\/+/, ''));
      return { name: name, data: e.data, crc: crc32(e.data), dt: dosTime(e.date) };
    });

    // 必要なサイズを先に確定させる（30/46/22 は各ヘッダーの固定長）
    var total = 0, cdSize = 0;
    items.forEach(function (it) {
      total += 30 + it.name.length + it.data.length;
      cdSize += 46 + it.name.length;
    });
    var w = new Writer(total + cdSize + 22);

    // ローカルファイルヘッダー＋データ
    items.forEach(function (it) {
      it.offset = w.pos;
      w.u32(0x04034B50);
      w.u16(20);              // 展開に必要なバージョン
      w.u16(0x0800);          // ファイル名はUTF-8
      w.u16(0);               // 無圧縮
      w.u16(it.dt.time);
      w.u16(it.dt.date);
      w.u32(it.crc);
      w.u32(it.data.length);  // 圧縮後サイズ（無圧縮なので同じ）
      w.u32(it.data.length);
      w.u16(it.name.length);
      w.u16(0);               // 拡張フィールドなし
      w.bytes(it.name);
      w.bytes(it.data);
    });

    // セントラルディレクトリ
    var cdStart = w.pos;
    items.forEach(function (it) {
      w.u32(0x02014B50);
      w.u16(20);              // 作成バージョン
      w.u16(20);
      w.u16(0x0800);
      w.u16(0);
      w.u16(it.dt.time);
      w.u16(it.dt.date);
      w.u32(it.crc);
      w.u32(it.data.length);
      w.u32(it.data.length);
      w.u16(it.name.length);
      w.u16(0);               // 拡張フィールド
      w.u16(0);               // コメント
      w.u16(0);               // 開始ディスク番号
      w.u16(0);               // 内部属性
      w.u32(0);               // 外部属性
      w.u32(it.offset);
      w.bytes(it.name);
    });

    // 終端レコード（サイズは EOCD を書く前の位置で確定させる）
    var cdEnd = w.pos;
    w.u32(0x06054B50);
    w.u16(0);
    w.u16(0);
    w.u16(items.length);
    w.u16(items.length);
    w.u32(cdEnd - cdStart);
    w.u32(cdStart);
    w.u16(0);

    return new Blob([w.buf.subarray(0, w.pos)], { type: 'application/zip' });
  }

  return { build: build, crc32: crc32 };
})();
