import { useState } from 'react';
import { ClipboardCheck, Copy, RotateCw } from 'lucide-react';
import { KNOWN_FIXES, normalize, looksLikeItsUrl, isValidItsUrl } from '../lib/itsUrlFixer';

const inputCls =
  'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none ring-indigo-500/50 focus:border-indigo-500 focus:ring-1';
const btnCls =
  'inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-all';

export default function UrlNormalizer() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState('');
  const [copied, setCopied] = useState(false);

  function handleNormalize() {
    const out = normalize(url);
    setResult(out);
    setCopied(false);
  }

  function handleRandom() {
    const bad = Object.keys(KNOWN_FIXES)[Math.floor(Math.random() * Object.keys(KNOWN_FIXES).length)];
    const demo = `https://${'univenierp01.univen.ac.za'}/pls/prodi41/${bad}?ts=${Date.now()}`;
    setUrl(demo);
    handleNormalize();
  }

  const valid = url ? isValidItsUrl(url) : null;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="url"
          className={inputCls}
          placeholder="https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1v"
          value={url}
          onChange={(e) => { setUrl(e.target.value); setCopied(false); }}
        />
        <button
          onClick={handleRandom}
          className={`${btnCls} border border-slate-700 text-slate-300 hover:bg-slate-800`}
          title="Insert a demo truncated URL"
        >
          <RotateCw size={16} className="mr-2" />
          Demo
        </button>
        <button
          onClick={handleNormalize}
          className={`${btnCls} border border-slate-700 text-slate-300 hover:bg-slate-800`}
          disabled={!url}
        >
          <ClipboardCheck size={16} className="mr-2" />
          Normalize
        </button>
      </div>

      {valid === false && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
          ⚠ This URL contains a known truncation pattern and would 404.
        </div>
      )}
      {valid === true && url && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300">
          ✓ URL looks valid — no truncated procedure detected.
        </div>
      )}

      {result && (
        <div className="space-y-2">
          <div className="text-xs font-medium text-slate-300">Result</div>
          <div className="relative">
            <pre
              className="w-full rounded-lg border border-slate-800/60 bg-slate-950/60 p-3 font-mono text-xs text-emerald-300 overflow-x-auto break-all"
              aria-label="normalized-url"
            >
              {result}
            </pre>
            <button
              onClick={() => { navigator.clipboard.writeText(result); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
              className="absolute top-2 right-2 rounded-md p-1 text-slate-400 hover:text-slate-200"
              title="Copy"
            >
              {copied ? <span className="text-xs text-emerald-400">copied</span> : <Copy size={16} />}
            </button>
          </div>
          {looksLikeItsUrl(result) && result !== url && (
            <div className="text-xs text-emerald-400">Fixed procedure names detected and restored.</div>
          )}
        </div>
      )}

      <div className="rounded-lg border border-slate-800/60 bg-slate-900/40 p-4">
        <div className="text-xs font-medium text-slate-300 mb-2">Known truncations</div>
        <table className="w-full table-auto text-left text-xs">
          <thead>
            <tr className="text-slate-400">
              <th className="pb-1">Truncated</th>
              <th className="pb-1">Restored</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(KNOWN_FIXES).map(([bad, good]) => (
              <tr key={bad} className="border-t border-slate-800/60">
                <td className="py-1 font-mono text-amber-300">{bad}</td>
                <td className="py-1 font-mono text-emerald-300">{good}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
