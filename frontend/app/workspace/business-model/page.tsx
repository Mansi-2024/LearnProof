"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import WorkspaceShell from "@/components/workspace/WorkspaceShell";
import BusinessModelWorkspace from "@/components/workspace/BusinessModelWorkspace";
import { ArtifactData, generateLiveArtifact } from "@/lib/api";

const SAMPLE_BIZ_ARTIFACT: ArtifactData = {
  id: "biz-artifact-demo-1",
  domain_slug: "business_model",
  target_concept: "unit-economics-contribution-margin",
  artifact_payload: {
    model_description: `QuickWash is an on-demand laundry delivery startup charging consumers $15 per bag. The company pays outsourced local laundromats $18 per bag to wash and fold, and pays gig drivers $5 per delivery. The founder projects profitability based on achieving 50,000 orders per month.`,
    flawed_assumption: "Flawed assumption: Negative unit contribution margin (-$8/order) cannot be fixed by increasing order volume — every incremental order accelerates cash burn.",
  },
  root_cause: "Negative gross contribution margin: Variable direct costs ($23) exceed revenue per order ($15), causing structural insolvency regardless of scale.",
  expected_behavior: "A viable business model where price ($28-$35) comfortably covers COGS, delivery, and marketing with positive gross contribution.",
  actual_behavior: "The startup burns $8 on every transaction, making scaling fatal.",
};

function BusinessModelWorkspaceInner() {
  const searchParams = useSearchParams();
  const targetConcept = searchParams.get("concept") || "unit-economics-contribution-margin";

  const [artifact, setArtifact] = useState<ArtifactData>(SAMPLE_BIZ_ARTIFACT);
  const [submittedFix, setSubmittedFix] = useState<Record<string, any>>({
    model_description: artifact.artifact_payload.model_description,
    flawed_assumption: artifact.artifact_payload.flawed_assumption,
  });
  const [generating, setGenerating] = useState(false);

  async function loadArtifact(concept: string) {
    setGenerating(true);
    const live = await generateLiveArtifact("business_model", concept, 0.5);
    if (live && live.artifact_payload && live.artifact_payload.model_description) {
      setArtifact(live);
      setSubmittedFix({
        model_description: live.artifact_payload.model_description,
        flawed_assumption: live.artifact_payload.flawed_assumption || "",
      });
    }
    setGenerating(false);
  }

  useEffect(() => {
    loadArtifact(targetConcept);
  }, [targetConcept]);

  return (
    <WorkspaceShell
      domain="business_model"
      domainDisplayName="Business Model"
      targetConcept={targetConcept.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      artifact={artifact}
      submittedFix={submittedFix}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-amber-50/60 p-3 rounded-lg border border-amber-100 text-xs">
          <span className="text-amber-900 font-medium">
            Active Concept: <b className="font-bold">{artifact.target_concept || targetConcept}</b>
          </span>
          <button
            onClick={() => loadArtifact(targetConcept)}
            disabled={generating}
            className="px-3 py-1 bg-amber-600 text-white font-semibold rounded hover:bg-amber-700 disabled:opacity-50 transition-colors text-[11px]"
          >
            {generating ? "Generating Artifact..." : "⚡ Generate New Artifact (Grok AI)"}
          </button>
        </div>

        <BusinessModelWorkspace
          key={artifact.id}
          initialModelDescription={artifact.artifact_payload.model_description}
          flawedAssumption={artifact.artifact_payload.flawed_assumption || ""}
          onChange={setSubmittedFix}
        />
      </div>
    </WorkspaceShell>
  );
}

export default function BusinessModelWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Business Model Workspace...</div>}>
      <BusinessModelWorkspaceInner />
    </Suspense>
  );
}
