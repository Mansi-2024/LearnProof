import { NextResponse, type NextRequest } from "next/server";
import { createSupabaseServerClient } from "@/lib/supabase/server";

/**
 * OAuth callback route handler.
 *
 * Supabase redirects here after the user authenticates with Google (or any
 * other OAuth provider).  This handler:
 * 1. Exchanges the one-time ``code`` query param for a session.
 * 2. Redirects the user to their intended destination (``next`` param) or
 *    the dashboard.
 *
 * In the Supabase dashboard, set the redirect URL to:
 *   http://localhost:3000/api/auth/callback   (development)
 *   https://yourdomain.com/api/auth/callback  (production)
 */
export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = requestUrl.searchParams.get("next") ?? "/dashboard";
  const origin = requestUrl.origin;

  if (code) {
    const supabase = createSupabaseServerClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // If anything went wrong, redirect to an error page or login.
  return NextResponse.redirect(`${origin}/login?error=oauth_callback_failed`);
}
