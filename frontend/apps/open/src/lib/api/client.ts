import { createApiConfig, withErrorHandling } from "@vulkanlabs/base/src/lib/api/api-utils";

// Configure API clients with shared configuration
export const apiConfig = createApiConfig({
    baseUrl: process.env.NEXT_PUBLIC_VULKAN_SERVER_URL!,
    headers: {
        "Content-Type": "application/json",
    },
});

export { withErrorHandling };

// Re-export common types
export type { DateRange } from "./types";
