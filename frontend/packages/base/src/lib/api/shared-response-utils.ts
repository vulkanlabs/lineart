// Shared response utilities for consistent API responses across apps

export interface SharedApiResponse<T = any> {
    success: boolean;
    data: T | null;
    error: string | null;
}

export interface SharedApiConfig {
    // Response factory function - apps can provide NextResponse.json or Response.json
    responseFactory: (body: any, options?: { status?: number }) => Response;
    
    // Error logging function - apps can provide their own logger
    logError: (message: string, error?: any) => void;
}

export class SharedResponseUtils {
    private config: SharedApiConfig;

    constructor(config: SharedApiConfig) {
        this.config = config;
    }

    success<T>(data: T): Response {
        return this.config.responseFactory({
            success: true,
            data,
            error: null,
        });
    }

    error(message: string, status: number = 500, logDetails?: any): Response {
        this.config.logError(`API Error: ${message}`, logDetails);
        return this.config.responseFactory(
            {
                success: false,
                error: message,
                data: null,
            },
            { status }
        );
    }

    validationError(message: string): Response {
        return this.error(message, 400);
    }

    serverError(message: string = "Internal server error", details?: any): Response {
        return this.error(message, 500, details);
    }

    notFound(message: string = "Not found"): Response {
        return this.error(message, 404);
    }
}

// Shared request parsing utilities
export async function parseWorkflowRequest(request: Request): Promise<{
    workflow: any;
    spec: any;
    uiMetadata: { [key: string]: any };
}> {
    const body = await request.json();
    return {
        workflow: body.workflow,
        spec: body.spec,
        uiMetadata: body.uiMetadata,
    };
}

export function parseQueryParams(request: Request): URLSearchParams {
    const { searchParams } = new URL(request.url);
    return searchParams;
}

export function getProjectIdFromParams(searchParams: URLSearchParams): string | null {
    return searchParams.get("project_id");
}

// Shared validation functions
export function validateWorkflowSaveRequest(
    workflow: any,
    spec: any,
    projectIdRequired: boolean = false,
    projectId?: string | null
): string | null {
    if (!workflow) {
        return "Workflow is required";
    }

    if (!spec) {
        return "Workflow spec is required";
    }

    if (projectIdRequired && !projectId) {
        return "Project ID is required";
    }

    return null; // No validation errors
}

export function validateServerUrl(serverUrl?: string): string | null {
    if (!serverUrl) {
        return "Server URL is not configured";
    }
    return null;
}