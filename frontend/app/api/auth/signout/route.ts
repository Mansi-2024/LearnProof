import { createSupabaseServerClient } from "@/lib/supabase/server";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Sign-out Route Handler.
 *
 * Called by the POST form on the dashboard page.
 * Clears the Supabase session from cookies and redirects to /login.
 */
export async function POST(request: NextRequest) {
  const supabase = createSupabaseServerClient();
  await supabase.auth.signOut();
  const origin = new URL(request.url).origin;
  return NextResponse.redirect(`${origin}/login`);
}
