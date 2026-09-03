"use client";

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea,
} from "recharts";
import { AttemptHistoryItem } from "@/lib/api";

interface DivergenceTimelineChartProps {
  attempts: AttemptHistoryItem[];
}

/**
 * [PLACEHOLDER-STYLED]: Timeline chart tracking Fix Correctness vs. Understanding Score.
 * Visually emphasizes divergence moments (lucky guesses where fix was right but understanding was low).
 * Note: A dedicated UI visual pass could add custom area gradient shading between the two lines to highlight the divergence delta even more prominently.
 */
export default function DivergenceTimelineChart({ attempts }: DivergenceTimelineChartProps) {
  const chartData = useMemo(() => {
    return attempts.map((att, idx) => {
      const fixPct = Math.round(att.fix_correctness * 100);
      const underPct = Math.round(att.understanding_score * 100);
      const divergenceGap = fixPct - underPct;
      const isLuckyGuess = att.fix_correctness >= 0.7 && att.understanding_score < 0.5;

      return {
        index: idx + 1,
        name: `Attempt #${idx + 1}`,
        concept: att.concept_name,
        domain: att.domain_name,
        fixCorrectness: fixPct,
        understandingScore: underPct,
        divergenceGap,
        isLuckyGuess,
        date: new Date(att.created_at).toLocaleDateString(),
      };
    });
  }, [attempts]);

  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-gray-900">
              Fix Correctness vs. Understanding Divergence
            </h3>
            <span className="px-2 py-0.5 text-[10px] font-extrabold uppercase bg-indigo-100 text-indigo-900 rounded">
              Core Insight
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Timeline tracking whether you genuinely understood the root cause or got lucky with a working fix.
          </p>
        </div>

        {/* Visual Legend Guide */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-blue-600 inline-block"></span>
            <span className="text-gray-600 font-medium">Fix Correctness</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-purple-600 inline-block"></span>
            <span className="text-gray-600 font-medium">Understanding Score</span>
          </div>
        </div>
      </div>

      {/* Chart Viewport */}
      <div className="w-full h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
            <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} tickLine={false} unit="%" />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-gray-900 text-white text-xs p-3.5 rounded-lg shadow-xl border border-gray-700 space-y-2 max-w-xs">
                      <div className="font-bold border-b border-gray-700 pb-1 flex justify-between">
                        <span>{d.name}: {d.concept}</span>
                        <span className="text-gray-400 font-normal">{d.date}</span>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-blue-300">
                          <span>Fix Correctness:</span>
                          <span className="font-mono font-bold">{d.fixCorrectness}%</span>
                        </div>
                        <div className="flex justify-between text-purple-300">
                          <span>Understanding:</span>
                          <span className="font-mono font-bold">{d.understandingScore}%</span>
                        </div>
                        <div className="flex justify-between text-amber-300 pt-1 border-t border-gray-800">
                          <span>Divergence Delta:</span>
                          <span className="font-mono font-bold">
                            {d.divergenceGap > 0 ? `+${d.divergenceGap}%` : `${d.divergenceGap}%`}
                          </span>
                        </div>
                      </div>

                      {d.isLuckyGuess && (
                        <div className="p-1.5 bg-yellow-900/60 border border-yellow-600/50 rounded text-[11px] text-yellow-200">
                          ⚠️ Lucky Guess: Fix worked but explanation indicated misconception.
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Line
              type="monotone"
              dataKey="fixCorrectness"
              name="Fix Correctness"
              stroke="#2563eb"
              strokeWidth={3}
              dot={{ r: 4, fill: "#2563eb" }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="understandingScore"
              name="Understanding Score"
              stroke="#9333ea"
              strokeWidth={3}
              dot={{ r: 4, fill: "#9333ea" }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs text-gray-600 flex items-center justify-between">
        <span>
          💡 <b>How to read this:</b> When the blue and purple lines stay close and trend upward, you are achieving true mastery. When the blue line is high and the purple line dips, you had a lucky guess without grasping the root cause.
        </span>
      </div>
    </div>
  );
}
