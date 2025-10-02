import { PolicyVersion } from "@vulkanlabs/client-open";
import { apiResult } from "@/lib/api-response";

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const policyId = searchParams.get("policy_id") || null;
        const includeArchived = searchParams.get("include_archived") === "true";

        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) {
            return apiResult.error("Server URL is not configured", 500);
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
            return apiResult.error(
                `Failed to fetch policy versions: ${response.statusText}`,
                response.status,
            );
        }

        if (response.status === 204) {
            return apiResult.success([]);
        }

        const data: PolicyVersion[] = await response.json();
        return apiResult.success(data);
    } catch (error) {
        console.error("Error fetching policy versions:", error);
        return apiResult.error(
            error instanceof Error ? error.message : "Failed to fetch policy versions",
            500,
        );
    }
}
