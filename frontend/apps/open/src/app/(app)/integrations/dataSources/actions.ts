"use server";

import { createDataSource, deleteDataSource } from "@/lib/api";
import { DataSourceSpec } from "@vulkanlabs/client-open";
import { handleActionError } from "@/lib/error-handler";

export async function createDataSourceAction(data: DataSourceSpec) {
    try {
        const response = await createDataSource(data);
        return response;
    } catch (error) {
        handleActionError("create", "data source", error);
    }
}

export async function deleteDataSourceAction(dataSourceId: string): Promise<void> {
    try {
        await deleteDataSource(dataSourceId);
    } catch (error) {
        handleActionError("delete", "data source", error);
    }
}
