import Link from "next/link";

const DOMAINS = [
  {
    slug: "code",
    name: "Code",
    description: "Debug recursion bugs, off-by-one errors, and syntax flaws with Monaco Editor and live test assertions.",
    badge: "Monaco + Live Eval",
    color: "border-blue-300 hover:border-blue-500 bg-blue-50/30",
  },
  {
    slug: "physics",
    name: "Physics",
    description: "Diagnose inverted gravity, trajectory errors, and unit mismatches with real-time 60fps Canvas simulations.",
    badge: "Canvas Simulation",
    color: "border-emerald-300 hover:border-emerald-500 bg-emerald-50/30",
  },
  {
    slug: "story",
    name: "Story",
    description: "Scan narrative paradoxes, timeline contradictions, and character memory leaks with sentence inspection tools.",
    badge: "Narrative Revision",
    color: "border-purple-300 hover:border-purple-500 bg-purple-50/30",
  },
  {
    slug: "business-model",
    name: "Business Model",
    description: "Diagnose negative unit contribution margin, misaligned CAC/LTV, and fatal venture assumptions with Lean Canvas.",
    badge: "Lean Canvas + LTV:CAC",
    color: "border-amber-300 hover:border-amber-500 bg-amber-50/30",
  },
  {
    slug: "chemistry",
    name: "Chemistry",
    description: "Repair unbalanced reactions, stoichiometry flaws, and mass conservation violations with live atom counters.",
    badge: "Stoichiometry Balancer",
    color: "border-rose-300 hover:border-rose-500 bg-rose-50/30",
  },
];

export default function WorkspaceHubPage() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 px-6 py-12">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link href="/dashboard" className="text-sm font-medium text-gray-500 hover:text-black">
              ← Dashboard
            </Link>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Repair Workspaces</h1>
          <p className="text-gray-600 mt-1">
            Choose a multi-domain repair workspace to diagnose broken artifacts and submit explanations to the AI Judge.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {DOMAINS.map((d) => (
            <Link
              key={d.slug}
              href={`/workspace/${d.slug}`}
              className={`p-6 rounded-xl border transition-all duration-200 shadow-sm hover:shadow-md ${d.color} group block`}
            >
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-bold group-hover:text-black">{d.name}</h2>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-white border text-gray-700">
                  {d.badge}
                </span>
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{d.description}</p>
              <div className="mt-4 text-xs font-semibold text-gray-900 group-hover:underline flex items-center gap-1">
                Enter {d.name} Workspace →
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
