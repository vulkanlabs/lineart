import { 
    SharedResponseUtils,
    parseWorkflowRequest, 
    parseQueryParams, 
    getProjectIdFromParams,
    validateWorkflowSaveRequest,
    validateServerUrl,
    type SharedApiConfig 
} from "./shared-response-utils";

// Configuration interface for workflow save handlers
export interface WorkflowSaveHandlerConfig {
    // App-specific API functions
    updatePolicyVersion?: (policyVersionId: string, data: any, projectId?: string) => Promise<any>;
    updateComponent?: (componentId: string, data: any) => Promise<any>;
    
    // Direct server communication
    serverUrl?: string;
    
    // App-specific requirements
    requiresProjectId: boolean;
    
    // Response utilities
    responseUtils: SharedResponseUtils;
}

// Configuration interface for list handlers  
export interface ListHandlerConfig {
    // App-specific API functions
    listComponents?: (projectId?: string, includeArchived?: boolean) => Promise<any>;
    listPolicyVersions?: (policyId: string, projectId?: string) => Promise<any>;
    
    // Direct server communication
    serverUrl?: string;
    
    // App-specific requirements
    requiresProjectId: boolean;
    
    // Response utilities
    responseUtils: SharedResponseUtils;
}

export class SharedWorkflowHandlers {
    private config: WorkflowSaveHandlerConfig;

    constructor(config: WorkflowSaveHandlerConfig) {
        this.config = config;
    }

    async handleWorkflowSave(request: Request): Promise<Response> {
        try {
            const { workflow, spec, uiMetadata } = await parseWorkflowRequest(request);
            const searchParams = parseQueryParams(request);
            const projectId = getProjectIdFromParams(searchParams);

            // Validate request
            const validationError = validateWorkflowSaveRequest(
                workflow, 
                spec, 
                this.config.requiresProjectId, 
                projectId
            );
            if (validationError) {
                return this.config.responseUtils.validationError(validationError);
            }

            // Handle different workflow types
            if (typeof workflow === "object" && "policy_version_id" in workflow) {
                return this.savePolicyVersion(workflow, spec, uiMetadata, projectId);
            } else if (typeof workflow === "object" && "component_id" in workflow) {
                return this.saveComponent(workflow, spec, uiMetadata);
            } else {
                return this.config.responseUtils.validationError("Invalid workflow type");
            }
        } catch (error) {
            return this.config.responseUtils.serverError(
                error instanceof Error ? error.message : "Unknown error",
                error
            );
        }
    }

    private async savePolicyVersion(
        policyVersion: any,
        spec: any,
        uiMetadata: any,
        projectId?: string | null
    ): Promise<Response> {
        try {
            if (!policyVersion.policy_version_id) {
                return this.config.responseUtils.validationError("Policy version ID is required");
            }

            const updateData = {
                alias: policyVersion.alias || null,
                spec: spec,
                requirements: [],
                ui_metadata: uiMetadata,
            };

            let data: any;

            if (this.config.updatePolicyVersion) {
                // Use API wrapper with project context
                data = await this.config.updatePolicyVersion(
                    policyVersion.policy_version_id,
                    updateData,
                    projectId || undefined
                );
            } else if (this.config.serverUrl) {
                // Direct server communication
                const serverError = validateServerUrl(this.config.serverUrl);
                if (serverError) {
                    return this.config.responseUtils.serverError(serverError);
                }

                const response = await fetch(
                    `${this.config.serverUrl}/policy-versions/${policyVersion.policy_version_id}`,
                    {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(updateData),
                        cache: "no-store",
                    }
                );

                if (!response.ok) {
                    const error = await response.json();
                    if (response.status !== 500) {
                        return this.config.responseUtils.error(
                            `Server responded with status: ${response.status}: ${error.detail}`,
                            response.status
                        );
                    } else {
                        return this.config.responseUtils.serverError("Internal server error", error);
                    }
                }

                data = await response.json();
            } else {
                return this.config.responseUtils.serverError("No update method configured");
            }

            return this.config.responseUtils.success(data);
        } catch (error) {
            return this.config.responseUtils.serverError(
                error instanceof Error ? error.message : "Failed to save policy version",
                error
            );
        }
    }

    private async saveComponent(
        component: any,
        spec: any,
        uiMetadata: any
    ): Promise<Response> {
        try {
            if (!component.component_id) {
                return this.config.responseUtils.validationError("Component ID is required");
            }

            const updateData = {
                requirements: component.workflow?.requirements || [],
                name: component.name,
                description: component.description || null,
                icon: component.icon || null,
                spec,
                variables: component.workflow?.variables || [],
                ui_metadata: uiMetadata,
            };

            if (!this.config.updateComponent) {
                return this.config.responseUtils.serverError("Component updates not supported");
            }

            const data = await this.config.updateComponent(component.component_id, updateData);
            return this.config.responseUtils.success(data);
        } catch (error) {
            return this.config.responseUtils.serverError(
                error instanceof Error ? error.message : "Failed to save component",
                error
            );
        }
    }
}

export class SharedListHandlers {
    private config: ListHandlerConfig;

    constructor(config: ListHandlerConfig) {
        this.config = config;
    }

    async handleComponentsList(request: Request): Promise<Response> {
        try {
            const searchParams = parseQueryParams(request);
            const includeArchived = searchParams.get("include_archived") === "true";
            const projectId = getProjectIdFromParams(searchParams);

            if (this.config.requiresProjectId && !projectId) {
                return this.config.responseUtils.validationError("Project ID is required");
            }

            let data: any;

            if (this.config.listComponents) {
                // Use API wrapper
                data = await this.config.listComponents(projectId || undefined, includeArchived);
            } else if (this.config.serverUrl) {
                // Direct server communication
                const serverError = validateServerUrl(this.config.serverUrl);
                if (serverError) {
                    return this.config.responseUtils.serverError(serverError);
                }

                const params = new URLSearchParams({
                    include_archived: includeArchived.toString(),
                });

                const url = `${this.config.serverUrl}/components?${params.toString()}`;
                const response = await fetch(url, {
                    cache: "no-store",
                });

                if (!response.ok) {
                    return this.config.responseUtils.error(
                        `Failed to fetch components: ${response.statusText}`,
                        response.status
                    );
                }

                if (response.status === 204) {
                    data = [];
                } else {
                    data = await response.json();
                }
            } else {
                return this.config.responseUtils.serverError("No list method configured");
            }

            return this.config.responseUtils.success(data);
        } catch (error) {
            return this.config.responseUtils.serverError(
                error instanceof Error ? error.message : "Failed to fetch components",
                error
            );
        }
    }
}