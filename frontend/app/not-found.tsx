import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col items-center justify-center p-6 text-center">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 font-mono text-2xl font-bold mb-6">
        404
      </div>
      <h1 className="text-3xl font-bold tracking-tight mb-2">Page Not Found</h1>
      <p className="text-neutral-400 max-w-md mb-8 text-sm leading-relaxed">
        The workspace or resource you are looking for does not exist or has been relocated.
      </p>
      <Link
        href="/dashboard"
        className="px-5 py-2.5 bg-neutral-100 text-neutral-900 text-sm font-semibold rounded-lg hover:bg-white transition-all shadow-sm"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}
