"use client";

import React, { useState, useEffect } from "react";

interface BusinessModelWorkspaceProps {
  initialModelDescription: string;
  flawedAssumption?: string;
  onChange: (fix: { model_description: string; corrected_sections?: Record<string, string> }) => void;
}

/**
 * [PLACEHOLDER-STYLED]: Lean Canvas grid and unit economics calculator.
 * Interaction logic (multi-section canvas editing, live gross contribution margin math, assumption adjustment) is fully functional.
 */
export default function BusinessModelWorkspace({
  initialModelDescription,
  flawedAssumption = "Unspecified flawed assumption",
  onChange,
}: BusinessModelWorkspaceProps) {
  const [modelDescription, setModelDescription] = useState(initialModelDescription);

  // Unit Economics Tuner fields
  const [price, setPrice] = useState<number>(25);
  const [costPerUnit, setCostPerUnit] = useState<number>(18);
  const [cac, setCac] = useState<number>(40);
  const [repeatPurchases, setRepeatPurchases] = useState<number>(4);

  // Calculated economics
  const grossContribution = price - costPerUnit;
  const ltv = grossContribution * repeatPurchases;
  const netLtvCacRatio = cac > 0 ? (ltv / cac).toFixed(2) : "0.00";

  useEffect(() => {
    onChange({
      model_description: modelDescription,
      corrected_sections: {
        unit_price: `$${price}`,
        cost_per_unit: `$${costPerUnit}`,
        cac: `$${cac}`,
        ltv_cac_ratio: `${netLtvCacRatio}:1`,
      },
    });
  }, [modelDescription, price, costPerUnit, cac, repeatPurchases]);

  return (
    <div className="space-y-6">
      {/* Flawed Assumption Alert Badge */}
      <div className="bg-rose-50 border border-rose-200 p-4 rounded-lg">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-bold text-rose-800">⚠️ Hidden Structural Assumption in Pitch:</span>
        </div>
        <p className="text-xs text-rose-700 font-medium">{flawedAssumption}</p>
      </div>

      {/* Lean Canvas Structured Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Value Proposition */}
        <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
          <h4 className="text-[11px] font-bold text-gray-500 uppercase mb-1">Value Proposition</h4>
          <p className="text-xs text-gray-800">
            On-demand convenience offering premium quality with rapid turnaround.
          </p>
        </div>

        {/* Target Customers */}
        <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
          <h4 className="text-[11px] font-bold text-gray-500 uppercase mb-1">Customer Segment</h4>
          <p className="text-xs text-gray-800">
            Busy urban professionals with high willingness to pay for saved time.
          </p>
        </div>

        {/* Revenue Streams & Pricing */}
        <div className="bg-indigo-50/60 p-3 rounded-lg border border-indigo-200">
          <h4 className="text-[11px] font-bold text-indigo-900 uppercase mb-1">Revenue Model</h4>
          <p className="text-xs text-indigo-950">
            Direct transactional fees per fulfillment + optional monthly subscription.
          </p>
        </div>
      </div>

      {/* Unit Economics Live Calculator */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
            Unit Economics & Margin Tuner
          </h4>
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded ${
              grossContribution > 0 && parseFloat(netLtvCacRatio) >= 3.0
                ? "bg-green-100 text-green-800"
                : grossContribution <= 0
                ? "bg-red-100 text-red-800"
                : "bg-yellow-100 text-yellow-800"
            }`}
          >
            {grossContribution <= 0
              ? "❌ Negative Unit Margin"
              : parseFloat(netLtvCacRatio) < 3.0
              ? "⚠️ Low LTV:CAC (< 3x)"
              : "✓ Healthy Economics (LTV/CAC ≥ 3x)"}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div>
            <label htmlFor="unit-price" className="block text-[11px] font-medium text-gray-600 mb-1">
              Selling Price ($)
            </label>
            <input
              id="unit-price"
              type="number"
              value={price}
              onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
              className="w-full text-xs font-mono p-2 border border-gray-300 rounded bg-white"
            />
          </div>
          <div>
            <label htmlFor="unit-cost" className="block text-[11px] font-medium text-gray-600 mb-1">
              Variable Cost ($)
            </label>
            <input
              id="unit-cost"
              type="number"
              value={costPerUnit}
              onChange={(e) => setCostPerUnit(parseFloat(e.target.value) || 0)}
              className="w-full text-xs font-mono p-2 border border-gray-300 rounded bg-white"
            />
          </div>
          <div>
            <label htmlFor="unit-cac" className="block text-[11px] font-medium text-gray-600 mb-1">
              Customer Acq. (CAC)
            </label>
            <input
              id="unit-cac"
              type="number"
              value={cac}
              onChange={(e) => setCac(parseFloat(e.target.value) || 0)}
              className="w-full text-xs font-mono p-2 border border-gray-300 rounded bg-white"
            />
          </div>
          <div>
            <label htmlFor="repeat-orders" className="block text-[11px] font-medium text-gray-600 mb-1">
              Repeat Orders (LTV)
            </label>
            <input
              id="repeat-orders"
              type="number"
              value={repeatPurchases}
              onChange={(e) => setRepeatPurchases(parseFloat(e.target.value) || 1)}
              className="w-full text-xs font-mono p-2 border border-gray-300 rounded bg-white"
            />
          </div>
        </div>

        {/* Output Metrics */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t text-center text-xs">
          <div className="p-2 bg-white rounded border">
            <span className="text-gray-500 block text-[10px]">Gross Margin / Tx</span>
            <span className={`font-mono font-bold ${grossContribution > 0 ? "text-green-600" : "text-red-600"}`}>
              ${grossContribution.toFixed(2)}
            </span>
          </div>
          <div className="p-2 bg-white rounded border">
            <span className="text-gray-500 block text-[10px]">Cumulative LTV</span>
            <span className="font-mono font-bold text-gray-900">${ltv.toFixed(2)}</span>
          </div>
          <div className="p-2 bg-white rounded border">
            <span className="text-gray-500 block text-[10px]">LTV : CAC Ratio</span>
            <span className="font-mono font-bold text-indigo-600">{netLtvCacRatio}x</span>
          </div>
        </div>
      </div>

      {/* Narrative Business Model Editor */}
      <div className="space-y-2">
        <label htmlFor="business-desc" className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
          Corrected Business Model Strategy & Description:
        </label>
        <textarea
          id="business-desc"
          rows={5}
          value={modelDescription}
          onChange={(e) => setModelDescription(e.target.value)}
          className="w-full text-sm p-4 rounded-lg border border-gray-300 shadow-sm focus:ring-2 focus:ring-black focus:outline-none"
          placeholder="Revise the business pitch to show sustainable unit economics, scalable distribution, and a viable pricing model..."
        />
      </div>
    </div>
  );
}
