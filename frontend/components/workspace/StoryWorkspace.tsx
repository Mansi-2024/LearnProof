"use client";

import React, { useState, useEffect } from "react";

interface StoryWorkspaceProps {
  initialText: string;
  inconsistencyType?: string;
  onChange: (fix: { text: string; inconsistency_type?: string }) => void;
}

/**
 * [PLACEHOLDER-STYLED]: Story reader and narrative revision editor.
 * Interaction logic (text highlighting, live story rewriting, character and word counter) is fully functional.
 */
export default function StoryWorkspace({
  initialText,
  inconsistencyType = "narrative_inconsistency",
  onChange,
}: StoryWorkspaceProps) {
  const [revisedText, setRevisedText] = useState(initialText);
  const [selectedHighlight, setSelectedHighlight] = useState<string | null>(null);

  useEffect(() => {
    onChange({ text: revisedText, inconsistency_type: inconsistencyType });
  }, [revisedText]);

  // Split into sentences for easy inspection
  const sentences = initialText.match(/[^.!?]+[.!?]+/g) || [initialText];

  return (
    <div className="space-y-6">
      {/* Flaw Category Tag */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Narrative Flaw Category
        </span>
        <span className="px-2.5 py-1 bg-purple-100 text-purple-800 text-xs font-bold rounded">
          {inconsistencyType.replace(/_/g, " ")}
        </span>
      </div>

      {/* Interactive Sentence Inspector */}
      <div className="bg-amber-50/50 p-4 rounded-lg border border-amber-200 space-y-2">
        <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
          Original Excerpt (Click sentences to highlight suspects):
        </h4>
        <div className="text-sm leading-relaxed text-gray-800 font-serif space-x-1">
          {sentences.map((sent, idx) => {
            const isSelected = selectedHighlight === sent;
            return (
              <span
                key={idx}
                onClick={() => setSelectedHighlight(isSelected ? null : sent)}
                className={`cursor-pointer px-1 py-0.5 rounded transition-colors ${
                  isSelected
                    ? "bg-amber-300 font-medium text-black underline decoration-amber-600 decoration-2"
                    : "hover:bg-amber-200/60"
                }`}
                title="Click to highlight"
              >
                {sent.trim()}{" "}
              </span>
            );
          })}
        </div>
      </div>

      {/* Story Revision Editor */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor="story-editor" className="text-xs font-bold text-gray-700 uppercase tracking-wider">
            Rewritten Story Excerpt (Fix the contradiction):
          </label>
          <span className="text-xs text-gray-400">
            {revisedText.split(/\s+/).filter(Boolean).length} words
          </span>
        </div>
        <textarea
          id="story-editor"
          rows={6}
          value={revisedText}
          onChange={(e) => setRevisedText(e.target.value)}
          className="w-full font-serif text-sm leading-relaxed p-4 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-black focus:outline-none"
          placeholder="Rewrite the flawed passage so the story maintains continuous logic, spatial consistency, and realistic motivation..."
        />
      </div>
    </div>
  );
}
