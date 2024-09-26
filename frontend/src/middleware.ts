import { stackServerApp } from "@/stack";
import { NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
    const user = await stackServerApp.getUser();
    if (!user) {
        return NextResponse.redirect(new URL("/handler/sign-in", request.url));
    }
    return NextResponse.next();
}

export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - handler (StackHandler routes)
         * - login (login page)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico, sitemap.xml, robots.txt (metadata files)
         */
        "/((?!handler|login|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
    ],
};
