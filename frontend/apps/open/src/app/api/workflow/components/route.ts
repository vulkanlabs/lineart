import { Component } from "@vulkanlabs/client-open";

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const includeArchived = searchParams.get("include_archived") === "true";

        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) {
            return Response.json({ error: "Server URL is not configured" }, { status: 500 });
        }

        // Build query parameters matching the original server action
        const params = new URLSearchParams({
            include_archived: includeArchived.toString(),
        });

        const url = `${serverUrl}/components?${params.toString()}`;

        const response = await fetch(url, {
            cache: "no-store",
        });

        if (!response.ok) {
            return Response.json(
                { error: `Failed to fetch components: ${response.statusText}` },
                { status: response.status },
            );
        }

        if (response.status === 204) {
            return Response.json([]);
        }

        const data: Component[] = await response.json();
        return Response.json(data);
    } catch (error) {
        console.error("Error fetching components:", error);
        return Response.json(
            { error: error instanceof Error ? error.message : "Failed to fetch components" },
            { status: 500 },
        );
    }
}
