"use client";

import React, { useState, useEffect, useRef } from "react";

interface PhysicsWorkspaceProps {
  initialConstants: Record<string, any>;
  correctConstants?: Record<string, any>;
  simType?: string;
  onChange: (fix: { constants: Record<string, any> }) => void;
}

/**
 * [PLACEHOLDER-STYLED]: Physics simulation canvas and parameter tuner controls.
 * Interaction logic (live 60fps HTML5 Canvas physics render, interactive parameter sliders, trajectory recalculation) is fully functional.
 */
export default function PhysicsWorkspace({
  initialConstants = {},
  correctConstants = {},
  simType = "projectile_motion",
  onChange,
}: PhysicsWorkspaceProps) {
  // Parse numeric values from string constants
  const [gravity, setGravity] = useState<number>(() => {
    const raw = initialConstants.gravity || "-9.8";
    const parsed = parseFloat(String(raw).replace(/[^0-9.-]/g, ""));
    return isNaN(parsed) ? 9.8 : parsed;
  });

  const [velocity, setVelocity] = useState<number>(() => {
    const raw = initialConstants.velocity || initialConstants.initial_velocity || "25";
    const parsed = parseFloat(String(raw).replace(/[^0-9.-]/g, ""));
    return isNaN(parsed) ? 25 : parsed;
  });

  const [angle, setAngle] = useState<number>(45);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Sync with parent submitted_fix
  useEffect(() => {
    onChange({
      constants: {
        gravity: `${gravity} m/s^2`,
        velocity: `${velocity} m/s`,
        angle: `${angle} deg`,
      },
    });
  }, [gravity, velocity, angle]);

  // Live Canvas Simulation Animation Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let t = 0;

    const rad = (angle * Math.PI) / 180;
    const vx = velocity * Math.cos(rad);
    const vy = velocity * Math.sin(rad);

    function render() {
      if (!ctx || !canvas) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Ground plane
      ctx.strokeStyle = "#94a3b8";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(20, 220);
      ctx.lineTo(canvas.width - 20, 220);
      ctx.stroke();

      // Target marker (expected landing zone ~ 63m scaled)
      ctx.fillStyle = "#22c55e";
      ctx.fillRect(450, 215, 40, 6);
      ctx.fillStyle = "#15803d";
      ctx.font = "10px sans-serif";
      ctx.fillText("Target Zone", 445, 235);

      // Origin cannon/launcher
      ctx.fillStyle = "#334155";
      ctx.beginPath();
      ctx.arc(40, 220, 10, 0, Math.PI * 2);
      ctx.fill();

      // Draw Trajectory curve
      ctx.beginPath();
      ctx.strokeStyle = gravity <= 0 ? "#ef4444" : "#3b82f6";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);

      for (let simT = 0; simT <= 10; simT += 0.05) {
        const x = 40 + vx * simT * 8;
        // If gravity is negative (broken), it accelerates upward
        const y = 220 - (vy * simT - 0.5 * gravity * simT * simT) * 4;
        if (simT === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, Math.max(10, Math.min(240, y)));
        if (y > 220 && simT > 0.1) break;
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Animated projectile particle
      const curX = 40 + vx * t * 8;
      const curY = 220 - (vy * t - 0.5 * gravity * t * t) * 4;

      ctx.fillStyle = gravity <= 0 ? "#dc2626" : "#2563eb";
      ctx.beginPath();
      ctx.arc(curX, Math.max(10, Math.min(220, curY)), 6, 0, Math.PI * 2);
      ctx.fill();

      t += 0.03;
      if (curY > 220 || curX > canvas.width - 20) {
        t = 0; // Loop animation
      }

      animId = requestAnimationFrame(render);
    }

    render();

    return () => cancelAnimationFrame(animId);
  }, [gravity, velocity, angle]);

  const isGravityCorrect = gravity > 0 && Math.abs(gravity - 9.8) <= 1.0;

  return (
    <div className="space-y-6">
      {/* Simulation Viewport */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Live Physics Simulation ({simType})
          </span>
          <span className={`text-xs px-2 py-0.5 rounded font-bold ${
            isGravityCorrect ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
          }`}>
            {isGravityCorrect ? "✓ Stable Trajectory" : "⚠️ Broken Physical Vector"}
          </span>
        </div>
        <div className="bg-slate-900 rounded-lg p-2 border border-slate-700 shadow-inner flex justify-center">
          <canvas ref={canvasRef} width={580} height={250} className="w-full max-w-xl h-auto" />
        </div>
      </div>

      {/* Interactive Sliders & Parameter Tuner */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-4">
        <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
          Physical Constants & Parameters
        </h4>

        {/* Gravity Slider */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <label htmlFor="gravity" className="font-medium text-gray-700">
              Gravitational Acceleration (g)
            </label>
            <span className={`font-mono font-bold ${gravity > 0 ? "text-blue-600" : "text-red-600"}`}>
              {gravity.toFixed(1)} m/s²
            </span>
          </div>
          <input
            id="gravity"
            type="range"
            min="-20"
            max="30"
            step="0.1"
            value={gravity}
            onChange={(e) => setGravity(parseFloat(e.target.value))}
            className="w-full accent-black cursor-pointer"
          />
          <div className="flex justify-between text-[10px] text-gray-400 font-mono">
            <span>-20.0 m/s² (Upward)</span>
            <span>0.0 m/s² (Zero-G)</span>
            <span>+9.8 m/s² (Earth)</span>
            <span>+30.0 m/s² (Heavy)</span>
          </div>
        </div>

        {/* Initial Velocity */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <label htmlFor="velocity" className="font-medium text-gray-700">
              Launch Velocity (v₀)
            </label>
            <span className="font-mono font-bold text-gray-900">{velocity} m/s</span>
          </div>
          <input
            id="velocity"
            type="range"
            min="5"
            max="50"
            step="1"
            value={velocity}
            onChange={(e) => setVelocity(parseFloat(e.target.value))}
            className="w-full accent-black cursor-pointer"
          />
        </div>

        {/* Launch Angle */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <label htmlFor="angle" className="font-medium text-gray-700">
              Launch Angle (θ)
            </label>
            <span className="font-mono font-bold text-gray-900">{angle}°</span>
          </div>
          <input
            id="angle"
            type="range"
            min="5"
            max="85"
            step="1"
            value={angle}
            onChange={(e) => setAngle(parseFloat(e.target.value))}
            className="w-full accent-black cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}
