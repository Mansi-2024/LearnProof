import { type NextRequest } from "next/server";
import { updateSession } from "@/lib/auth/middleware";

/**
 * Next.js middleware — runs on every matched request before rendering.
 *
 * Delegates to updateSession() which handles Supabase session refresh
 * and route protection.
 */
export async function middleware(request: NextRequest) {
  return await updateSession(request);
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - _next/static  (static files)
     * - _next/image   (image optimization)
     * - favicon.ico   (browser icon)
     * - public/        (public assets)
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
