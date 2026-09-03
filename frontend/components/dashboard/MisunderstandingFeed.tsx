"use client";

import React from "react";
import Link from "next/link";
import { AttemptHistoryItem } from "@/lib/api";

interface MisunderstandingFeedProps {
  attempts: AttemptHistoryItem[];
}

/**
 * [PLACEHOLDER-STYLED]: Misunderstanding Feed ("You fixed it, but didn't quite get why").
 * Growth-mindset non-punitive callout displaying lucky guess moments where fix succeeded but explanation revealed a misconception.
 */
export default function MisunderstandingFeed({ attempts }: MisunderstandingFeedProps) {
  const flagged = attempts.filter((a) => a.misunderstanding_flag);

  if (flagged.length === 0) {
    return (
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm text-center py-8">
        <span className="text-2xl">🎯</span>
        <h4 className="text-sm font-bold text-gray-900 mt-2">No Misunderstandings Flagged</h4>
        <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
          Every time your fix worked, your conceptual explanation aligned with the true root cause. Keep maintaining deep conceptual rigor!
        </p>
      </div>
    );
  }

  const domainRouteMap: Record<string, string> = {
    code: "/workspace/code",
    physics: "/workspace/physics",
    story: "/workspace/story",
    business_model: "/workspace/business-model",
    chemistry: "/workspace/chemistry",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-gray-900">
              Conceptual Misunderstandings &amp; Lucky Guesses ({flagged.length})
            </h3>
            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800">
              High-Value Learning Signal
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            Moments where your fix passed, but your explanation indicated a misconception. Reviewing these solidifies true intuition.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {flagged.map((item) => (
          <div
            key={item.id}
            className="p-5 bg-amber-50/40 border border-amber-200 rounded-xl shadow-sm hover:border-amber-400 transition-colors space-y-3"
          >
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span className="text-base">💡</span>
                <span className="font-bold text-sm text-gray-900">{item.concept_name}</span>
                <span className="px-2 py-0.5 text-[10px] font-semibold uppercase bg-white border border-amber-300 text-amber-900 rounded">
                  {item.domain_name}
                </span>
              </div>
              <span className="text-[11px] text-gray-400 font-mono">
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </div>

            {/* Score pill comparison */}
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded border border-gray-200 font-mono">
                <span className="text-gray-500">Fix Correctness:</span>
                <span className="font-bold text-green-700">{(item.fix_correctness * 100).toFixed(0)}% ✓</span>
              </div>
              <div className="flex items-center gap-1.5 bg-white px-2.5 py-1 rounded border border-amber-300 font-mono">
                <span className="text-gray-500">Understanding:</span>
                <span className="font-bold text-amber-800">{(item.understanding_score * 100).toFixed(0)}% ⚠️</span>
              </div>
            </div>

            {/* Student Explanation vs Feedback */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-white/80 rounded-lg border border-amber-200/60">
                <span className="font-bold text-gray-600 uppercase text-[10px] block mb-1">
                  Your Explanation at the Time:
                </span>
                <p className="text-gray-800 italic">"{item.submitted_explanation}"</p>
              </div>

              <div className="p-3 bg-amber-100/60 rounded-lg border border-amber-300/80">
                <span className="font-bold text-amber-900 uppercase text-[10px] block mb-1">
                  AI Judge Diagnostic Feedback:
                </span>
                <p className="text-amber-950">{item.feedback_text || "Explanation revealed conceptual confusion."}</p>
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <Link
                href={domainRouteMap[item.domain_name] || "/workspace"}
                className="text-xs font-semibold text-amber-900 hover:text-black underline"
              >
                Revisit &amp; Practice {item.concept_name} →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
