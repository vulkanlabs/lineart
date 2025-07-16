import { DataSource } from "@vulkanlabs/base/workflow";

export async function GET(request: Request) {
    try {
        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) {
            return Response.json({ error: "Server URL is not configured" }, { status: 500 });
        }

        const url = `${serverUrl}/data-sources`;

        const response = await fetch(url, {
            cache: "no-store",
        });

        if (!response.ok) {
            return Response.json(
                { error: `Failed to fetch data sources: ${response.statusText}` },
                { status: response.status },
            );
        }

        const data: DataSource[] = await response.json();
        return Response.json(data);
    } catch (error) {
        console.error("Error fetching data sources:", error);
        return Response.json(
            { error: error instanceof Error ? error.message : "Failed to fetch data sources" },
            { status: 500 },
        );
    }
}
