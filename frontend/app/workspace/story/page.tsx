"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import WorkspaceShell from "@/components/workspace/WorkspaceShell";
import StoryWorkspace from "@/components/workspace/StoryWorkspace";
import { ArtifactData, generateLiveArtifact } from "@/lib/api";

const SAMPLE_STORY_ARTIFACT: ArtifactData = {
  id: "story-artifact-demo-1",
  domain_slug: "story",
  target_concept: "spatial-and-physical-continuity",
  artifact_payload: {
    inconsistency_type: "spatial_continuity_error",
    text: `Elena carefully melted the heavy iron key in the blazing forge until it was nothing more than glowing liquid slag. An hour later, as the guards approached the corridor, Elena reached into her pocket, pulled out that same iron key, and unlocked the dungeon gate to escape.`,
  },
  root_cause: "Physical impossibility: The key was permanently destroyed in the forge, making it impossible for Elena to retrieve it from her pocket intact an hour later.",
  expected_behavior: "Elena should use an alternative escape method (e.g. lockpicking, a hidden duplicate key, or bribing the guard).",
  actual_behavior: "The narrative resurrects a destroyed object with zero explanation, breaking reader immersion and physical continuity.",
};

function StoryWorkspaceInner() {
  const searchParams = useSearchParams();
  const targetConcept = searchParams.get("concept") || "spatial-and-physical-continuity";

  const [artifact, setArtifact] = useState<ArtifactData>(SAMPLE_STORY_ARTIFACT);
  const [submittedFix, setSubmittedFix] = useState<Record<string, any>>({
    text: artifact.artifact_payload.text,
    inconsistency_type: artifact.artifact_payload.inconsistency_type,
  });
  const [generating, setGenerating] = useState(false);

  async function loadArtifact(concept: string) {
    setGenerating(true);
    const live = await generateLiveArtifact("story", concept, 0.5);
    if (live && live.artifact_payload && live.artifact_payload.text) {
      setArtifact(live);
      setSubmittedFix({
        text: live.artifact_payload.text,
        inconsistency_type: live.artifact_payload.inconsistency_type || "narrative_inconsistency",
      });
    }
    setGenerating(false);
  }

  useEffect(() => {
    loadArtifact(targetConcept);
  }, [targetConcept]);

  return (
    <WorkspaceShell
      domain="story"
      domainDisplayName="Story"
      targetConcept={targetConcept.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      artifact={artifact}
      submittedFix={submittedFix}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-purple-50/60 p-3 rounded-lg border border-purple-100 text-xs">
          <span className="text-purple-900 font-medium">
            Active Concept: <b className="font-bold">{artifact.target_concept || targetConcept}</b>
          </span>
          <button
            onClick={() => loadArtifact(targetConcept)}
            disabled={generating}
            className="px-3 py-1 bg-purple-600 text-white font-semibold rounded hover:bg-purple-700 disabled:opacity-50 transition-colors text-[11px]"
          >
            {generating ? "Generating Artifact..." : "⚡ Generate New Artifact (Grok AI)"}
          </button>
        </div>

        <StoryWorkspace
          key={artifact.id}
          initialText={artifact.artifact_payload.text}
          inconsistencyType={artifact.artifact_payload.inconsistency_type || "narrative_inconsistency"}
          onChange={setSubmittedFix}
        />
      </div>
    </WorkspaceShell>
  );
}

export default function StoryWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Story Workspace...</div>}>
      <StoryWorkspaceInner />
    </Suspense>
  );
}
