import { useState } from 'react';
import type { ReactNode } from 'react';
import { Play, RotateCw, Trash2 } from 'lucide-react';
import { diagnose, KNOWN_FIXES } from '../lib/itsUrlFixer';
import type { DiagStep } from '../lib/itsUrlFixer';

const inputCls =
  'w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 outline-none ring-indigo-500/50 focus:border-indigo-500 focus:ring-1';
const btnCls =
  'inline-flex items-center justify-center rounded-lg px-3.5 py-2 text-sm font-medium transition-all';

const STATUS_ICON: Record<DiagStep['status'], ReactNode> = {
  info: <span className="text-slate-400">ℹ</span>,
  pass: <span className="text-emerald-400">✓</span>,
  fail: <span className="text-red-400">✗</span>,
  ok: <span className="text-emerald-400">✓</span>,
  warn: <span className="text-amber-400">!</span>,
};

export default function DiagnosticSimulator() {
  const [url, setUrl] = useState('');
  const [steps, setSteps] = useState<DiagStep[]>([]);

  function handleRun() {
    if (!url) return;
    setSteps(diagnose(url));
  }

  function handleDemo() {
    const bad = Object.keys(KNOWN_FIXES)[Math.floor(Math.random() * Object.keys(KNOWN_FIXES).length)];
    const demo = `https://univenierp01.univen.ac.za/pls/prodi41/${bad}`;
    setUrl(demo);
    setSteps(diagnose(demo));
  }

  function handleClear() {
    setUrl('');
    setSteps([]);
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-300">
        Paste an ITS URL and watch the simulator trace it step by step — from parse
        to truncation detection to the normalized result.
      </p>

      <div className="flex gap-2">
        <input
          type="url"
          className={inputCls}
          placeholder="https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1v"
          value={url}
          onChange={(e) => { setUrl(e.target.value); setSteps([]); }}
        />
        <button
          onClick={handleDemo}
          className={`${btnCls} border border-slate-700 text-slate-300 hover:bg-slate-800`}
          title="Load a demo truncated URL"
        >
          <RotateCw size={16} className="mr-2" />
          Demo
        </button>
        <button
          onClick={handleRun}
          className={`${btnCls} border border-slate-700 text-slate-300 hover:bg-slate-800`}
          disabled={!url}
        >
          <Play size={16} className="mr-2" />
          Diagnose
        </button>
        <button
          onClick={handleClear}
          className={`${btnCls} border border-slate-700 text-slate-300 hover:bg-slate-800`}
          title="Clear"
        >
          <Trash2 size={16} />
        </button>
      </div>

      {steps.length === 0 ? (
        <div className="rounded-xl border border-slate-800/60 bg-slate-900/40 p-6 text-center text-sm text-slate-400">
          Enter a URL and click <span className="font-medium text-slate-300">Diagnose</span> to see the trace.
        </div>
      ) : (
        <div className="space-y-2">
          {steps.map((s, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 rounded-lg border p-3 text-sm ${
                s.status === 'fail'
                  ? 'border-red-500/30 bg-red-500/10'
                  : s.status === 'ok'
                  ? 'border-emerald-500/30 bg-emerald-500/10'
                  : s.status === 'warn'
                  ? 'border-amber-500/30 bg-amber-500/10'
                  : 'border-slate-800/60 bg-slate-900/40'
              }`}
            >
              <span
                className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded-full text-xs ${
                  s.status === 'fail'
                    ? 'bg-red-500/20 text-red-400'
                    : s.status === 'ok'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : s.status === 'warn'
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-slate-700/30 text-slate-400'
                }`}
              >
                {i + 1}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-slate-200">{s.step}</span>
                  {STATUS_ICON[s.status]}
                </div>
                <pre className="mt-1 max-w-[calc(100% - 2.5rem)] overflow-x-auto font-mono text-xs text-slate-300">
                  {s.message}
                </pre>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
