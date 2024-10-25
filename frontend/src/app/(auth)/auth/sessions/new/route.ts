import { stackServerApp } from "@/stack";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
    const body = await request.json();
    if (!body || !body.email || !body.password) {
        return new Response(null, {
            status: 401,
            statusText: "Unauthorized",
        });
    }

    const signInResult = await stackServerApp.signInWithCredential({
        email: body.email,
        password: body.password,
        noRedirect: true,
    });

    if (!signInResult || signInResult.status === "error") {
        return new Response(null, {
            status: 401,
            statusText: "Unauthorized",
        });
    }

    const user = await stackServerApp.getUser();
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
