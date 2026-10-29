import { AlertTriangle, CheckCircle, Globe } from 'lucide-react';

const card = 'rounded-xl border border-slate-800/60 bg-slate-900/40 p-5';
const row = 'flex items-start gap-3';

export default function BugOverview() {
  return (
    <div className="space-y-5">
      <p className="text-sm text-slate-300">
        The UNIVEN Oracle WebLogic/PLSQL gateway truncates procedure names in ITS
        URLs before the WebView loads them, producing{' '}
        <span className="font-mono text-red-400">404 Not Found</span> errors for
        students on the Venda campus webview.
      </p>

      <div className={card}>
        <div className={row}>
          <Globe className="mt-0.5 h-5 w-5 text-red-400" />
          <div>
            <h2 className="font-semibold text-slate-200">Root cause</h2>
            <p className="mt-1 text-sm text-slate-400">
              The gateway sometimes cuts a procedure name after a 7-character boundary,
              e.g. <span className="font-mono text-emerald-300">gen.gw1pkg.gw1view</span>{' '}
              becomes <span className="font-mono text-amber-300">gen.gw1pkg.gw1v</span>.
              The truncated route no longer resolves, so the WebView returns 404.
            </p>
          </div>
        </div>
      </div>

      <div className={card}>
        <div className={row}>
          <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-400" />
          <div>
            <h2 className="font-semibold text-slate-200">Symptoms</h2>
            <ul className="mt-1 list-disc list-inside space-y-1 text-sm text-slate-400">
              <li>Blank/error page on the ITS portal inside the Venda campus webview.</li>
              <li>Network log shows a <span className="font-mono">404</span> for a <span className="font-mono">/pls/...gw1pkg.gw1X</span> URL.</li>
              <li>Re-opening or refreshing sometimes 'sticks' the truncated URL in history.</li>
            </ul>
          </div>
        </div>
      </div>

      <div className={card}>
        <div className={row}>
          <CheckCircle className="mt-0.5 h-5 w-5 text-emerald-400" />
          <div>
            <h2 className="font-semibold text-slate-200">Fix</h2>
            <p className="mt-1 text-sm text-slate-400">
              Intercept the URL and restore the full procedure name before it loads.{' '}
              <span className="font-mono text-emerald-300">gw1v → gw1view</span> (and the
              other procedure suffixes in the Fix Code tab). The dashboard's Normalizer and
              Diagnostic tabs validate any URL against the same rule set as the{' '}
              <span className="font-mono">ItsUrlFixer</span> Dart class.
            </p>
          </div>
        </div>
      </div>

      <div className="text-xs text-slate-500">
        Affected domain: <span className="font-mono">univenierp01.univen.ac.za</span> ·
        Gateway: <span className="font-mono">/pls/prodi41/</span> ·
        Affected procedures: gw1v, gw1p, gw1c, gw1i, gw1s, gw1u, gw1d
      </div>
    </div>
  );
}
