"use client";

import React, { useState, useEffect } from "react";

interface ChemistryWorkspaceProps {
  initialEquation: string;
  initialReactants?: string[];
  initialProducts?: string[];
  onChange: (fix: { equation: string; reactants: string[]; products: string[] }) => void;
}

// Helper to count element occurrences in chemical formula string
function parseElementCounts(termString: string): Record<string, number> {
  const counts: Record<string, number> = {};
  if (!termString) return counts;

  const parts = termString.split("+").map((p) => p.trim());
  for (const part of parts) {
    // Match leading stoichiometric coefficient e.g. "2 H2O" or "3CO2"
    const coefMatch = part.match(/^(\d+)\s*(.*)$/);
    const coef = coefMatch ? parseInt(coefMatch[1], 10) : 1;
    const formula = coefMatch ? coefMatch[2] : part;

    // Match elements and subscripts e.g. "H2", "O", "C6", "Fe3"
    const elemRegex = /([A-Z][a-z]*)(\d*)/g;
    let match: RegExpExecArray | null;
    while ((match = elemRegex.exec(formula)) !== null) {
      const elem = match[1];
      const count = match[2] ? parseInt(match[2], 10) : 1;
      counts[elem] = (counts[elem] || 0) + count * coef;
    }
  }
  return counts;
}

/**
 * [PLACEHOLDER-STYLED]: Chemistry reaction builder and stoichiometric atom balance dashboard.
 * Interaction logic (equation editing, live parser calculating left vs right atom counts, mass conservation validation) is fully functional.
 */
export default function ChemistryWorkspace({
  initialEquation,
  initialReactants = ["H2", "O2"],
  initialProducts = ["H2O"],
  onChange,
}: ChemistryWorkspaceProps) {
  const [equation, setEquation] = useState(initialEquation);

  // Split into left and right sides of equation
  const sides = equation.split(/->|→|-->/).map((s) => s.trim());
  const leftStr = sides[0] || "";
  const rightStr = sides[1] || "";

  const leftCounts = parseElementCounts(leftStr);
  const rightCounts = parseElementCounts(rightStr);

  const allElements = Array.from(
    new Set([...Object.keys(leftCounts), ...Object.keys(rightCounts)])
  ).sort();

  const isBalanced =
    allElements.length > 0 &&
    allElements.every((elem) => (leftCounts[elem] || 0) === (rightCounts[elem] || 0));

  useEffect(() => {
    const reactants = leftStr.split("+").map((s) => s.trim()).filter(Boolean);
    const products = rightStr.split("+").map((s) => s.trim()).filter(Boolean);
    onChange({ equation, reactants, products });
  }, [equation]);

  return (
    <div className="space-y-6">
      {/* Header status */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Chemical Reaction Balancer
        </span>
        <span
          className={`px-2.5 py-1 text-xs font-bold rounded ${
            isBalanced ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
          }`}
        >
          {isBalanced ? "✓ Conservation of Mass Satisfied" : "⚠️ Unbalanced Stoichiometry"}
        </span>
      </div>

      {/* Interactive Equation Input */}
      <div className="space-y-2">
        <label htmlFor="chem-eq" className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
          Reaction Equation (Format: Reactants -&gt; Products)
        </label>
        <input
          id="chem-eq"
          type="text"
          value={equation}
          onChange={(e) => setEquation(e.target.value)}
          placeholder="e.g. 2 H2 + O2 -> 2 H2O"
          className="w-full text-base font-mono p-3.5 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-black focus:outline-none bg-white"
        />
        <p className="text-[11px] text-gray-400">
          Tip: Adjust coefficients and subscripts directly (e.g. change <code className="bg-gray-100 px-1">H2 + O2 -&gt; H2O</code> to <code className="bg-gray-100 px-1">2 H2 + O2 -&gt; 2 H2O</code>).
        </p>
      </div>

      {/* Live Atom Balancing Inspector Grid */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-3">
        <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
          Live Atom Count Comparison (Left vs Right)
        </h4>

        {allElements.length === 0 ? (
          <p className="text-xs text-gray-400">Type a reaction equation above to inspect atom counts.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {allElements.map((elem) => {
              const lCount = leftCounts[elem] || 0;
              const rCount = rightCounts[elem] || 0;
              const elemBalanced = lCount === rCount;

              return (
                <div
                  key={elem}
                  className={`p-3 rounded-lg border text-center transition-colors ${
                    elemBalanced
                      ? "bg-green-50/80 border-green-200 text-green-950"
                      : "bg-red-50/80 border-red-200 text-red-950"
                  }`}
                >
                  <span className="font-bold text-lg font-mono block">{elem}</span>
                  <div className="text-xs font-mono mt-1 space-x-1">
                    <span>Reactants: <b>{lCount}</b></span>
                    <span>|</span>
                    <span>Products: <b>{rCount}</b></span>
                  </div>
                  <span className={`text-[10px] font-bold block mt-1 ${
                    elemBalanced ? "text-green-700" : "text-red-700"
                  }`}>
                    {elemBalanced ? "✓ Balanced" : "✗ Imbalanced"}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
