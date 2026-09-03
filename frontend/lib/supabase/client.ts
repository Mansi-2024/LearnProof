import { createBrowserClient } from "@supabase/ssr";

/**
 * Browser-side Supabase client.
 *
 * Uses only the public NEXT_PUBLIC_ env vars — safe to call from any
 * Client Component.  Creates a new client instance per call; React
 * useMemo or a module-level singleton can be used to share one instance.
 *
 * Usage (Client Component):
 *   const supabase = createSupabaseBrowserClient()
 *   const { data, error } = await supabase.auth.getSession()
 */
export function createSupabaseBrowserClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
