'use client';
import { useState } from "react";

export default function ProfilePage() {
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSave = () => {
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const fieldClass =
    "w-full rounded-lg bg-[#f5f5f5] border border-[#d1d5db] px-4 py-3 text-[#1a1a1a] placeholder-gray-400 focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED] transition-colors";

  const selectClass =
    "w-full appearance-none rounded-lg bg-[#f5f5f5] border border-[#d1d5db] px-4 py-3 text-[#1a1a1a] focus:border-[#7C3AED] focus:outline-none focus:ring-1 focus:ring-[#7C3AED] transition-colors";

  const labelClass = "block text-sm font-medium text-[#374151]";

  return (
    <div className="min-h-screen bg-[#f0f2f5] text-[#1a1a1a]">
      {/* Top Navigation Bar */}
      <div className="sticky top-0 z-10 flex items-center justify-between bg-white/90 backdrop-blur px-4 py-3 shadow-sm">
        <button className="text-gray-500 hover:text-gray-700">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-[#1a1a1a]">Complete Your Profile</h1>
        <div className="w-8"></div>
      </div>

      {/* Progress Bar */}
      <div className="px-4 pt-4">
        <div className="h-1.5 w-full rounded-full bg-[#e5e7eb]">
          <div className="h-1.5 w-1/3 rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A78BFA]"></div>
        </div>
        <p className="mt-2 text-center text-xs text-gray-400">Step 1 of 3</p>
      </div>

      <div className="mx-auto mt-6 max-w-xl px-4 pb-32">
        {/* Biographical Details Section */}
        <section className="rounded-xl bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-[#1a1a1a]">Biographical Details</h2>
          <p className="mt-1 text-sm text-gray-500">
            In this section you are required to enter your biographical details.
          </p>

          <div className="mt-5 space-y-4">
            {/* Nationality */}
            <div>
              <label className={labelClass}>Nationality</label>
              <p className="mt-1 text-xs text-gray-400">
                Please select your current nationality and capture your ID or passport number.
              </p>
              <div className="mt-2 relative">
                <select className={selectClass}>
                  <option>SA Citizen</option>
                  <option>Permanent Resident</option>
                  <option>Foreign National</option>
                </select>
                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>

            {/* SA Citizenship Code */}
            <div>
              <label className={labelClass}>SA Citizenship Code *</label>
              <div className="mt-2 relative">
                <select className={selectClass}>
                  <option>RSA - South Africa</option>
                  <option>Permanent Resident</option>
                  <option>Foreign National</option>
                </select>
                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>

            {/* ID / Passport Number */}
            <div>
              <label className={labelClass}>ID / Passport Number *</label>
              <div className="mt-2 relative">
                <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="16" rx="2" />
                    <circle cx="9" cy="12" r="2" />
                    <path d="M15 8h3M15 12h3M15 16h2" />
                  </svg>
                </div>
                <input
                  type="text"
                  defaultValue="6303160134088"
                  className={`${fieldClass} pl-12`}
                  placeholder="Enter ID/Passport Number"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Personal Information Section */}
        <section className="mt-5 rounded-xl bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-[#1a1a1a]">Personal Information</h2>
          <p className="mt-1 text-sm text-gray-500">Please enter your personal information.</p>

          <div className="mt-5 space-y-4">
            {/* Gender */}
            <div>
              <label className={labelClass}>Gender *</label>
              <div className="mt-2 relative">
                <select className={selectClass}>
                  <option>Female</option>
                  <option>Male</option>
                  <option>Other</option>
                </select>
                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Date of Birth */}
            <div>
              <label className={labelClass}>Date of birth (DD-MON-YYYY) *</label>
              <div className="mt-2 relative">
                <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" />
                    <path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                </div>
                <input
                  type="text"
                  defaultValue="16/3/1963"
                  className={`${fieldClass} pl-12`}
                  placeholder="DD-MON-YYYY"
                />
                <button className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className={labelClass}>Title *</label>
              <div className="mt-2 relative">
                <select className={selectClass}>
                  <option>Mrs</option>
                  <option>Mr</option>
                  <option>Dr</option>
                  <option>Prof</option>
                  <option>Ms</option>
                </select>
                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Initials */}
            <div>
              <label className={labelClass}>Initials *</label>
              <div className="mt-2 relative">
                <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 7V4h16v3M9 20h6M12 4v16" />
                  </svg>
                </div>
                <input
                  type="text"
                  defaultValue="L"
                  className={`${fieldClass} pl-12`}
                  placeholder="Enter Initials"
                />
              </div>
            </div>

            {/* Surname */}
            <div>
              <label className={labelClass}>Surname *</label>
              <div className="mt-2 relative">
                <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
                <input
                  type="text"
                  defaultValue="Buys"
                  className={`${fieldClass} pl-12`}
                  placeholder="Enter Surname"
                />
              </div>
            </div>

            {/* First Names */}
            <div>
              <label className={labelClass}>First names *</label>
              <div className="mt-2 relative">
                <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
                <input
                  type="text"
                  defaultValue="Laura"
                  className={`${fieldClass} pl-12`}
                  placeholder="Enter First Names"
                />
              </div>
            </div>

            {/* Maiden Name */}
            <div>
              <label className={labelClass}>Maiden name</label>
              <div className="mt-2 relative">
                <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </div>
                <input
                  type="text"
                  defaultValue=""
                  className={`${fieldClass} pl-12`}
                  placeholder="Enter Maiden Name"
                />
              </div>
            </div>

            {/* Marital Status */}
            <div>
              <label className={labelClass}>Marital status *</label>
              <div className="mt-2 relative">
                <select className={selectClass}>
                  <option>Divorced</option>
                  <option>Single</option>
                  <option>Married</option>
                  <option>Widowed</option>
                  <option>Domestic Partner</option>
                </select>
                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Home Language */}
            <div>
              <label className={labelClass}>Home language *</label>
              <div className="mt-2 relative">
                <select className={selectClass}>
                  <option>ENGLISH</option>
                  <option>AFRIKAANS</option>
                  <option>ZULU</option>
                  <option>XHOSA</option>
                  <option>OTHER</option>
                </select>
                <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Success Message */}
      {showSuccess && (
        <div className="fixed bottom-24 left-4 right-4 z-50 animate-fade-in">
          <div className="rounded-lg bg-green-600 px-4 py-3 text-center text-sm font-medium text-white shadow-lg">
            Profile Updated Successfully
          </div>
        </div>
      )}

      {/* Bottom Action Buttons */}
      <div className="fixed bottom-0 left-0 right-0 z-10 border-t border-gray-200 bg-white/95 backdrop-blur px-4 py-4">
        <div className="mx-auto flex max-w-xl gap-3">
          <button
            onClick={handleSave}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300"
          >
            Save
          </button>
          <button className="flex-1 rounded-lg bg-gradient-to-r from-[#7C3AED] to-[#A78BFA] px-4 py-3 text-sm font-medium text-white hover:from-[#6D28D9] hover:to-[#9333EA] focus:outline-none focus:ring-2 focus:ring-[#7C3AED]">
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
