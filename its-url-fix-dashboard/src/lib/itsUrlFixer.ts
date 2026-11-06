// Mirrors lib/ItsUrlFixer.dart — Oracle PL/SQL gateway URL truncation fixer.

export const ITS_DOMAIN = 'univenierp01.univen.ac.za';

export const KNOWN_FIXES: Record<string, string> = {
  'gen.gw1pkg.gw1v': 'gen.gw1pkg.gw1view',
  'gen.gw1pkg.gw1p': 'gen.gw1pkg.gw1print',
  'gen.gw1pkg.gw1c': 'gen.gw1pkg.gw1call',
  'gen.gw1pkg.gw1i': 'gen.gw1pkg.gw1init',
  'gen.gw1pkg.gw1s': 'gen.gw1pkg.gw1submit',
  'gen.gw1pkg.gw1u': 'gen.gw1pkg.gw1update',
  'gen.gw1pkg.gw1d': 'gen.gw1pkg.gw1delete',
};

export const PROCEDURE_SUFFIXES = ['view', 'print', 'call', 'init', 'submit', 'update', 'delete'];

export function looksLikeItsUrl(url: string): boolean {
  const lower = url.toLowerCase();
  return (
    lower.includes(ITS_DOMAIN) ||
    lower.includes('/pls/prodi41/') ||
    (lower.includes('/pls/') && lower.includes('.gw1pkg.'))
  );
}

export function normalize(url: string): string {
  if (!looksLikeItsUrl(url)) return url;
  return fixTruncatedProcedureNames(url);
}

export function isValidItsUrl(url: string): boolean {
  if (!looksLikeItsUrl(url)) return true;
  for (const bad of Object.keys(KNOWN_FIXES)) {
    if (url.includes(bad) && !url.includes(KNOWN_FIXES[bad])) {
      return false;
    }
  }
  return true;
}

function fixTruncatedProcedureNames(url: string): string {
  for (const [bad, good] of Object.entries(KNOWN_FIXES)) {
    const qMark = url.indexOf('?');
    const pathPart = qMark !== -1 ? url.substring(0, qMark) : url;

    if (url.includes(`/${bad}`) || url.includes(`/${bad}?`) || url.endsWith(bad)) {
      let fixed = url.replaceAll(`/${bad}`, `/${good}`);
      if (fixed.endsWith(bad) && fixed !== url) {
        return fixed;
      }
      return url.replaceAll(bad, good);
    }

    if (pathPart.includes(bad)) {
      return url.replaceAll(bad, good);
    }
  }

  return smartRestoreSuffix(url);
}

function smartRestoreSuffix(url: string): string {
  const qMark = url.indexOf('?');
  const pathPart = qMark !== -1 ? url.substring(0, qMark) : url;

  // gen.gw1pkg.gw1X  (single trailing letter)
  const regex = /(gen\.gw1pkg\.gw1[a-zA-Z])/;
  const match = regex.exec(pathPart);
  if (match) {
    const truncated = match[0];
    const prefix = truncated.substring(0, truncated.length - 1);
    const letter = truncated.split('.').pop()!;
    for (const suffix of PROCEDURE_SUFFIXES) {
      if (suffix.startsWith(letter)) {
        return url.replace(truncated, `${prefix}${suffix}`);
      }
    }
  }

  // Broader: package.procedure where procedure is short and starts with gw1
  const pkgRegex = /(\w+\.\w+\.\w+)(\?|$)/;
  const pkgMatch = pkgRegex.exec(pathPart);
  if (pkgMatch) {
    const procedure = pkgMatch[1];
    const parts = procedure.split('.');
    if (parts.length >= 3) {
      const procName = parts[parts.length - 1];
      if (procName.startsWith('gw1') && procName.length < 8) {
        const restored = restoreGatewayProcedure(procName);
        if (restored !== procName) {
          const fullProcedure = `${parts[0]}.${parts[1]}.${restored}`;
          return url.replace(procedure, fullProcedure);
        }
      }
    }
  }

  return url;
}

function restoreGatewayProcedure(truncated: string): string {
  if (KNOWN_FIXES[truncated] !== undefined) {
    return KNOWN_FIXES[truncated];
  }
  for (const [bad, good] of Object.entries(KNOWN_FIXES)) {
    if (bad.startsWith(truncated)) {
      return good;
    }
  }
  return truncated;
}

export function findTruncated(url: string): string | null {
  if (!looksLikeItsUrl(url)) return null;
  const qMark = url.indexOf('?');
  const pathPart = qMark !== -1 ? url.substring(0, qMark) : url;

  for (const bad of Object.keys(KNOWN_FIXES)) {
    if (pathPart.includes(bad)) return bad;
  }

  const single = /(gen\.gw1pkg\.gw1[a-zA-Z])/.exec(pathPart);
  if (single) return single[1];

  const pkgRegex = /(\w+\.\w+\.gw1[a-zA-Z]{1,3})(\?|$)/;
  const pkgMatch = pkgRegex.exec(pathPart);
  if (pkgMatch) return pkgMatch[1];

  return null;
}

export type DiagStep = {
  step: string;
  status: 'info' | 'pass' | 'fail' | 'ok' | 'warn';
  message: string;
};

export function diagnose(url: string): DiagStep[] {
  const steps: DiagStep[] = [];
  steps.push({ step: 'Parse URL', status: 'info', message: url });

  if (!looksLikeItsUrl(url)) {
    steps.push({ step: 'ITS URL?', status: 'pass', message: 'Not an ITS / PL-SQL gateway URL — no fix needed.' });
    return steps;
  }
  steps.push({ step: 'ITS URL', status: 'pass', message: 'Matches ITS domain or /pls/ gateway.' });

  const truncated = findTruncated(url);
  if (truncated) {
    steps.push({ step: 'Truncation check', status: 'fail', message: `Truncated procedure detected: ${truncated}` });
    const fixed = normalize(url);
    steps.push({ step: 'Normalize', status: fixed !== url ? 'ok' : 'warn', message: fixed });
    steps.push({
      step: 'Result',
      status: fixed !== url ? 'ok' : 'warn',
      message: fixed !== url ? '404 resolved — fixed URL will load correctly.' : 'Truncation detected but could not auto-fix.',
    });
  } else {
    steps.push({ step: 'Truncation check', status: 'pass', message: 'No truncated procedure names found.' });
    steps.push({ step: 'Result', status: 'ok', message: 'URL is valid — will load correctly.' });
  }
  return steps;
}
