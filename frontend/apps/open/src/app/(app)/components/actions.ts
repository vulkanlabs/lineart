"use server";

import { createComponent, deleteComponent } from "@/lib/api";
import { type ComponentBase } from "@vulkanlabs/client-open";

export async function createComponentAction(data: ComponentBase): Promise<any> {
    try {
        const response = await createComponent(data);
        return response;
    } catch (error) {
        console.error("Error creating component:", error);
        throw new Error("Failed to create component");
    }
}

export async function deleteComponentAction(componentId: string): Promise<void> {
    try {
        await deleteComponent(componentId);
    } catch (error) {
        console.error("Error deleting component:", error);
        throw new Error("Failed to delete component");
    }
}
