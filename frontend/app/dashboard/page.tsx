"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchMasterySnapshot,
  fetchAttemptHistory,
  MasterySnapshotItem,
  AttemptHistoryItem,
} from "@/lib/api";
import WeakestConceptWidget from "@/components/dashboard/WeakestConceptWidget";
import MasteryRadarChart from "@/components/dashboard/MasteryRadarChart";
import DivergenceTimelineChart from "@/components/dashboard/DivergenceTimelineChart";
import MisunderstandingFeed from "@/components/dashboard/MisunderstandingFeed";
import OnboardingModal from "@/components/ui/OnboardingModal";

export default function DashboardPage() {
  const [masteryItems, setMasteryItems] = useState<MasterySnapshotItem[]>([]);
  const [attempts, setAttempts] = useState<AttemptHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(true);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);
    try {
      const [mList, aList] = await Promise.all([
        fetchMasterySnapshot(),
        fetchAttemptHistory(),
      ]);
      setMasteryItems(mList);
      setAttempts(aList);
    } catch (err: any) {
      console.error("Failed to load dashboard data:", err);
      setError("Could not connect to backend service. Showing offline simulation mode.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboardData();

    // Auto-open onboarding once per user session
    const hasSeen = localStorage.getItem("repair_has_seen_onboarding");
    if (!hasSeen) {
      setIsOnboardingOpen(true);
      localStorage.setItem("repair_has_seen_onboarding", "true");
    }
  }, []);

  // Summary Metrics
  const avgMastery =
    masteryItems.length > 0
      ? Math.round(
          (masteryItems.reduce((acc, curr) => acc + curr.mastery_score, 0) /
            masteryItems.length) *
            100
        )
      : 0;

  const totalAttempts = attempts.length;
  const luckyGuessesCount = attempts.filter((a) => a.misunderstanding_flag).length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20 selection:bg-indigo-500 selection:text-white">
      {/* Onboarding Modal */}
      <OnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
      />

      {/* Navigation Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-20 shadow-sm">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="font-black text-xl tracking-tight text-slate-950">
              Repair
            </Link>
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase tracking-wide">
              Mastery Dashboard
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs font-semibold">
            {/* Onboarding tour button */}
            <button
              onClick={() => setIsOnboardingOpen(true)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors flex items-center gap-1.5"
            >
              <span>ℹ️</span>
              <span>How It Works</span>
            </button>

            {/* Demo mode badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg text-[11px] font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Demo Mode Active</span>
            </div>

            <Link
              href="/workspace"
              className="px-3.5 py-1.5 bg-black text-white rounded-lg hover:bg-slate-800 transition-colors shadow-sm"
            >
              Workspaces →
            </Link>

            <form action="/api/auth/signout" method="post">
              <button
                type="submit"
                className="text-slate-400 hover:text-rose-600 transition-colors px-2 py-1"
              >
                Sign Out
              </button>
            </form>
          </div>
        </div>
      </header>

      {/* Main Dashboard Content */}
      <main className="max-w-6xl mx-auto mt-6 px-4 space-y-6">
        {/* Error / Offline Alert */}
        {error && (
          <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
            <span>{error}</span>
            <button
              onClick={loadDashboardData}
              className="font-bold underline hover:text-black ml-4"
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading ? (
          <div className="space-y-6 animate-pulse">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="h-24 bg-slate-200 rounded-xl"></div>
              <div className="h-24 bg-slate-200 rounded-xl"></div>
              <div className="h-24 bg-slate-200 rounded-xl"></div>
            </div>
            <div className="h-40 bg-slate-200 rounded-xl"></div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="h-80 bg-slate-200 rounded-xl"></div>
              <div className="h-80 bg-slate-200 rounded-xl"></div>
            </div>
          </div>
        ) : (
          <>
            {/* Top KPI Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Overall BKT Mastery
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-slate-900">{avgMastery}%</span>
                  <span className="text-xs text-slate-400">across {masteryItems.length} concepts</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Evaluated Attempts
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-blue-600">{totalAttempts}</span>
                  <span className="text-xs text-slate-400">multi-domain submissions</span>
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Lucky Guesses Flagged
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-amber-600">{luckyGuessesCount}</span>
                  <span className="text-xs text-amber-800 font-semibold">misconceptions detected</span>
                </div>
              </div>
            </div>

            {/* 1. Weakest Concept Across All Domains Widget */}
            <WeakestConceptWidget items={masteryItems} />

            {/* 2. Charts Row: Radar Chart + Divergence Timeline Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <MasteryRadarChart items={masteryItems} />
              <DivergenceTimelineChart attempts={attempts} />
            </div>

            {/* 3. Feed of misunderstanding_flag=true Moments */}
            <MisunderstandingFeed attempts={attempts} />

            {/* 4. Quick Launch Workspaces Grid */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-slate-900">5 Repair Workspaces</h3>
                  <p className="text-xs text-slate-500">
                    Launch directly into an interactive domain sandbox to diagnose and repair broken artifacts.
                  </p>
                </div>
                <Link href="/workspace" className="text-xs font-bold text-indigo-600 hover:underline">
                  View All →
                </Link>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { name: "Code", slug: "code", icon: "💻", color: "bg-blue-50/50 border-blue-200 hover:border-blue-400" },
                  { name: "Physics", slug: "physics", icon: "🚀", color: "bg-emerald-50/50 border-emerald-200 hover:border-emerald-400" },
                  { name: "Story", slug: "story", icon: "📖", color: "bg-purple-50/50 border-purple-200 hover:border-purple-400" },
                  { name: "Business Model", slug: "business-model", icon: "📊", color: "bg-amber-50/50 border-amber-200 hover:border-amber-400" },
                  { name: "Chemistry", slug: "chemistry", icon: "🧪", color: "bg-rose-50/50 border-rose-200 hover:border-rose-400" },
                ].map((ws) => (
                  <Link
                    key={ws.slug}
                    href={`/workspace/${ws.slug}`}
                    className={`p-4 rounded-xl border text-center transition-all shadow-sm hover:shadow-md block ${ws.color}`}
                  >
                    <span className="text-2xl block mb-1">{ws.icon}</span>
                    <span className="font-bold text-xs text-slate-900 block">{ws.name}</span>
                  </Link>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
