// Global App - Shared API patterns (inline approach)
import { Component } from "@vulkanlabs/client-open";
import { apiResult } from "@/lib/api-response";

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const includeArchived = searchParams.get("include_archived") === "true";

        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) return apiResult.error("Server URL is not configured");

        const params = new URLSearchParams({ include_archived: includeArchived.toString() });
        const url = `${serverUrl}/components?${params.toString()}`;

        const response = await fetch(url, { cache: "no-store" });

        if (!response.ok) {
            return apiResult.error(
                `Failed to fetch components: ${response.statusText}`,
                response.status,
            );
        }

        if (response.status === 204) return apiResult.success([]);

        const data: Component[] = await response.json();
        return apiResult.success(data);
    } catch (error) {
        return apiResult.error(
            error instanceof Error ? error.message : "Failed to fetch components",
        );
    }
}
