"use server";

import { type Component, type ComponentUpdate } from "@vulkanlabs/client-open";
import { componentsApi, withErrorHandling } from "./client";

export async function fetchComponents(includeArchived: boolean = false): Promise<Component[]> {
    return withErrorHandling(
        componentsApi.listComponents({ includeArchived: includeArchived }),
        `fetch components`,
    );
}

export async function fetchComponent(componentName: string): Promise<Component> {
    return withErrorHandling(
        componentsApi.getComponent({ componentName: componentName }),
        `fetch component ${componentName}`,
    );
}

export async function createComponent(data: ComponentUpdate): Promise<Component> {
    return withErrorHandling(
        componentsApi.createComponent({ componentUpdate: data }),
        `create component`,
    );
}

export async function updateComponent(
    componentName: string,
    data: ComponentUpdate,
): Promise<Component> {
    return withErrorHandling(
        componentsApi.updateComponent({ componentName, componentUpdate: data }),
        `update component ${componentName}`,
    );
}

export async function deleteComponent(componentName: string): Promise<void> {
    return withErrorHandling(
        componentsApi.deleteComponent({ componentName }),
        `delete component ${componentName}`,
    );
}
