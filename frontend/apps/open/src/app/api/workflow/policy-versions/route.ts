import { PolicyVersion } from "@vulkanlabs/client-open";

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const policyId = searchParams.get("policy_id") || null;
        const includeArchived = searchParams.get("include_archived") === "true";

        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) {
            return Response.json({ error: "Server URL is not configured" }, { status: 500 });
        }

        // Build query parameters matching the original server action
        const params = new URLSearchParams({
            include_archived: includeArchived.toString(),
        });

        if (policyId) {
            params.append("policy_id", policyId);
        }

        const url = `${serverUrl}/policy-versions?${params.toString()}`;

        const response = await fetch(url, {
            cache: "no-store",
        });

        if (!response.ok) {
            return Response.json(
                { error: `Failed to fetch policy versions: ${response.statusText}` },
                { status: response.status },
            );
        }

        const data: PolicyVersion[] = await response.json();
        return Response.json(data);
    } catch (error) {
        console.error("Error fetching policy versions:", error);
        return Response.json(
            { error: error instanceof Error ? error.message : "Failed to fetch policy versions" },
            { status: 500 },
        );
    }
}
