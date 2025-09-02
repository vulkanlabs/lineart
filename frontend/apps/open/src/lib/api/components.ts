import { ComponentsApi, type Component, type ComponentUpdate } from "@vulkanlabs/client-open";
import { apiConfig, withErrorHandling } from "./client";

const componentsApi = new ComponentsApi(apiConfig);

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
 * @param {string} componentName - The component identifier (usually encoded for URL safety)
 * @returns {Promise<Component>} Component details with config, versions, metadata
 */
export async function fetchComponent(componentName: string): Promise<Component> {
    return withErrorHandling(
        componentsApi.getComponent({ componentName: componentName }),
        `fetch component ${componentName}`,
    );
}

/**
 * Create a new component
 * @param {ComponentUpdate} data - Component definition with name, description, config
 * @returns {Promise<Component>} Newly created component with generated metadata
 */
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

/**
 * Delete/archive a component
 * @param {string} componentName - Component identifier to delete
 * @returns {Promise<void>} Success or throws error
 *
 * This is likely a soft delete - component gets archived, not permanently removed
 */
export async function deleteComponent(componentName: string): Promise<void> {
    return withErrorHandling(
        componentsApi.deleteComponent({ componentName }),
        `delete component ${componentName}`,
    );
}
