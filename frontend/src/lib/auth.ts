import { CurrentUser } from "@stackframe/stack";

export type AuthHeaders = Awaited<ReturnType<typeof getAuthHeaders>>;

export async function getAuthHeaders(user: CurrentUser) {
    const stackAuthJson = await user.getAuthJson();
    return {
        "x-stack-access-token": stackAuthJson.accessToken,
        "x-stack-refresh-token": stackAuthJson.refreshToken,
    };
}
