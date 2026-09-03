"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import WorkspaceShell from "@/components/workspace/WorkspaceShell";
import CodeWorkspace from "@/components/workspace/CodeWorkspace";
import { ArtifactData, generateLiveArtifact } from "@/lib/api";

const SAMPLE_CODE_ARTIFACT: ArtifactData = {
  id: "code-artifact-demo-1",
  domain_slug: "code",
  target_concept: "recursion-base-case",
  artifact_payload: {
    language: "python",
    code: `def factorial(n):
    # Bug: Missing base case for n <= 1
    return n * factorial(n - 1)
`,
    test_cases: [
      { input: "factorial(1)", expected_output: "1", actual_output: "RecursionError: maximum recursion depth exceeded" },
      { input: "factorial(4)", expected_output: "24", actual_output: "RecursionError: maximum recursion depth exceeded" },
    ],
  },
  root_cause: "The recursive function factorial(n) lacks a terminating condition (if n <= 1: return 1), causing infinite recursion and stack overflow.",
  expected_behavior: "factorial(1) should return 1; factorial(4) should return 24.",
  actual_behavior: "Execution throws RecursionError due to uncontrolled infinite recursive calls.",
};

function CodeWorkspaceInner() {
  const searchParams = useSearchParams();
  const targetConcept = searchParams.get("concept") || "recursion-base-case";

  const [artifact, setArtifact] = useState<ArtifactData>(SAMPLE_CODE_ARTIFACT);
  const [submittedFix, setSubmittedFix] = useState<Record<string, any>>({
    code: artifact.artifact_payload.code,
    language: artifact.artifact_payload.language,
  });
  const [generating, setGenerating] = useState(false);

  async function loadArtifact(concept: string) {
    setGenerating(true);
    const live = await generateLiveArtifact("code", concept, 0.5);
    if (live && live.artifact_payload && live.artifact_payload.code) {
      setArtifact(live);
      setSubmittedFix({
        code: live.artifact_payload.code,
        language: live.artifact_payload.language || "python",
      });
    }
    setGenerating(false);
  }

  useEffect(() => {
    loadArtifact(targetConcept);
  }, [targetConcept]);

  return (
    <WorkspaceShell
      domain="code"
      domainDisplayName="Code"
      targetConcept={targetConcept.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      artifact={artifact}
      submittedFix={submittedFix}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-blue-50/60 p-3 rounded-lg border border-blue-100 text-xs">
          <span className="text-blue-900 font-medium">
            Active Concept: <b className="font-bold">{artifact.target_concept || targetConcept}</b>
          </span>
          <button
            onClick={() => loadArtifact(targetConcept)}
            disabled={generating}
            className="px-3 py-1 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50 transition-colors text-[11px]"
          >
            {generating ? "Generating Artifact..." : "⚡ Generate New Artifact (Grok AI)"}
          </button>
        </div>

        <CodeWorkspace
          key={artifact.id}
          initialCode={artifact.artifact_payload.code}
          language={artifact.artifact_payload.language || "python"}
          testCases={artifact.artifact_payload.test_cases || []}
          onChange={setSubmittedFix}
        />
      </div>
    </WorkspaceShell>
  );
}

export default function CodeWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Code Workspace...</div>}>
      <CodeWorkspaceInner />
    </Suspense>
  );
}
