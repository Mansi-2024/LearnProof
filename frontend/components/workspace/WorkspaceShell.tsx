"use client";

import React, { useState } from "react";
import { fetchHint, submitVerification, VerifyFixResult, ArtifactData } from "@/lib/api";

interface WorkspaceShellProps {
  domain: string;
  domainDisplayName: string;
  targetConcept: string;
  artifact: ArtifactData;
  submittedFix: Record<string, any>;
  children: React.ReactNode;
}

/**
 * [PLACEHOLDER-STYLED]: Shell layout, domain headers, and verification panel.
 * Interaction logic (progressive hints, explanation capture, submission to /verify-fix) is fully functional.
 */
export default function WorkspaceShell({
  domain,
  domainDisplayName,
  targetConcept,
  artifact,
  submittedFix,
  children,
}: WorkspaceShellProps) {
  const [explanation, setExplanation] = useState("");
  const [hintLevel, setHintLevel] = useState<number>(0);
  const [hintText, setHintText] = useState<string | null>(null);
  const [hintLoading, setHintLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<VerifyFixResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Progressive Hint Handler
  async function handleGetHint(nextLevel: number) {
    setHintLoading(true);
    setError(null);
    try {
      const hint = await fetchHint(artifact.id, nextLevel);
      setHintLevel(nextLevel);
      setHintText(hint);
    } catch (err: any) {
      setError("Failed to fetch hint: " + err.message);
    } finally {
      setHintLoading(false);
    }
  }

  // Submit Handler
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!explanation.trim()) {
      setError("Please provide an explanation of why the artifact was broken.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const verification = await submitVerification({
        artifact_id: artifact.id,
        submitted_fix: submittedFix,
        submitted_explanation: explanation,
        artifact_context: artifact,
      });
      setResult(verification);
    } catch (err: any) {
      setError(err.message || "Failed to submit verification.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 pb-20">
      {/* Top Header / Domain Banner */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <a href="/dashboard" className="text-sm font-medium text-gray-500 hover:text-black">
            ← Dashboard
          </a>
          <span className="text-gray-300">|</span>
          <span className="px-2.5 py-1 text-xs font-semibold uppercase tracking-wider bg-blue-100 text-blue-800 rounded">
            {domainDisplayName}
          </span>
          <h1 className="text-lg font-bold">Concept: {targetConcept}</h1>
        </div>

        {/* Progressive Hint Drawer Controls */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-medium">Progressive Hints:</span>
          {[1, 2, 3].map((lvl) => (
            <button
              key={lvl}
              type="button"
              onClick={() => handleGetHint(lvl)}
              disabled={hintLoading}
              className={`px-3 py-1 text-xs rounded border transition-colors ${
                hintLevel === lvl
                  ? "bg-amber-100 border-amber-400 text-amber-900 font-semibold"
                  : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              {lvl === 1 ? "Level 1 (Nudge)" : lvl === 2 ? "Level 2 (Rule)" : "Level 3 (Diagnostic)"}
            </button>
          ))}
        </div>
      </header>

      {/* Hint Banner if active */}
      {hintText && (
        <div className="max-w-6xl mx-auto mt-4 px-4">
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start justify-between gap-3 shadow-sm">
            <div>
              <span className="font-semibold text-amber-900 text-sm">
                Hint Level {hintLevel}:{" "}
              </span>
              <span className="text-sm text-amber-800">{hintText}</span>
            </div>
            <button
              onClick={() => setHintText(null)}
              className="text-xs text-amber-600 hover:text-amber-800 font-bold"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Interactive Workspace Area */}
      <main className="max-w-6xl mx-auto mt-6 px-4 space-y-6">
        {/* Context Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
              Expected Behavior
            </h3>
            <p className="text-sm text-gray-800">{artifact.expected_behavior}</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-red-200 bg-red-50/30 shadow-sm">
            <h3 className="text-xs font-bold text-red-600 uppercase tracking-wider mb-1">
              Actual Behavior (Defect)
            </h3>
            <p className="text-sm text-gray-800">{artifact.actual_behavior}</p>
          </div>
        </div>

        {/* Domain-specific interactive component */}
        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
          {children}
        </div>

        {/* Universal Explanation & Submission Panel */}
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm space-y-4">
          <div>
            <label htmlFor="explanation" className="block text-sm font-bold text-gray-800 mb-1">
              Why was this broken? (Explain the root cause and your rationale)
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Note: The AI Judge grades your conceptual explanation separately from the fix. Lucky guesses without sound reasoning will be flagged.
            </p>
            <textarea
              id="explanation"
              rows={4}
              required
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              placeholder="Explain the underlying flaw, which invariant or rule was violated, and why your fix resolves it..."
              className="w-full rounded-md border border-gray-300 p-3 text-sm focus:ring-2 focus:ring-black focus:outline-none"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-md">
              {error}
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-gray-400">
              Submits to <code className="bg-gray-100 px-1 py-0.5 rounded">POST /verify-fix</code>
            </span>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 bg-black text-white text-sm font-medium rounded-md hover:bg-gray-800 disabled:opacity-50 transition-colors"
            >
              {submitting ? "Evaluating with AI Judge..." : "Submit for Verification →"}
            </button>
          </div>
        </form>

        {/* Verification Result Card */}
        {result && (
          <div className="bg-white p-6 rounded-lg border-2 border-indigo-200 shadow-md space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h2 className="text-lg font-bold text-gray-900">Verification Results</h2>
              <span className="text-xs font-semibold px-2 py-1 rounded bg-green-100 text-green-800">
                Mastery Updated via BKT
              </span>
            </div>

            {/* Score Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Fix Correctness</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-blue-600">
                    {(result.fix_correctness * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-gray-500">
                    {result.fix_correctness >= 0.8 ? "Passed" : "Needs Revision"}
                  </span>
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <span className="text-xs font-medium text-gray-500 uppercase">Understanding Score</span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-3xl font-extrabold text-purple-600">
                    {(result.understanding_score * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-gray-500">
                    {result.understanding_score >= 0.7 ? "High Conceptual Alignment" : "Partial Alignment"}
                  </span>
                </div>
              </div>
            </div>

            {/* Lucky Guess / Misconception Alert */}
            {result.misunderstanding_flag && (
              <div className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded-r-md">
                <div className="flex items-center gap-2">
                  <span className="text-lg">⚠️</span>
                  <h4 className="text-sm font-bold text-yellow-900">
                    Lucky Guess / Misconception Flagged
                  </h4>
                </div>
                <p className="text-xs text-yellow-800 mt-1">
                  Your fix resolved the immediate failure, but your explanation indicates a conceptual misunderstanding of the true root cause. Review the feedback below to cement the concept.
                </p>
              </div>
            )}

            {/* Feedback text */}
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-xs font-bold text-gray-600 uppercase mb-1">Judge Feedback</h4>
              <p className="text-sm text-gray-800 whitespace-pre-line">{result.feedback_text}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
