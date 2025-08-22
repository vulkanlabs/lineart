// Global App - Shared API patterns (inline approach)
import { Component } from "@vulkanlabs/client-open";

// Shared response pattern
const apiResponse = {
    success: (data: any) => Response.json(data),
    error: (message: string, status: number = 500) => {
        console.error(`API Error: ${message}`);
        return Response.json({ error: message }, { status });
    },
};

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const includeArchived = searchParams.get("include_archived") === "true";

        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) return apiResponse.error("Server URL is not configured");

        const params = new URLSearchParams({ include_archived: includeArchived.toString() });
        const url = `${serverUrl}/components?${params.toString()}`;

        const response = await fetch(url, { cache: "no-store" });

        if (!response.ok) {
            return apiResponse.error(
                `Failed to fetch components: ${response.statusText}`,
                response.status,
            );
        }

        if (response.status === 204) return apiResponse.success([]);

        const data: Component[] = await response.json();
        return apiResponse.success(data);
    } catch (error) {
        return apiResponse.error(
            error instanceof Error ? error.message : "Failed to fetch components",
        );
    }
}
