/*
 * DevTool+ - a local-only developer utility toolkit embedded in ACEsi's Code
 * Editor. Everything runs in the browser: no network calls, no external
 * services. Built with Lit and bundled to /static/devtool-plus.js so it works
 * fully offline.
 */
import { LitElement, html, css } from 'lit';

/* ---------------------------------------------------------------- helpers */
const enc = new TextEncoder();
const dec = new TextDecoder();

function bytesToB64(bytes) {
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}
function b64ToBytes(s) {
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}
const utf8ToB64 = (s) => bytesToB64(enc.encode(s));
const b64ToUtf8 = (s) => dec.decode(b64ToBytes(s));

function bytesToHex(bytes, sep = '') {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join(sep);
}
function hexToBytes(s) {
  const clean = String(s || '').replace(/0x/gi, '').replace(/[^0-9a-f]/gi, '');
  if (clean.length % 2) throw new Error('Hex string must have an even number of digits');
  const out = new Uint8Array(clean.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  return out;
}
const rot13 = (s) => String(s).replace(/[a-z]/gi, (c) => {
  const base = c <= 'Z' ? 65 : 97;
  return String.fromCharCode(((c.charCodeAt(0) - base + 13) % 26) + base);
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}
function unescapeHtml(s) {
  const el = document.createElement('textarea');
  el.innerHTML = String(s);
  return el.value;
}

async function digestHex(algo, s) {
  const buf = await crypto.subtle.digest(algo, enc.encode(s));
  return bytesToHex(new Uint8Array(buf));
}
async function hmacHex(s, key) {
  const k = await crypto.subtle.importKey('raw', enc.encode(key), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', k, enc.encode(s));
  return bytesToHex(new Uint8Array(sig));
}

/* Compact, dependency-free MD5 (RFC 1321). */
const MD5_S = [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22,
  5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20,
  4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23,
  6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21];
const MD5_K = Array.from({ length: 64 }, (_, i) => Math.floor(Math.abs(Math.sin(i + 1)) * 4294967296));
function md5(msg) {
  const bytes = enc.encode(msg);
  const bitLen = bytes.length * 8;
  const paddedLen = Math.ceil((bytes.length + 1 + 8) / 64) * 64;
  const buf = new Uint8Array(paddedLen);
  buf.set(bytes);
  buf[bytes.length] = 0x80;
  const dv = new DataView(buf.buffer);
  dv.setUint32(paddedLen - 8, bitLen >>> 0, true);
  dv.setUint32(paddedLen - 4, Math.floor(bitLen / 4294967296), true);
  let a0 = 0x67452301, b0 = 0xefcdab89, c0 = 0x98badcfe, d0 = 0x10325476;
  for (let off = 0; off < paddedLen; off += 64) {
    const M = [];
    for (let i = 0; i < 16; i++) M.push(dv.getUint32(off + i * 4, true));
    let A = a0, B = b0, C = c0, D = d0;
    for (let i = 0; i < 64; i++) {
      let F, g;
      if (i < 16) { F = (B & C) | (~B & D); g = i; }
      else if (i < 32) { F = (D & B) | (~D & C); g = (5 * i + 1) % 16; }
      else if (i < 48) { F = B ^ C ^ D; g = (3 * i + 5) % 16; }
      else { F = C ^ (B | ~D); g = (7 * i) % 16; }
      F = (F + A + MD5_K[i] + M[g]) >>> 0;
      A = D; D = C; C = B;
      B = (B + (((F << MD5_S[i]) | (F >>> (32 - MD5_S[i]))) >>> 0)) >>> 0;
    }
    a0 = (a0 + A) >>> 0; b0 = (b0 + B) >>> 0; c0 = (c0 + C) >>> 0; d0 = (d0 + D) >>> 0;
  }
  const hx = (w) => [w & 255, (w >>> 8) & 255, (w >>> 16) & 255, (w >>> 24) & 255]
    .map((b) => b.toString(16).padStart(2, '0')).join('');
  return hx(a0) + hx(b0) + hx(c0) + hx(d0);
}

/* ------------------------------------------------------------- tool data */
const fld = (key, label, placeholder = '', type = 'textarea', extra = {}) =>
  ({ key, label, placeholder, type, ...extra });

export const TOOLS = [
  /* --- Data ------------------------------------------------------------- */
  { id: 'json-pretty', name: 'JSON Formatter', category: 'Data', tags: ['json', 'format', 'beautify'],
    fields: [fld('in', 'JSON', '{"key": "value"}')],
    run: (v) => JSON.stringify(JSON.parse(v.in), null, 2) },
  { id: 'json-minify', name: 'JSON Minifier', category: 'Data', tags: ['json', 'minify', 'compact'],
    fields: [fld('in', 'JSON', '{"key": "value"}')],
    run: (v) => JSON.stringify(JSON.parse(v.in)) },
  { id: 'json-to-query', name: 'JSON → Query String', category: 'Data', tags: ['json', 'query', 'url'],
    fields: [fld('in', 'JSON', '{"a": 1, "b": "two"}')],
    run: (v) => { const o = JSON.parse(v.in); return new URLSearchParams(Object.entries(o).map(([k, x]) => [k, String(x)])).toString(); } },
  { id: 'query-to-json', name: 'Query String → JSON', category: 'Data', tags: ['query', 'url', 'json'],
    fields: [fld('in', 'Query string', 'a=1&b=two')],
    run: (v) => JSON.stringify(Object.fromEntries(new URLSearchParams(v.in.replace(/^\?/, ''))), null, 2) },
  { id: 'csv-to-json', name: 'CSV → JSON', category: 'Data', tags: ['csv', 'json', 'table'],
    fields: [fld('in', 'CSV', 'name,age\nAlice,30\nBob,25')],
    run: (v) => {
      const lines = String(v.in).split(/\r?\n/).filter(Boolean);
      if (!lines.length) return '';
      const split = (line) => {
        const out = []; let cur = '', q = false;
        for (let i = 0; i < line.length; i++) {
          const c = line[i];
          if (c === '"') { if (q && line[i + 1] === '"') { cur += '"'; i++; } else q = !q; }
          else if (c === ',' && !q) { out.push(cur); cur = ''; }
          else cur += c;
        }
        out.push(cur); return out;
      };
      const head = split(lines[0]);
      const rows = lines.slice(1).map((l) => {
        const cells = split(l); const o = {};
        head.forEach((h, i) => { o[h] = cells[i] ?? ''; });
        return o;
      });
      return JSON.stringify(rows, null, 2);
    } },
  { id: 'json-to-csv', name: 'JSON → CSV', category: 'Data', tags: ['json', 'csv', 'table'],
    fields: [fld('in', 'JSON array', '[{"name":"Alice","age":30}]')],
    run: (v) => {
      const rows = JSON.parse(v.in);
      if (!Array.isArray(rows) || !rows.length) return '';
      const head = Object.keys(rows[0]);
      const esc = (x) => /[",\n]/.test(String(x)) ? '"' + String(x).replace(/"/g, '""') + '"' : String(x);
      return [head.join(','), ...rows.map((r) => head.map((h) => esc(r[h] ?? '')).join(','))].join('\n');
    } },
  { id: 'sort-lines', name: 'Sort Lines', category: 'Data', tags: ['sort', 'lines', 'order'],
    fields: [fld('in', 'Lines', 'banana\napple\ncherry'), fld('order', 'Order', '', 'select',
      { options: [{ value: 'asc', label: 'A → Z' }, { value: 'desc', label: 'Z → A' }] })],
    run: (v) => { const l = String(v.in).split(/\r?\n/).sort((a, b) => a.localeCompare(b)); return (v.order === 'desc' ? l.reverse() : l).join('\n'); } },
  { id: 'unique-lines', name: 'Remove Duplicate Lines', category: 'Data', tags: ['unique', 'dedupe', 'lines'],
    fields: [fld('in', 'Lines', 'a\nb\na\nc')],
    run: (v) => Array.from(new Set(String(v.in).split(/\r?\n/))).join('\n') },
  { id: 'text-stats', name: 'Text Statistics', category: 'Data', tags: ['count', 'words', 'characters', 'stats'],
    fields: [fld('in', 'Text', 'Hello world')],
    run: (v) => {
      const s = String(v.in);
      const chars = s.length, noSpaces = s.replace(/\s/g, '').length;
      const words = (s.trim().match(/\S+/g) || []).length;
      const lines = s ? s.split(/\r?\n/).length : 0;
      return `Characters: ${chars}\nCharacters (no spaces): ${noSpaces}\nWords: ${words}\nLines: ${lines}\nUTF-8 bytes: ${enc.encode(s).length}`;
    } },
  { id: 'timestamp', name: 'Unix Timestamp ⇄ Date', category: 'Data', tags: ['time', 'unix', 'date', 'epoch'],
    fields: [fld('in', 'Value', '1700000000'), fld('mode', 'Direction', '', 'select',
      { options: [{ value: 'to-date', label: 'Timestamp → Date' }, { value: 'to-ts', label: 'Date → Timestamp' }] })],
    run: (v) => {
      if (v.mode === 'to-ts') { const t = Date.parse(v.in); return isNaN(t) ? 'Invalid date' : String(Math.floor(t / 1000)); }
      const n = Number(v.in); return isNaN(n) ? 'Invalid timestamp' : new Date(n * 1000).toISOString();
    } },
  { id: 'number-base', name: 'Number Base Converter', category: 'Data', tags: ['binary', 'hex', 'octal', 'radix'],
    fields: [fld('in', 'Number', '255'), fld('from', 'From base', '', 'select',
      { options: [10, 2, 16, 8].map((b) => ({ value: String(b), label: `Base ${b}` })) }), fld('to', 'To base', '', 'select',
      { options: [2, 8, 10, 16].map((b) => ({ value: String(b), label: `Base ${b}` })) })],
    run: (v) => {
      const n = parseInt(String(v.in).trim(), parseInt(v.from, 10));
      if (isNaN(n)) return 'Invalid number for the selected base';
      return n.toString(parseInt(v.to, 10));
    } },

  /* --- Encoding ---------------------------------------------------------- */
  { id: 'b64-encode', name: 'Base64 Encode', category: 'Encoding', tags: ['base64', 'encode', 'utf8'],
    fields: [fld('in', 'Text', 'Hello world')], run: (v) => utf8ToB64(v.in) },
  { id: 'b64-decode', name: 'Base64 Decode', category: 'Encoding', tags: ['base64', 'decode', 'utf8'],
    fields: [fld('in', 'Base64', 'SGVsbG8gd29ybGQ=')], run: (v) => b64ToUtf8(String(v.in).trim()) },
  { id: 'b64url-encode', name: 'Base64URL Encode', category: 'Encoding', tags: ['base64', 'url', 'encode'],
    fields: [fld('in', 'Text', 'Hello world')],
    run: (v) => utf8ToB64(v.in).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '') },
  { id: 'b64url-decode', name: 'Base64URL Decode', category: 'Encoding', tags: ['base64', 'url', 'decode'],
    fields: [fld('in', 'Base64URL', 'SGVsbG8gd29ybGQ')],
    run: (v) => { let s = String(v.in).trim().replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '='; return b64ToUtf8(s); } },
  { id: 'url-encode', name: 'URL Encode', category: 'Encoding', tags: ['url', 'percent', 'encode', 'uri'],
    fields: [fld('in', 'Text', 'a b&c=d')], run: (v) => encodeURIComponent(v.in) },
  { id: 'url-decode', name: 'URL Decode', category: 'Encoding', tags: ['url', 'percent', 'decode', 'uri'],
    fields: [fld('in', 'Encoded', 'a%20b%26c%3Dd')], run: (v) => decodeURIComponent(v.in) },
  { id: 'html-escape', name: 'HTML Escape', category: 'Encoding', tags: ['html', 'entities', 'escape'],
    fields: [fld('in', 'Text', '<div class="x">')], run: (v) => escapeHtml(v.in) },
  { id: 'html-unescape', name: 'HTML Unescape', category: 'Encoding', tags: ['html', 'entities', 'unescape'],
    fields: [fld('in', 'Entities', '&lt;div class=&quot;x&quot;&gt;')], run: (v) => unescapeHtml(v.in) },
  { id: 'text-to-hex', name: 'Text → Hex', category: 'Encoding', tags: ['hex', 'bytes', 'encode'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => bytesToHex(enc.encode(v.in), ' ') },
  { id: 'hex-to-text', name: 'Hex → Text', category: 'Encoding', tags: ['hex', 'bytes', 'decode'],
    fields: [fld('in', 'Hex', '48 65 6c 6c 6f')], run: (v) => dec.decode(hexToBytes(v.in)) },
  { id: 'text-to-binary', name: 'Text → Binary', category: 'Encoding', tags: ['binary', 'bits', 'encode'],
    fields: [fld('in', 'Text', 'Hi')],
    run: (v) => Array.from(enc.encode(v.in), (b) => b.toString(2).padStart(8, '0')).join(' ') },
  { id: 'binary-to-text', name: 'Binary → Text', category: 'Encoding', tags: ['binary', 'bits', 'decode'],
    fields: [fld('in', 'Binary', '01001000 01101001')],
    run: (v) => { const nums = String(v.in).split(/\s+/).filter(Boolean).map((b) => parseInt(b, 2)); return dec.decode(new Uint8Array(nums)); } },
  { id: 'rot13', name: 'ROT13', category: 'Encoding', tags: ['rot13', 'caesar', 'cipher'],
    fields: [fld('in', 'Text', 'Hello World')], run: (v) => rot13(v.in) },
  { id: 'jwt-decode', name: 'JWT Decode', category: 'Encoding', tags: ['jwt', 'token', 'json'],
    fields: [fld('in', 'JWT', 'header.payload.signature')],
    run: (v) => {
      const parts = String(v.in).trim().split('.');
      if (parts.length < 2) return 'Not a JWT (expected header.payload.signature)';
      const pretty = (p) => JSON.stringify(JSON.parse(b64ToUtf8(p.replace(/-/g, '+').replace(/_/g, '/'))), null, 2);
      return `HEADER\n${pretty(parts[0])}\n\nPAYLOAD\n${pretty(parts[1])}`;
    } },

  /* --- Cryptography ------------------------------------------------------ */
  { id: 'sha1', name: 'SHA-1', category: 'Cryptography', tags: ['hash', 'sha1'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => digestHex('SHA-1', v.in) },
  { id: 'sha256', name: 'SHA-256', category: 'Cryptography', tags: ['hash', 'sha256', 'secure'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => digestHex('SHA-256', v.in) },
  { id: 'sha384', name: 'SHA-384', category: 'Cryptography', tags: ['hash', 'sha384'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => digestHex('SHA-384', v.in) },
  { id: 'sha512', name: 'SHA-512', category: 'Cryptography', tags: ['hash', 'sha512'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => digestHex('SHA-512', v.in) },
  { id: 'md5', name: 'MD5', category: 'Cryptography', tags: ['hash', 'md5', 'legacy'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => md5(v.in) },
  { id: 'hmac-sha256', name: 'HMAC-SHA256', category: 'Cryptography', tags: ['hmac', 'hash', 'key', 'sign'],
    fields: [fld('msg', 'Message', 'Hello'), fld('key', 'Secret key', 'secret')],
    run: (v) => hmacHex(v.msg, v.key) },
  { id: 'xor-cipher', name: 'XOR Cipher', category: 'Cryptography', tags: ['xor', 'cipher', 'encrypt'],
    fields: [fld('msg', 'Message', 'Hello'), fld('key', 'Key', 'secret')],
    run: (v) => {
      const k = v.key || ' ';
      const codes = Array.from(v.msg, (c, i) => c.charCodeAt(0) ^ k.charCodeAt(i % k.length));
      return codes.map((n) => n.toString(16).padStart(4, '0')).join(' ');
    } },
  { id: 'basic-auth', name: 'Basic Auth Header', category: 'Cryptography', tags: ['basic', 'auth', 'header', 'base64'],
    fields: [fld('user', 'Username', 'admin'), fld('pass', 'Password', 'password')],
    run: (v) => 'Basic ' + utf8ToB64(`${v.user}:${v.pass}`) },
  { id: 'uuid', name: 'UUID v4 Generator', category: 'Cryptography', tags: ['uuid', 'guid', 'random', 'generate'],
    fields: [], action: true,
    run: () => { const b = crypto.getRandomValues(new Uint8Array(16)); b[6] = (b[6] & 0x0f) | 0x40; b[8] = (b[8] & 0x3f) | 0x80;
      const h = bytesToHex(b); return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`; } },

  /* --- Text -------------------------------------------------------------- */
  { id: 'uppercase', name: 'UPPERCASE', category: 'Text', tags: ['upper', 'case', 'text'],
    fields: [fld('in', 'Text', 'Hello world')], run: (v) => v.in.toUpperCase() },
  { id: 'lowercase', name: 'lowercase', category: 'Text', tags: ['lower', 'case', 'text'],
    fields: [fld('in', 'Text', 'HELLO WORLD')], run: (v) => v.in.toLowerCase() },
  { id: 'title-case', name: 'Title Case', category: 'Text', tags: ['title', 'case', 'text'],
    fields: [fld('in', 'Text', 'hello world')],
    run: (v) => v.in.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase()) },
  { id: 'reverse', name: 'Reverse Text', category: 'Text', tags: ['reverse', 'flip', 'text'],
    fields: [fld('in', 'Text', 'Hello')], run: (v) => Array.from(v.in).reverse().join('') },
  { id: 'trim-lines', name: 'Trim & Remove Empty Lines', category: 'Text', tags: ['trim', 'clean', 'lines', 'whitespace'],
    fields: [fld('in', 'Text', '  a  \n\n  b  ')],
    run: (v) => String(v.in).split(/\r?\n/).map((l) => l.trim()).filter(Boolean).join('\n') },
  { id: 'find-replace', name: 'Find & Replace', category: 'Text', tags: ['find', 'replace', 'search', 'text'],
    fields: [fld('in', 'Text', 'one fish two fish'), fld('find', 'Find', 'fish', 'text'),
      fld('rep', 'Replace with', 'cat', 'text'), fld('all', 'Replace all', '', 'select',
        { options: [{ value: 'yes', label: 'All' }, { value: 'no', label: 'First only' }] })],
    run: (v) => { if (!v.find) return v.in; return v.all === 'no' ? v.in.replace(v.find, v.rep) : v.in.split(v.find).join(v.rep); } },
  { id: 'slugify', name: 'Slugify', category: 'Text', tags: ['slug', 'url', 'seo', 'text'],
    fields: [fld('in', 'Text', 'Hello World!')],
    run: (v) => v.in.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') },
  { id: 'camel-case', name: 'camelCase', category: 'Text', tags: ['camel', 'case', 'identifier'],
    fields: [fld('in', 'Text', 'hello world foo')],
    run: (v) => { const w = v.in.replace(/([a-z])([A-Z])/g, '$1 $2').split(/[^a-zA-Z0-9]+/).filter(Boolean);
      return w.map((x, i) => i ? x[0].toUpperCase() + x.slice(1).toLowerCase() : x.toLowerCase()).join(''); } },
  { id: 'snake-case', name: 'snake_case', category: 'Text', tags: ['snake', 'case', 'identifier'],
    fields: [fld('in', 'Text', 'Hello World Foo')],
    run: (v) => v.in.replace(/([a-z])([A-Z])/g, '$1_$2').replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_+|_+$/g, '').toLowerCase() },
  { id: 'kebab-case', name: 'kebab-case', category: 'Text', tags: ['kebab', 'case', 'identifier'],
    fields: [fld('in', 'Text', 'Hello World Foo')],
    run: (v) => v.in.replace(/([a-z])([A-Z])/g, '$1-$2').replace(/[^a-zA-Z0-9]+/g, '-').replace(/^-+|-+$/g, '').toLowerCase() },
  { id: 'line-numbers', name: 'Add Line Numbers', category: 'Text', tags: ['number', 'lines', 'text'],
    fields: [fld('in', 'Text', 'alpha\nbeta\ngamma')],
    run: (v) => String(v.in).split(/\r?\n/).map((l, i) => `${i + 1}. ${l}`).join('\n') },
  { id: 'escape-string', name: 'Escape JS / JSON String', category: 'Text', tags: ['escape', 'string', 'json', 'javascript'],
    fields: [fld('in', 'Text', 'line1\n"quoted"')],
    run: (v) => JSON.stringify(v.in).slice(1, -1) },

  /* --- Design ------------------------------------------------------------ */
  { id: 'hex-to-rgb', name: 'HEX → RGB', category: 'Design', tags: ['color', 'hex', 'rgb', 'design'],
    fields: [fld('in', 'Hex color', '#ff9d00', 'text')],
    run: (v) => { const m = String(v.in).trim().replace('#', '');
      const full = m.length === 3 ? m.split('').map((c) => c + c).join('') : m;
      if (!/^[0-9a-f]{6}$/i.test(full)) return 'Invalid hex color';
      return `rgb(${parseInt(full.slice(0,2),16)}, ${parseInt(full.slice(2,4),16)}, ${parseInt(full.slice(4,6),16)})`; } },
  { id: 'rgb-to-hex', name: 'RGB → HEX', category: 'Design', tags: ['color', 'rgb', 'hex', 'design'],
    fields: [fld('in', 'R, G, B', '255, 157, 0', 'text')],
    run: (v) => { const n = String(v.in).match(/\d+/g); if (!n || n.length < 3) return 'Expected three numbers';
      return '#' + n.slice(0, 3).map((x) => Math.max(0, Math.min(255, +x)).toString(16).padStart(2, '0')).join(''); } },
  { id: 'hsl-to-hex', name: 'HSL → HEX', category: 'Design', tags: ['color', 'hsl', 'hex', 'design'],
    fields: [fld('h', 'Hue (0-360)', '33', 'text'), fld('s', 'Saturation %', '100', 'text'), fld('l', 'Lightness %', '50', 'text')],
    run: (v) => {
      const h = ((+v.h) % 360 + 360) % 360, s = Math.max(0, Math.min(100, +v.s)) / 100, l = Math.max(0, Math.min(100, +v.l)) / 100;
      const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs((h / 60) % 2 - 1)), m = l - c / 2;
      let r = 0, g = 0, b = 0;
      if (h < 60) [r, g, b] = [c, x, 0]; else if (h < 120) [r, g, b] = [x, c, 0];
      else if (h < 180) [r, g, b] = [0, c, x]; else if (h < 240) [r, g, b] = [0, x, c];
      else if (h < 300) [r, g, b] = [x, 0, c]; else [r, g, b] = [c, 0, x];
      return '#' + [r, g, b].map((n) => Math.round((n + m) * 255).toString(16).padStart(2, '0')).join('');
    } },
  { id: 'shade-color', name: 'Lighten / Darken Color', category: 'Design', tags: ['color', 'shade', 'lighten', 'darken'],
    fields: [fld('hex', 'Hex color', '#ff9d00', 'text'), fld('amt', 'Amount (-100..100)', '-20', 'text')],
    run: (v) => { const m = String(v.hex).trim().replace('#', '');
      const full = m.length === 3 ? m.split('').map((c) => c + c).join('') : m;
      if (!/^[0-9a-f]{6}$/i.test(full)) return 'Invalid hex color';
      const a = Math.max(-100, Math.min(100, +v.amt || 0)) / 100;
      const ch = [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16))
        .map((n) => Math.round(a >= 0 ? n + (255 - n) * a : n * (1 + a))
          .toString(16).padStart(2, '0')).join('');
      return '#' + ch; } },
  { id: 'contrast', name: 'WCAG Contrast Ratio', category: 'Design', tags: ['contrast', 'wcag', 'accessibility', 'color'],
    fields: [fld('fg', 'Foreground hex', '#ff9d00', 'text'), fld('bg', 'Background hex', '#000000', 'text')],
    run: (v) => {
      const lum = (hex) => { const m = hex.replace('#', ''); const f = m.length === 3 ? m.split('').map((c) => c + c).join('') : m;
        if (!/^[0-9a-f]{6}$/i.test(f)) return null;
        const c = [0, 2, 4].map((i) => { const x = parseInt(f.slice(i, i + 2), 16) / 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; };
      const a = lum(String(v.fg).trim()), b = lum(String(v.bg).trim());
      if (a === null || b === null) return 'Invalid hex color';
      const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
      const grade = ratio >= 7 ? 'AAA' : ratio >= 4.5 ? 'AA' : ratio >= 3 ? 'AA Large' : 'Fail';
      return `${ratio.toFixed(2)}:1\n${grade}`;
    } },
  { id: 'palette', name: 'Complementary Palette', category: 'Design', tags: ['palette', 'complement', 'color', 'design'],
    fields: [fld('in', 'Hex color', '#ff9d00', 'text')],
    run: (v) => {
      const m = String(v.in).trim().replace('#', ''); const f = m.length === 3 ? m.split('').map((c) => c + c).join('') : m;
      if (!/^[0-9a-f]{6}$/i.test(f)) return 'Invalid hex color';
      const rgb = [0, 2, 4].map((i) => parseInt(f.slice(i, i + 2), 16));
      const comp = rgb.map((n) => (255 - n).toString(16).padStart(2, '0')).join('');
      const shift = (d) => '#' + rgb.map((n, i) => ((n + (i === 0 ? d : i === 1 ? d : 0) + 256) % 256).toString(16).padStart(2, '0')).join('');
      return `Base       #${f}\nComplement #${comp}\nAnalogous  ${shift(-40)}  ${shift(40)}`;
    } },
  { id: 'gradient', name: 'CSS Gradient Generator', category: 'Design', tags: ['css', 'gradient', 'color', 'design'],
    fields: [fld('c1', 'Start color', '#ff9d00', 'text'), fld('c2', 'End color', '#000000', 'text'), fld('angle', 'Angle (deg)', '135', 'text')],
    run: (v) => `linear-gradient(${v.angle}deg, ${v.c1}, ${v.c2});` },
  { id: 'box-shadow', name: 'CSS Box Shadow Generator', category: 'Design', tags: ['css', 'shadow', 'box', 'design'],
    fields: [fld('x', 'X offset', '0', 'text'), fld('y', 'Y offset', '4', 'text'), fld('blur', 'Blur', '10', 'text'),
      fld('spread', 'Spread', '0', 'text'), fld('color', 'Color', 'rgba(0,0,0,0.5)', 'text')],
    run: (v) => `box-shadow: ${v.x}px ${v.y}px ${v.blur}px ${v.spread}px ${v.color};` },
  { id: 'text-shadow', name: 'CSS Text Shadow Generator', category: 'Design', tags: ['css', 'shadow', 'text', 'design'],
    fields: [fld('x', 'X offset', '1', 'text'), fld('y', 'Y offset', '1', 'text'), fld('blur', 'Blur', '2', 'text'), fld('color', 'Color', '#000', 'text')],
    run: (v) => `text-shadow: ${v.x}px ${v.y}px ${v.blur}px ${v.color};` },
];

const CATEGORIES = ['Pinned', 'Data', 'Encoding', 'Cryptography', 'Text', 'Design'];

/* ------------------------------------------------------------ component */
class DevtoolPlusPanel extends LitElement {
  static properties = {
    open: { type: Boolean, reflect: true },
    query: { state: true },
    category: { state: true },
    selected: { state: true },
    values: { state: true },
    outputs: { state: true },
    pinned: { state: true },
    copied: { state: true },
  };

  constructor() {
    super();
    this.open = false;
    this.query = '';
    this.category = 'Data';
    this.selected = TOOLS[0].id;
    this.values = {};
    this.outputs = {};
    this.pinned = this._loadPinned();
    this.copied = false;
    this._runToken = 0;
    for (const t of TOOLS) {
      const v = {};
      for (const f of t.fields) v[f.key] = f.type === 'select' ? (f.options[0]?.value ?? '') : (f.default ?? f.placeholder ?? '');
      this.values[t.id] = v;
    }
  }

  static styles = css`
    :host {
      --dtp-bg: var(--ace-bg, #000);
      --dtp-panel: var(--ace-panel, #0a0a0a);
      --dtp-accent: var(--ace-accent, #ff9d00);
      --dtp-border: var(--ace-border, #ff9d00);
      --dtp-text: var(--ace-text, #ff9d00);
      --dtp-muted: var(--ace-muted, #9a7b3f);
      --dtp-error: #ff5c5c;
      display: none;
      flex: 0 0 auto;
      width: 420px;
      min-width: 320px;
      max-width: 60vw;
      height: 100%;
      box-sizing: border-box;
      background: var(--dtp-bg);
      color: var(--dtp-text);
      border-left: 1px solid var(--dtp-border);
      font-family: 'Roboto Mono', monospace;
      font-size: 12px;
      z-index: 5;
    }
    :host([open]) { display: flex; flex-direction: column; }
    .head { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-bottom: 1px solid var(--dtp-border); }
    .title { font-weight: 700; color: var(--dtp-accent); letter-spacing: .5px; white-space: nowrap; }
    .badge { color: var(--dtp-muted); font-size: 10px; white-space: nowrap; }
    input, select, textarea, button {
      font-family: inherit; font-size: 12px; box-sizing: border-box;
      background: var(--dtp-bg); color: var(--dtp-text);
      border: 1px solid var(--dtp-border); border-radius: 3px; outline: none;
    }
    input:focus, select:focus, textarea:focus { box-shadow: 0 0 0 1px var(--dtp-accent); }
    .search { flex: 1; min-width: 0; padding: 5px 7px; }
    .iconbtn { padding: 3px 7px; cursor: pointer; }
    .iconbtn:hover { background: var(--dtp-accent); color: #000; }
    .cats { display: flex; flex-wrap: wrap; gap: 4px; padding: 7px 8px; border-bottom: 1px solid #333; }
    .cat { padding: 3px 8px; cursor: pointer; border-color: #444; color: var(--dtp-muted); }
    .cat.active { background: var(--dtp-accent); color: #000; border-color: var(--dtp-accent); }
    .body { display: flex; flex: 1; min-height: 0; }
    *::-webkit-scrollbar { width: 10px; height: 10px; }
    *::-webkit-scrollbar-track { background: #000; }
    *::-webkit-scrollbar-thumb { background: #ffa500; border: 1px solid #ffa500; border-radius: 4px; }
    *::-webkit-scrollbar-thumb:hover { background: #ffbf00; }
    .list { width: 40%; overflow-y: auto; border-right: 1px solid #333; }
    .item { display: flex; align-items: center; gap: 4px; padding: 5px 7px; cursor: pointer; border-bottom: 1px solid #1c1c1c; }
    .item:hover { background: #141414; }
    .item.active { background: #1a1400; border-left: 2px solid var(--dtp-accent); }
    .item .nm { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .pin { background: none; border: none; color: var(--dtp-muted); cursor: pointer; font-size: 13px; padding: 0 2px; }
    .pin.on { color: var(--dtp-accent); }
    .work { flex: 1; min-width: 0; display: flex; flex-direction: column; padding: 9px; gap: 7px; overflow-y: auto; }
    .wtitle { color: var(--dtp-accent); font-weight: 700; font-size: 13px; }
    .field { display: flex; flex-direction: column; gap: 3px; }
    .field label { color: var(--dtp-muted); font-size: 10px; text-transform: uppercase; letter-spacing: .5px; }
    .field textarea { width: 100%; min-height: 58px; resize: vertical; padding: 6px; }
    .field input, .field select { width: 100%; padding: 5px 6px; }
    .outhead { display: flex; align-items: center; gap: 6px; margin-top: 2px; }
    .outhead span { flex: 1; color: var(--dtp-muted); font-size: 10px; text-transform: uppercase; }
    .outhead button { padding: 3px 7px; cursor: pointer; }
    pre.out { margin: 0; width: 100%; min-height: 90px; max-height: 40vh; overflow: auto; white-space: pre-wrap;
      word-break: break-word; background: var(--dtp-panel); border: 1px solid #333; padding: 8px; color: #c8c8c8; }
    .empty { color: var(--dtp-muted); padding: 10px; }
    .foot { padding: 5px 9px; border-top: 1px solid #333; color: var(--dtp-muted); font-size: 10px; }
  `;

  _loadPinned() {
    try { return JSON.parse(localStorage.getItem('devtoolplus.pinned') || '[]'); }
    catch { return []; }
  }
  _savePinned() {
    try { localStorage.setItem('devtoolplus.pinned', JSON.stringify(this.pinned)); } catch { /* storage disabled */ }
  }
  _tool(id) { return TOOLS.find((t) => t.id === id); }
  get selectedTool() { return this._tool(this.selected) || TOOLS[0]; }

  get visibleTools() {
    const q = this.query.trim().toLowerCase();
    return TOOLS.filter((t) => {
      if (this.category === 'Pinned') return this.pinned.includes(t.id);
      if (t.category !== this.category) return false;
      if (!q) return true;
      return (t.name + ' ' + t.category + ' ' + t.tags.join(' ')).toLowerCase().includes(q);
    });
  }

  _setField(tool, key, value) {
    this.values = { ...this.values, [tool.id]: { ...this.values[tool.id], [key]: value } };
    this._run(tool);
  }

  async _run(tool) {
    if (!tool) return;
    const token = ++this._runToken;
    try {
      const out = await tool.run(this.values[tool.id] || {});
      if (token !== this._runToken) return; // a newer field change won
      this.outputs = { ...this.outputs, [tool.id]: String(out ?? '') };
    } catch (e) {
      if (token !== this._runToken) return;
      this.outputs = { ...this.outputs, [tool.id]: '⚠ ' + (e.message || String(e)) };
    }
  }

  firstUpdated() { this._run(this.selectedTool); }

  updated(changed) {
    if (changed.has('selected')) this._run(this.selectedTool);
  }

  _select(id) { this.selected = id; }
  _togglePin(id, e) {
    e.stopPropagation();
    this.pinned = this.pinned.includes(id) ? this.pinned.filter((x) => x !== id) : [...this.pinned, id];
    this._savePinned();
  }
  async _copy() {
    const text = this.outputs[this.selected] || '';
    try { await navigator.clipboard.writeText(text); }
    catch {
      const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta);
      ta.select(); try { document.execCommand('copy'); } catch { /* ignore */ } ta.remove();
    }
    this.copied = true;
    clearTimeout(this._copyTimer);
    this._copyTimer = setTimeout(() => { this.copied = false; }, 1200);
  }
  _close() { this.open = false; }

  _renderField(tool, field) {
    const val = this.values[tool.id]?.[field.key] ?? '';
    if (field.type === 'select') {
      return html`<div class="field"><label>${field.label}</label>
        <select .value=${val} @change=${(e) => this._setField(tool, field.key, e.target.value)}>
          ${field.options.map((o) => html`<option value=${o.value}>${o.label}</option>`)}
        </select></div>`;
    }
    if (field.type === 'textarea') {
      return html`<div class="field"><label>${field.label}</label>
        <textarea .value=${val} placeholder=${field.placeholder}
          @input=${(e) => this._setField(tool, field.key, e.target.value)}></textarea></div>`;
    }
    return html`<div class="field"><label>${field.label}</label>
      <input type="text" .value=${val} placeholder=${field.placeholder}
        @input=${(e) => this._setField(tool, field.key, e.target.value)}></div>`;
  }

  render() {
    const tool = this.selectedTool;
    const out = this.outputs[tool.id] ?? '';
    return html`
      <div class="head">
        <span class="title">DevTool+</span>
        <span class="badge">${TOOLS.length} local tools</span>
        <input class="search" type="text" placeholder="Search name, category, tag…"
          .value=${this.query} @input=${(e) => { this.query = e.target.value; }}>
        <button class="iconbtn" title="Close DevTool+" @click=${this._close}>✕</button>
      </div>
      <div class="cats">
        ${CATEGORIES.map((c) => html`<button class="cat ${this.category === c ? 'active' : ''}"
          @click=${() => { this.category = c; }}>${c === 'Pinned' ? '📌 ' : ''}${c}</button>`)}
      </div>
      <div class="body">
        <div class="list">
          ${this.visibleTools.length ? this.visibleTools.map((t) => html`
            <div class="item ${t.id === this.selected ? 'active' : ''}" @click=${() => this._select(t.id)}>
              <span class="nm" title=${t.tags.join(', ')}>${t.name}</span>
              <button class="pin ${this.pinned.includes(t.id) ? 'on' : ''}" title="Pin tool"
                @click=${(e) => this._togglePin(t.id, e)}>${this.pinned.includes(t.id) ? '★' : '☆'}</button>
            </div>`) : html`<div class="empty">No tools here yet.</div>`}
        </div>
        <div class="work">
          <div class="wtitle">${tool.name}</div>
          <div class="wtitle" style="font-size:10px;font-weight:400;color:var(--dtp-muted)">${tool.tags.map((x) => '#' + x).join(' ')}</div>
          ${tool.fields.map((f) => this._renderField(tool, f))}
          ${tool.action ? html`<button @click=${() => this._run(tool)}>Generate</button>` : ''}
          <div class="outhead">
            <span>Output · updates instantly${tool.action ? '' : ' as you type'}</span>
            <button @click=${() => this._run(tool)} title="Refresh">↻</button>
            <button @click=${this._copy} title="Copy output">${this.copied ? 'Copied!' : 'Copy'}</button>
          </div>
          <pre class="out">${out}</pre>
        </div>
      </div>
      <div class="foot">🔒 Local only · nothing leaves this browser · offline ready</div>
    `;
  }
}

customElements.define('devtool-plus-panel', DevtoolPlusPanel);

/* Global toggle used by the Code Editor toolbar button. */
window.toggleDevToolPlus = function (force) {
  const panel = document.getElementById('devtool-plus-panel');
  if (!panel) return false;
  panel.open = typeof force === 'boolean' ? force : !panel.open;
  return panel.open;
};
window.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.altKey && (e.key === 'd' || e.key === 'D')) {
    e.preventDefault();
    window.toggleDevToolPlus();
  }
});

/* ------------------------------------------------------- programmatic API
 * ACEsi itself uses the SAME tools the panel uses. The server calls this object
 * through CDP (devtool_list / devtool_run), so the model and the user can never
 * drift apart: one TOOLS array, one implementation, all local/offline.
 */
const _fieldInfo = (f) => {
  const info = { key: f.key, label: f.label, type: f.type, placeholder: f.placeholder || '' };
  if (f.options) info.options = f.options.map((o) => ({ value: o.value, label: o.label }));
  return info;
};

function findTool(idOrName) {
  const key = String(idOrName || '').trim().toLowerCase();
  if (!key) return null;
  return TOOLS.find((t) => t.id.toLowerCase() === key
    || t.name.toLowerCase() === key
    || t.tags.some((tag) => tag.toLowerCase() === key)) || null;
}

function normalizeValues(tool, values) {
  const fields = tool.fields || [];
  const args = {};
  for (const f of fields) {
    args[f.key] = f.type === 'select' ? (f.options[0]?.value ?? '') : '';
  }
  if (values === undefined || values === null || values === '') return args;
  if (typeof values !== 'object' || Array.isArray(values)) {
    if (fields.length) {
      args[fields[0].key] = Array.isArray(values) ? values.join('\n') : String(values);
    }
    return args;
  }
  for (const [k, v] of Object.entries(values)) {
    const declared = fields.find((f) => f.key === k
      || f.key.toLowerCase() === String(k).toLowerCase());
    args[declared ? declared.key : k] =
      (v === null || v === undefined) ? '' : (typeof v === 'object' ? JSON.stringify(v) : String(v));
  }
  return args;
}

const devToolPlusApi = {
  version: 1,
  count: TOOLS.length,
  categories: CATEGORIES.slice(),
  list(filter) {
    const f = typeof filter === 'string' ? { query: filter } : (filter || {});
    const q = String(f.query || f.q || '').trim().toLowerCase();
    const cat = String(f.category || '').trim().toLowerCase();
    return TOOLS.filter((t) => {
      if (cat && t.category.toLowerCase() !== cat) return false;
      if (!q) return true;
      return (t.id + ' ' + t.name + ' ' + t.category + ' ' + t.tags.join(' '))
        .toLowerCase().includes(q);
    }).map((t) => ({
      id: t.id, name: t.name, category: t.category, tags: t.tags,
      fields: (t.fields || []).map(_fieldInfo), action: !!t.action,
    }));
  },
  describe(idOrName) {
    const t = findTool(idOrName);
    return t ? { id: t.id, name: t.name, category: t.category, tags: t.tags,
      fields: (t.fields || []).map(_fieldInfo), action: !!t.action } : null;
  },
  async run(idOrName, values) {
    const t = findTool(idOrName);
    if (!t) throw new Error('Unknown DevTool+ tool: ' + idOrName);
    const args = normalizeValues(t, values);
    const out = await t.run(args);
    return { id: t.id, name: t.name, category: t.category,
      input: args, output: String(out ?? '') };
  },
};
window.devToolPlus = devToolPlusApi;
window.devtoolPlus = devToolPlusApi; // tolerant lowercase alias
