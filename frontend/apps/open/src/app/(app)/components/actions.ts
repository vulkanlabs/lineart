"use server";

import { createComponent, deleteComponent } from "@/lib/api";
import { type ComponentBase } from "@vulkanlabs/client-open";
import { handleActionError } from "@/lib/error-handler";

export async function createComponentAction(data: ComponentBase): Promise<any> {
    try {
        const response = await createComponent(data);
        return response;
    } catch (error) {
        handleActionError("create", "component", error);
    }
}

export async function deleteComponentAction(componentName: string): Promise<void> {
    try {
        await deleteComponent(componentName);
    } catch (error) {
        handleActionError("delete", "component", error);
    }
}
