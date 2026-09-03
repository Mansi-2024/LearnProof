import Link from "next/link";
import { createSupabaseServerClient } from "@/lib/supabase/server";

export default async function HomePage() {
  const supabase = createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const DOMAINS = [
    { name: "Code", slug: "code", icon: "💻", badge: "Monaco + Live Eval", desc: "Debug recursion, async race conditions & off-by-one errors." },
    { name: "Physics", slug: "physics", icon: "🚀", badge: "Canvas Simulation", desc: "Correct inverted gravity vectors & trajectory calculations live." },
    { name: "Story", slug: "story", icon: "📖", badge: "Narrative Revision", desc: "Resolve spatial continuity paradoxes & plot inconsistencies." },
    { name: "Business Model", slug: "business-model", icon: "📊", badge: "Lean Canvas", desc: "Diagnose negative contribution margin & unscalable assumptions." },
    { name: "Chemistry", slug: "chemistry", icon: "🧪", badge: "Stoichiometry Balancer", desc: "Repair unbalanced reactions & mass conservation violations." },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <header className="px-6 py-5 max-w-6xl w-full mx-auto flex items-center justify-between border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <span className="text-xl font-black tracking-tight text-white">Repair</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wide">
            Multi-Domain
          </span>
        </div>

        <nav className="flex items-center gap-4 text-xs font-semibold">
          {user ? (
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-500/20"
            >
              Open Dashboard →
            </Link>
          ) : (
            <>
              <Link href="/workspace" className="text-slate-400 hover:text-white transition-colors">
                Explore Workspaces
              </Link>
              <Link href="/login" className="text-slate-300 hover:text-white transition-colors">
                Log In
              </Link>
              <Link
                href="/signup"
                className="px-4 py-2 bg-white text-slate-950 rounded-lg hover:bg-slate-200 transition-colors font-bold shadow-sm"
              >
                Get Started
              </Link>
            </>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl w-full mx-auto px-6 py-16 space-y-16">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Powered by Bayesian Knowledge Tracing &amp; Grok AI
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400">
            Master complex concepts by fixing broken artifacts.
          </h1>

          <p className="text-sm sm:text-base text-slate-400 leading-relaxed max-w-2xl mx-auto">
            Diagnose intentional bugs across code, physics simulations, narrative continuity, startup unit economics, and chemical reactions. We grade your fix <i>and</i> your conceptual rationale.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link
              href={user ? "/dashboard" : "/signup"}
              className="px-6 py-3.5 bg-indigo-600 text-white text-sm font-bold rounded-xl hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-600/30 hover:shadow-indigo-600/50 transform hover:-translate-y-0.5"
            >
              Start Learning Free →
            </Link>
            <Link
              href="/workspace"
              className="px-6 py-3.5 bg-slate-900 border border-slate-700 text-slate-200 text-sm font-semibold rounded-xl hover:bg-slate-800 hover:text-white transition-all"
            >
              Try Interactive Sandboxes
            </Link>
          </div>
        </div>

        {/* 5 Domain Sandboxes Feature Grid */}
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-xs font-bold uppercase tracking-widest text-indigo-400">
              5 Dedicated Repair Workspaces
            </h2>
            <p className="text-lg font-bold text-white mt-1">One engine, infinite domains.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {DOMAINS.map((d) => (
              <Link
                key={d.slug}
                href={`/workspace/${d.slug}`}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/60 transition-all duration-200 group flex flex-col justify-between hover:bg-slate-900 shadow-sm"
              >
                <div className="space-y-3">
                  <div className="text-3xl">{d.icon}</div>
                  <h3 className="font-bold text-sm text-white group-hover:text-indigo-300 transition-colors">
                    {d.name}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{d.desc}</p>
                </div>
                <div className="pt-4 mt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500 font-mono">{d.badge}</span>
                  <span className="text-indigo-400 group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* The Two-Score Core Insight Callout */}
        <div className="p-8 rounded-3xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 relative overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div className="space-y-4">
              <span className="px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-bold">
                The Anti-Lucky Guess Guarantee
              </span>
              <h3 className="text-2xl font-black text-white">
                Never confuse a lucky fix with true comprehension.
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                If you fix a bug by accident but your explanation reveals a false assumption (e.g. claiming Python arrays start at index 1), our Grok-powered AI Judge flags the misconception immediately and weights your BKT mastery accordingly.
              </p>
            </div>

            <div className="bg-slate-950 p-5 rounded-2xl border border-slate-800/80 space-y-3 font-mono text-xs shadow-inner">
              <div className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-400">Submission Evaluation:</span>
                <span className="text-emerald-400 font-bold">✓ Fix Correct (100%)</span>
              </div>
              <div className="flex justify-between text-amber-400 font-bold">
                <span>Understanding Score:</span>
                <span>20% (Misconception Flagged)</span>
              </div>
              <div className="p-3 bg-amber-950/40 border border-amber-800/40 rounded-lg text-amber-200/90 text-[11px] leading-relaxed">
                "Your base case ended the recursion, but your rationale that all Python functions require if statements is incorrect."
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-slate-800/80 text-center text-xs text-slate-500 max-w-6xl w-full mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <span>© 2026 Repair. Generalized Broken-Artifact Learning Engine.</span>
        <div className="flex items-center gap-4 text-slate-400">
          <Link href="/workspace" className="hover:text-white">Workspaces</Link>
          <Link href="/dashboard" className="hover:text-white">Dashboard</Link>
        </div>
      </footer>
    </div>
  );
}
