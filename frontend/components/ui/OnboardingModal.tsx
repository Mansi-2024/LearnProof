"use client";

import React, { useState, useEffect } from "react";

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const STEPS = [
  {
    step: 1,
    badge: "The Paradigm",
    title: "Learn by Repairing Broken Artifacts",
    description:
      "Most learning tools test rote memorization. Repair tests deep diagnostic intuition across 5 domains: Code, Physics, Story, Business Model, and Chemistry.",
    illustration: "🛠️",
    details: [
      "Inspect realistic broken artifacts with intentional flaws",
      "Interactive domain sandboxes: Monaco Editor, Canvas physics, Lean Canvas & stoichiometry balancers",
      "Request progressive Socratic hints without spoiling the solution",
    ],
  },
  {
    step: 2,
    badge: "Dual-Score Engine",
    title: "Fix Correctness vs. Conceptual Understanding",
    description:
      "Every submission requires two things: your corrected artifact and an explanation of WHY it was broken.",
    illustration: "🧠",
    details: [
      "Fix Correctness (0-100%): Did your fix resolve the operational failure?",
      "Understanding Score (0-100%): Did you grasp the true root cause or just get lucky?",
      "AI Judge powered by Grok semantically compares your explanation against ground-truth principles",
    ],
  },
  {
    step: 3,
    badge: "Adaptive BKT",
    title: "Bayesian Mastery & Lucky Guess Detection",
    description:
      "The engine uses Bayesian Knowledge Tracing (BKT) to model your genuine knowledge state over time.",
    illustration: "📊",
    details: [
      "Weights understanding (70%) over raw fixes (30%) to prevent gaming the system",
      "Flags 'Lucky Guess' moments where the fix works but the explanation reveals a misconception",
      "Prioritizes your weakest concepts across all domains so practice is always high-impact",
    ],
  },
];

export default function OnboardingModal({ isOpen, onClose }: OnboardingModalProps) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // Escape key listener
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const stepData = STEPS[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 max-w-lg w-full overflow-hidden flex flex-col transform transition-all scale-100">
        {/* Header */}
        <div className="px-6 pt-6 pb-4 flex items-center justify-between border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-[10px] font-extrabold uppercase tracking-wider bg-black text-white rounded-full">
              {stepData.badge}
            </span>
            <span className="text-xs text-gray-400">
              Step {currentStep + 1} of {STEPS.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 text-sm font-bold w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-4">
          <div className="text-4xl text-center py-2">{stepData.illustration}</div>

          <div className="text-center space-y-1">
            <h3 className="text-xl font-extrabold text-gray-900">{stepData.title}</h3>
            <p className="text-xs text-gray-600 leading-relaxed max-w-sm mx-auto">
              {stepData.description}
            </p>
          </div>

          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200/80 space-y-2.5">
            {stepData.details.map((item, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                <span className="text-indigo-600 font-bold">✓</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Navigation */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            {STEPS.map((_, idx) => (
              <span
                key={idx}
                onClick={() => setCurrentStep(idx)}
                className={`w-2 h-2 rounded-full cursor-pointer transition-all ${
                  currentStep === idx ? "w-6 bg-black" : "bg-gray-300 hover:bg-gray-400"
                }`}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={() => setCurrentStep((prev) => prev - 1)}
                className="px-4 py-2 text-xs font-semibold text-gray-600 hover:text-black rounded-lg transition-colors"
              >
                Back
              </button>
            )}

            {currentStep < STEPS.length - 1 ? (
              <button
                onClick={() => setCurrentStep((prev) => prev + 1)}
                className="px-5 py-2 text-xs font-semibold bg-black text-white rounded-lg hover:bg-gray-800 transition-colors shadow-sm"
              >
                Next Step →
              </button>
            ) : (
              <button
                onClick={onClose}
                className="px-5 py-2 text-xs font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
              >
                Start Practicing →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
