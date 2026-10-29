import Link from "next/link";


export default function HomePage() {
  return (
    <main className="grid min-h-screen place-items-center px-6 py-12">
      <section className="w-full max-w-2xl rounded-3xl bg-white p-10 shadow-[0_24px_60px_rgba(16,24,40,0.12)]">
        <p className="m-0 text-sm uppercase tracking-[0.08em] text-slate-600">Starter template</p>
        <h1 className="mt-4 text-[clamp(2rem,5vw,3.25rem)] font-semibold leading-[1.05] text-slate-950">
          Arena Next.js PostgreSQL Starter
        </h1>
        <p className="mt-4 text-base text-slate-700">
          Server-rendered with Next.js after a successful PostgreSQL query through Drizzle.
        </p>
        <div className="mt-8 space-y-3">
          <Link
            href="/complete-profile"
            className="block rounded-lg bg-blue-600 px-6 py-3 text-center text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Go to Complete Profile
          </Link>
          <Link
            href="/its-portal"
            className="block rounded-lg bg-[#8B5CF6] px-6 py-3 text-center text-sm font-medium text-white hover:bg-[#7C3AED] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6] focus:ring-offset-2"
          >
            Go to ITS Portal
          </Link>
        </div>
      </section>
    </main>
  );
}
