"use server";

import { type Component, type ComponentBase } from "@vulkanlabs/client-open";
import { componentsApi, withErrorHandling } from "./client";

/**
 * Fetch all components with optional archived filter
 * @param {boolean} [includeArchived=false] - Include archived/deleted components in results
 * @returns {Promise<Component[]>} List of component objects
 */
export async function fetchComponents(includeArchived: boolean = false): Promise<Component[]> {
    return withErrorHandling(
        componentsApi.listComponents({ includeArchived: includeArchived }),
        `fetch components`,
    );
}

/**
 * Get a single component by name
 * @param {string} componentId - The component identifier (usually encoded for URL safety)
 * @returns {Promise<Component>} Component details with config, versions, metadata
 */
export async function fetchComponent(componentId: string): Promise<Component> {
    return withErrorHandling(
        componentsApi.getComponent({ componentId: componentId }),
        `fetch component ${componentId}`,
    );
}

/**
 * Create a new component
 * @param {ComponentBase} data - Component definition with name, description, config
 * @returns {Promise<Component>} Newly created component with generated metadata
 */
export async function createComponent(data: ComponentBase): Promise<Component> {
    return withErrorHandling(
        componentsApi.createComponent({ componentBase: data }),
        `create component`,
    );
}

export async function updateComponent(
    componentId: string,
    data: ComponentBase | any, // Allow any to handle backend/frontend type inconsistencies
): Promise<Component> {
    return withErrorHandling(
        componentsApi.updateComponent({ componentId, componentBase: data }),
        `update component ${componentId}`,
    );
}

/**
 * Delete/archive a component
 * @param {string} componentId - Component identifier to delete
 * @returns {Promise<void>} Success or throws error
 *
 * This is likely a soft delete - component gets archived, not permanently removed
 */
export async function deleteComponent(componentId: string): Promise<void> {
    return withErrorHandling(
        componentsApi.deleteComponent({ componentId }),
        `delete component ${componentId}`,
    );
}
