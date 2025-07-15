"use server";

import { createComponent } from "@/lib/api";
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
