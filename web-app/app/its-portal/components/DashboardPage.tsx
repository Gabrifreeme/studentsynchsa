'use client';

export default function DashboardPage({ userName = 'Laura Buys', onNavigate }: { userName?: string; onNavigate?: (page: 'dashboard' | 'profile' | 'applications' | 'documents') => void }) {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold mb-2">Welcome, {userName}</h1>
      <p className="text-[#9CA3AF] mb-8">Manage your applications and profile from here.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <button
          onClick={() => onNavigate('profile')}
          className="bg-[#1E2635] rounded-xl p-6 text-left hover:bg-[#2A3447] transition-colors"
        >
          <div className="text-2xl mb-3">👤</div>
          <h3 className="font-semibold mb-1">My Profile</h3>
          <p className="text-sm text-[#6B7280]">Complete your biographical details</p>
        </button>

        <button
          onClick={() => onNavigate('applications')}
          className="bg-[#1E2635] rounded-xl p-6 text-left hover:bg-[#2A3447] transition-colors"
        >
          <div className="text-2xl mb-3">📝</div>
          <h3 className="font-semibold mb-1">Applications</h3>
          <p className="text-sm text-[#6B7280]">View and manage your applications</p>
        </button>

        <button
          onClick={() => onNavigate('documents')}
          className="bg-[#1E2635] rounded-xl p-6 text-left hover:bg-[#2A3447] transition-colors"
        >
          <div className="text-2xl mb-3">📁</div>
          <h3 className="font-semibold mb-1">Documents</h3>
          <p className="text-sm text-[#6B7280]">Upload supporting documents</p>
        </button>
      </div>
    </div>
  );
}
