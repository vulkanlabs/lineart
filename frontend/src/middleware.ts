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
    // TODO: Add more paths to the matcher
    // Match all paths except /, stack path, and static paths
    matcher: ["/policies/:path*", "/components/:path*"],
};
