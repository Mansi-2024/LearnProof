"use client";

import React, { useState, useMemo } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { MasterySnapshotItem } from "@/lib/api";

interface MasteryRadarChartProps {
  items: MasterySnapshotItem[];
}

const DOMAIN_TABS = [
  { id: "all", label: "All Domains" },
  { id: "code", label: "Code" },
  { id: "physics", label: "Physics" },
  { id: "story", label: "Story" },
  { id: "business_model", label: "Business Model" },
  { id: "chemistry", label: "Chemistry" },
];

/**
 * [PLACEHOLDER-STYLED]: Radar Chart visualization of BKT concept mastery.
 * Data mapping, domain grouping, polar scaling, and interactive filtering are fully functional.
 * Note: A dedicated UI visual pass could polish radar grid styling, gradients, and custom polar point glyphs.
 */
export default function MasteryRadarChart({ items }: MasteryRadarChartProps) {
  const [selectedDomain, setSelectedDomain] = useState("all");

  const filteredData = useMemo(() => {
    const list =
      selectedDomain === "all"
        ? items
        : items.filter((i) => i.domain_name === selectedDomain);

    return list.map((item) => ({
      concept: item.concept_name,
      mastery: Math.round(item.mastery_score * 100),
      domain: item.domain_display_name,
      attempts: item.attempts_count,
      fullMark: 100,
    }));
  }, [items, selectedDomain]);

  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-gray-900">Concept Mastery Profile (BKT)</h3>
          <p className="text-xs text-gray-500">
            Bayesian Knowledge Tracing probability of mastery across target concepts.
          </p>
        </div>

        {/* Domain Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          {DOMAIN_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedDomain(tab.id)}
              className={`px-2.5 py-1 text-xs rounded-md font-medium whitespace-nowrap transition-colors ${
                selectedDomain === tab.id
                  ? "bg-black text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Radar Chart Container */}
      <div className="w-full h-80 flex items-center justify-center">
        {filteredData.length < 3 ? (
          <div className="text-center text-xs text-gray-400 py-12">
            Need at least 3 concepts in this category to render a full radar polygon.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={filteredData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis
                dataKey="concept"
                tick={{ fill: "#475569", fontSize: 11, fontWeight: 500 }}
              />
              <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-gray-900 text-white text-xs p-3 rounded-lg shadow-lg border border-gray-700 space-y-1">
                        <div className="font-bold text-sm">{data.concept}</div>
                        <div className="text-gray-300">Domain: {data.domain}</div>
                        <div className="text-indigo-300 font-mono">
                          Mastery Score: <b>{data.mastery}%</b>
                        </div>
                        <div className="text-gray-400">Total Attempts: {data.attempts}</div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Radar
                name="Mastery"
                dataKey="mastery"
                stroke="#4f46e5"
                fill="#6366f1"
                fillOpacity={0.4}
              />
            </RadarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
