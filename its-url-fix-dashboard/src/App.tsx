import { useState } from 'react';
import { BugIcon, Search, Code, Activity } from 'lucide-react';
import BugOverview from './components/BugOverview';
import UrlNormalizer from './components/UrlNormalizer';
import FlutterFixCode from './components/FlutterFixCode';
import DiagnosticSimulator from './components/DiagnosticSimulator';

type TabId = 'overview' | 'normalizer' | 'code' | 'simulator';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const TABS: Tab[] = [
  { id: 'overview', label: 'Bug Overview', icon: <BugIcon size={18} /> },
  { id: 'normalizer', label: 'URL Normalizer', icon: <Search size={18} /> },
  { id: 'code', label: 'Flutter Fix Code', icon: <Code size={18} /> },
  { id: 'simulator', label: 'Diagnostic Sim', icon: <Activity size={18} /> },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800/60 bg-slate-950/50 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-red-500 to-orange-600 shadow-lg shadow-red-900/30">
              <BugIcon size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight sm:text-xl">
                ITS URL Fix Dashboard
              </h1>
              <p className="text-xs text-slate-400">
                UNIVEN WebView 404 Bug — <span className="font-mono text-emerald-400">gw1v</span> → <span className="font-mono text-emerald-400">gw1view</span>
              </p>
            </div>
          </div>
          <div className="rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
            Fix Active
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="border-b border-slate-800/60 bg-slate-950/30">
        <div className="mx-auto flex max-w-6xl px-4 sm:px-6">
          <div className="flex gap-1 overflow-x-auto py-2">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-500/30'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">
        {activeTab === 'overview' && <BugOverview />}
        {activeTab === 'normalizer' && <UrlNormalizer />}
        {activeTab === 'code' && <FlutterFixCode />}
        {activeTab === 'simulator' && <DiagnosticSimulator />}
      </main>
    </div>
  );
}
