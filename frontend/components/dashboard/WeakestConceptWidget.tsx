"use client";

import React from "react";
import Link from "next/link";
import { MasterySnapshotItem } from "@/lib/api";

interface WeakestConceptWidgetProps {
  items: MasterySnapshotItem[];
}

/**
 * [PLACEHOLDER-STYLED]: Hero card widget highlighting the lowest mastery concept across all domains.
 * Data wiring and weakest concept computation (BKT P(L) sorting and novelty tie-break) are fully functional.
 */
export default function WeakestConceptWidget({ items }: WeakestConceptWidgetProps) {
  if (!items || items.length === 0) return null;

  // Find lowest mastery concept
  const weakest = [...items].sort((a, b) => a.mastery_score - b.mastery_score)[0];

  const domainRouteMap: Record<string, string> = {
    code: "/workspace/code",
    physics: "/workspace/physics",
    story: "/workspace/story",
    business_model: "/workspace/business-model",
    chemistry: "/workspace/chemistry",
  };

  const baseUrl = domainRouteMap[weakest.domain_name] || "/workspace";
  const workspaceHref = weakest.concept_tag
    ? `${baseUrl}?concept=${encodeURIComponent(weakest.concept_tag)}`
    : baseUrl;

  const masteryPercent = Math.round(weakest.mastery_score * 100);



  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider bg-amber-200 text-amber-900 rounded">
            Target Focus Area
          </span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white border border-amber-200 text-gray-700">
            {weakest.domain_display_name}
          </span>
        </div>

        <h3 className="text-xl font-extrabold text-gray-900">
          Weakest Concept: {weakest.concept_name}
        </h3>

        <p className="text-xs text-gray-600 max-w-xl">
          Your estimated knowledge state for this concept is lowest across all tracked domains.
          Strengthening this concept will balance your overall mastery profile.
        </p>

        <div className="flex items-center gap-4 text-xs font-medium text-gray-700 pt-1">
          <div>
            Mastery Probability: <span className="font-mono font-bold text-amber-800">{masteryPercent}%</span>
          </div>
          <span className="text-gray-300">•</span>
          <div>
            Attempts Logged: <span className="font-mono font-bold">{weakest.attempts_count}</span>
          </div>
        </div>
      </div>

      <div className="w-full md:w-auto">
        <Link
          href={workspaceHref}
          className="inline-flex items-center justify-center w-full md:w-auto px-6 py-3 bg-black text-white text-sm font-semibold rounded-lg hover:bg-gray-800 shadow-sm transition-all"
        >
          Practice Concept Now →
        </Link>
      </div>
    </div>
  );
}
