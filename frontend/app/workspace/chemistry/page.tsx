"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import WorkspaceShell from "@/components/workspace/WorkspaceShell";
import ChemistryWorkspace from "@/components/workspace/ChemistryWorkspace";
import { ArtifactData, generateLiveArtifact } from "@/lib/api";

const SAMPLE_CHEM_ARTIFACT: ArtifactData = {
  id: "chem-artifact-demo-1",
  domain_slug: "chemistry",
  target_concept: "stoichiometric-mass-conservation",
  artifact_payload: {
    equation: "C3H8 + O2 -> CO2 + H2O",
    reactants: ["C3H8", "O2"],
    products: ["CO2", "H2O"],
  },
  root_cause: "Unbalanced stoichiometry: The combustion of propane (C3H8 + O2 -> CO2 + H2O) violates conservation of mass across carbon, hydrogen, and oxygen atoms.",
  expected_behavior: "Correct stoichiometric balancing: C3H8 + 5 O2 -> 3 CO2 + 4 H2O, conserving 3 Carbon, 8 Hydrogen, and 10 Oxygen atoms on both sides.",
  actual_behavior: "Carbon atoms disappear (3 on left vs 1 on right), Hydrogen disappears (8 on left vs 2 on right), and Oxygen appears out of nowhere (2 on left vs 3 on right).",
};

function ChemistryWorkspaceInner() {
  const searchParams = useSearchParams();
  const targetConcept = searchParams.get("concept") || "stoichiometric-mass-conservation";

  const [artifact, setArtifact] = useState<ArtifactData>(SAMPLE_CHEM_ARTIFACT);
  const [submittedFix, setSubmittedFix] = useState<Record<string, any>>({
    equation: artifact.artifact_payload.equation,
    reactants: artifact.artifact_payload.reactants,
    products: artifact.artifact_payload.products,
  });
  const [generating, setGenerating] = useState(false);

  async function loadArtifact(concept: string) {
    setGenerating(true);
    const live = await generateLiveArtifact("chemistry", concept, 0.5);
    if (live && live.artifact_payload && live.artifact_payload.equation) {
      setArtifact(live);
      setSubmittedFix({
        equation: live.artifact_payload.equation,
        reactants: live.artifact_payload.reactants || [],
        products: live.artifact_payload.products || [],
      });
    }
    setGenerating(false);
  }

  useEffect(() => {
    loadArtifact(targetConcept);
  }, [targetConcept]);

  return (
    <WorkspaceShell
      domain="chemistry"
      domainDisplayName="Chemistry"
      targetConcept={targetConcept.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      artifact={artifact}
      submittedFix={submittedFix}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-rose-50/60 p-3 rounded-lg border border-rose-100 text-xs">
          <span className="text-rose-900 font-medium">
            Active Concept: <b className="font-bold">{artifact.target_concept || targetConcept}</b>
          </span>
          <button
            onClick={() => loadArtifact(targetConcept)}
            disabled={generating}
            className="px-3 py-1 bg-rose-600 text-white font-semibold rounded hover:bg-rose-700 disabled:opacity-50 transition-colors text-[11px]"
          >
            {generating ? "Generating Artifact..." : "⚡ Generate New Artifact (Grok AI)"}
          </button>
        </div>

        <ChemistryWorkspace
          key={artifact.id}
          initialEquation={artifact.artifact_payload.equation}
          initialReactants={artifact.artifact_payload.reactants || []}
          initialProducts={artifact.artifact_payload.products || []}
          onChange={setSubmittedFix}
        />
      </div>
    </WorkspaceShell>
  );
}

export default function ChemistryWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Chemistry Workspace...</div>}>
      <ChemistryWorkspaceInner />
    </Suspense>
  );
}
