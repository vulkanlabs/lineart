"use server";

import { createDataSource, deleteDataSource } from "@/lib/api";
import { DataSourceSpec } from "@vulkanlabs/client-open";

export async function createDataSourceAction(data: DataSourceSpec) {
    try {
        const response = await createDataSource(data);
        return response;
    } catch (error) {
        console.error("Error creating data source:", error);
        throw new Error("Failed to create data source");
    }
}

export async function deleteDataSourceAction(dataSourceId: string): Promise<void> {
    try {
        await deleteDataSource(dataSourceId);
    } catch (error) {
        console.error("Error deleting data source:", error);
        throw new Error("Failed to delete data source");
    }
}
