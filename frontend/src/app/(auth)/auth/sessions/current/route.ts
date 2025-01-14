import { stackServerApp } from "@/stack";
import { headers } from "next/headers";
import { NextResponse } from "next/server";

export async function GET() {
    const headersList = await headers();
    const refreshToken = headersList.get("x-stack-refresh-token");
    const accessToken = headersList.get("x-stack-access-token");

    const user = await stackServerApp.getUser({
        or: "return-null",
        tokenStore: { accessToken: accessToken, refreshToken: refreshToken },
    });
    if (!user) {
        return new Response(null, {
            status: 401,
            statusText: "Unauthorized",
        });
    }

    const creds = await user.getAuthJson();
    return NextResponse.json(
        {
            ...creds,
            user_id: user.id,
        },
        { status: 200 },
    );
}
