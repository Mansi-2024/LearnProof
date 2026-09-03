"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import WorkspaceShell from "@/components/workspace/WorkspaceShell";
import PhysicsWorkspace from "@/components/workspace/PhysicsWorkspace";
import { ArtifactData, generateLiveArtifact } from "@/lib/api";

const SAMPLE_PHYSICS_ARTIFACT: ArtifactData = {
  id: "physics-artifact-demo-1",
  domain_slug: "physics",
  target_concept: "projectile-gravitational-acceleration",
  artifact_payload: {
    sim_type: "projectile_motion",
    constants: {
      gravity: "-9.8 m/s^2", // Bug: Inverted gravity causing projectile to fly upward
      initial_velocity: "25 m/s",
      launch_angle: "45 deg",
    },
    correct_constants: {
      gravity: "9.8 m/s^2",
      initial_velocity: "25 m/s",
      launch_angle: "45 deg",
    },
  },
  root_cause: "Inverted gravity sign in projectile motion kinematic formula y(t) = v0*sin(θ)*t - 0.5*g*t^2 causes upward unbounded acceleration instead of parabolic downward arc.",
  expected_behavior: "The projectile should follow a downward concave parabola and land at distance x ≈ 63.7 meters.",
  actual_behavior: "The projectile shoots straight up into outer space because gravity is negative.",
};

function PhysicsWorkspaceInner() {
  const searchParams = useSearchParams();
  const targetConcept = searchParams.get("concept") || "projectile-gravitational-acceleration";

  const [artifact, setArtifact] = useState<ArtifactData>(SAMPLE_PHYSICS_ARTIFACT);
  const [submittedFix, setSubmittedFix] = useState<Record<string, any>>({
    constants: artifact.artifact_payload.constants,
    correct_constants: artifact.artifact_payload.correct_constants,
  });
  const [generating, setGenerating] = useState(false);

  async function loadArtifact(concept: string) {
    setGenerating(true);
    const live = await generateLiveArtifact("physics", concept, 0.5);
    if (live && live.artifact_payload && live.artifact_payload.constants) {
      setArtifact(live);
      setSubmittedFix({
        constants: live.artifact_payload.constants,
        correct_constants: live.artifact_payload.correct_constants || live.artifact_payload.constants,
      });
    }
    setGenerating(false);
  }

  useEffect(() => {
    loadArtifact(targetConcept);
  }, [targetConcept]);

  return (
    <WorkspaceShell
      domain="physics"
      domainDisplayName="Physics"
      targetConcept={targetConcept.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
      artifact={artifact}
      submittedFix={submittedFix}
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between bg-emerald-50/60 p-3 rounded-lg border border-emerald-100 text-xs">
          <span className="text-emerald-900 font-medium">
            Active Concept: <b className="font-bold">{artifact.target_concept || targetConcept}</b>
          </span>
          <button
            onClick={() => loadArtifact(targetConcept)}
            disabled={generating}
            className="px-3 py-1 bg-emerald-600 text-white font-semibold rounded hover:bg-emerald-700 disabled:opacity-50 transition-colors text-[11px]"
          >
            {generating ? "Generating Artifact..." : "⚡ Generate New Artifact (Grok AI)"}
          </button>
        </div>

        <PhysicsWorkspace
          key={artifact.id}
          simType={artifact.artifact_payload.sim_type || "projectile_motion"}
          initialConstants={artifact.artifact_payload.constants || {}}
          onChange={setSubmittedFix}
        />
      </div>
    </WorkspaceShell>
  );
}

export default function PhysicsWorkspacePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading Physics Workspace...</div>}>
      <PhysicsWorkspaceInner />
    </Suspense>
  );
}
