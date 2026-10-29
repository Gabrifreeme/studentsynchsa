import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import itsUrlFixerSource from '../lib/ItsUrlFixer.dart?raw';

export default function FlutterFixCode() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(itsUrlFixerSource);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lines = itsUrlFixerSource.split('\n');

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-300">
        This is the production Dart interceptor that runs in the StudentSyncSA
        Flutter app. It detects truncated ITS procedure names and restores them
        <span className="font-mono text-emerald-300"> gw1v → gw1view</span>
        before the WebView loads the URL, preventing the 404.
      </p>

      <div className="flex items-center justify-between">
        <h2 className="text-xs font-medium text-slate-300">ItsUrlFixer.dart</h2>
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 rounded-md border border-slate-700 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-800"
        >
          {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>

      <div className="relative">
        <pre className="overflow-x-auto rounded-xl bg-slate-950/70 p-4 font-mono text-xs text-slate-300">
          <code className="block">
            {lines.map((line, i) => (
              <span key={i} className="table-row">
                <span className="table-cell select-none text-slate-600 text-right pr-4 mr-4 border-r border-slate-800/60">
                  {i + 1}
                </span>
                <span>{line}</span>
              </span>
            ))}
          </code>
        </pre>
      </div>

      <div className="rounded-lg border border-slate-800/60 bg-slate-900/40 p-4">
        <div className="text-xs font-medium text-slate-300 mb-2">Key mapping</div>
        <div className="font-mono text-xs text-emerald-300">
          gen.gw1pkg.gw1v → gen.gw1pkg.gw1view<br />
          gen.gw1pkg.gw1p → gen.gw1pkg.gw1print<br />
          gen.gw1pkg.gw1c → gen.gw1pkg.gw1call<br />
          gen.gw1pkg.gw1i → gen.gw1pkg.gw1init<br />
          gen.gw1pkg.gw1s → gen.gw1pkg.gw1submit<br />
          gen.gw1pkg.gw1u → gen.gw1pkg.gw1update<br />
          gen.gw1pkg.gw1d → gen.gw1pkg.gw1delete
        </div>
      </div>
    </div>
  );
}