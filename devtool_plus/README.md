# DevTool+

A local-only developer utility toolkit docked into ACEsi's Code Editor. Built with
Lit, bundled to `../static/devtool-plus.js`, and served from Flask's default
`/static/` route. No network calls, no CDN, no external services — everything
runs in the browser, offline.

## Files
- `src/devtool-plus.js` — the Lit component and the tool definitions.
- `../static/devtool-plus.js` — the generated offline bundle loaded by `ACEsi.html`.
- `package.json` / `package-lock.json` — pinned build dependencies.

## Rebuild after editing a tool
```bat
cd devtool_plus
npm install
npm run build
```
Then hard-reload `http://127.0.0.1:5000/` in the browser.

## Adding a tool
Add an entry to the `TOOLS` array in `src/devtool-plus.js`:

```js
{ id: 'unique-id', name: 'Display Name', category: 'Text', tags: ['tag1', 'tag2'],
  fields: [ fld('in', 'Input label', 'placeholder') ],
  run: (v) => doSomething(v.in) }          // may be async
```

- `category` must be one of `Data`, `Encoding`, `Cryptography`, `Text`, `Design`
  (add it to `CATEGORIES` if you introduce a new one).
- `fields` support `textarea` (default), `text`, and `select` (pass `options`).
- `run` receives `{ fieldKey: value }` and returns a string (or a Promise of one).
  Output updates instantly as the user types. Set `action: true` for tools with
  no input that need a Generate button (e.g. the UUID generator).
- Pinned favorites and are stored in `localStorage` under `devtoolplus.pinned`.

The toolbar button in ACEsi's Code Editor calls `window.toggleDevToolPlus()`;
`Ctrl+Alt+D` does the same.
