import { apiResult } from "@/lib/api-response";
import { fetchDataSources } from "@/lib/api/data-sources";

export async function GET(request: Request) {
    try {
        // Parse query parameters
        const { searchParams } = new URL(request.url);
        const status = searchParams.get("status") || undefined;
        const includeArchived = searchParams.get("include_archived") === "true";

        // Use local client method to fetch data sources
        const data = await fetchDataSources(includeArchived, status);
        return apiResult.success(data);
    } catch (error) {
        console.error("Error fetching data sources:", error);
        return apiResult.error(
            error instanceof Error ? error.message : "Failed to fetch data sources",
            500,
        );
    }
}
