"use server";

import { createDataSource } from "@/lib/api";
import { DataSourceSpec } from "@vulkan-server/DataSourceSpec";

export async function createDataSourceAction(data: DataSourceSpec) {
    try {
        const response = await createDataSource(data);
        return response;
    } catch (error) {
        console.error("Error creating data source:", error);
        throw new Error("Failed to create data source");
    }
}
