import { DataSource } from "@vulkanlabs/base/workflow";
import { apiResult } from "@/lib/api-response";

export async function GET(request: Request) {
    try {
        const serverUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        if (!serverUrl) {
            return apiResult.error("Server URL is not configured", 500);
        }

        const url = `${serverUrl}/data-sources`;

        const response = await fetch(url, {
            cache: "no-store",
        });

        if (!response.ok) {
            return apiResult.error(
                `Failed to fetch data sources: ${response.statusText}`,
                response.status,
            );
        }

        if (response.status === 204) {
            return apiResult.success([]);
        }

        const data: DataSource[] = await response.json();
        return apiResult.success(data);
    } catch (error) {
        console.error("Error fetching data sources:", error);
        return apiResult.error(
            error instanceof Error ? error.message : "Failed to fetch data sources",
            500,
        );
    }
}
