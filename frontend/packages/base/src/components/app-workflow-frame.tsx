"use client";

import React, { useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { z } from "zod";

import {
    WorkflowFrame,
    WorkflowApiProvider,
    WorkflowDataProvider,
    createWorkflowApiClient,
    type Workflow,
} from "../workflow";

/**
 * Configuration schema for runtime validation with enhanced performance
 */
const AppWorkflowFrameConfigSchema = z.object({
    /** Whether policyId is required for multi-tenant environments */
    requirePolicyId: z.boolean().optional().default(false),
    /** Whether to pass projectId to WorkflowFrame component */
    passProjectIdToFrame: z.boolean().optional().default(false),
});

/**
 * Default empty configuration object - frozen for performance
 */
const DEFAULT_CONFIG: AppWorkflowFrameConfig = Object.freeze({});

/**
 * Global scope configuration - no policy isolation required
 */
export const GLOBAL_SCOPE_CONFIG: AppWorkflowFrameConfig = Object.freeze({
    requirePolicyId: false,
    passProjectIdToFrame: true,
});

/**
 * Project scope configuration - requires policy isolation
 */
export const PROJECT_SCOPE_CONFIG: AppWorkflowFrameConfig = Object.freeze({
    requirePolicyId: true,
    passProjectIdToFrame: true,
});

/**
 * Configuration for app-specific workflow frame behavior
 */
export interface AppWorkflowFrameConfig {
    /** Whether policyId is required for multi-tenant environments */
    requirePolicyId?: boolean;
    /** Whether to pass projectId to WorkflowFrame component */
    passProjectIdToFrame?: boolean;
}

/**
 * Base props that both apps use
 */
interface BaseAppWorkflowFrameProps {
    workflowData: Workflow;
    onNodeClick?: (e: React.MouseEvent, node: any) => void;
    onPaneClick?: (e: React.MouseEvent) => void;
    config?: AppWorkflowFrameConfig;
}

/**
 * Global scope workflow frame props (no policy isolation)
 */
export interface GlobalScopeWorkflowFrameProps extends BaseAppWorkflowFrameProps {
    projectId?: string;
}

/**
 * Project scope workflow frame props (requires policy isolation)
 */
export interface ProjectScopeWorkflowFrameProps extends BaseAppWorkflowFrameProps {
    projectId: string;
    policyId: string;
}

/**
 * Union type for all possible props
 */
export type AppWorkflowFrameProps = GlobalScopeWorkflowFrameProps | ProjectScopeWorkflowFrameProps;

/**
 * Type guard to check if props include policyId (project scope mode)
 */
function isProjectScopeProps(
    props: AppWorkflowFrameProps,
): props is ProjectScopeWorkflowFrameProps {
    return "policyId" in props && typeof props.policyId === "string";
}

/**
 * Configurable application workflow frame that adapts to different deployment modes.
 *
 * Performance optimized with React.memo to prevent unnecessary re-renders when props haven't changed.
 * Uses custom comparison function to handle union types and optional props correctly.
 *
 * @param props - Union type supporting both global and project scope configurations
 * @returns Memoized React component with workflow frame functionality
 */
export const AppWorkflowFrame = React.memo<AppWorkflowFrameProps>(
    function AppWorkflowFrame(props: AppWorkflowFrameProps) {
        const {
            workflowData,
            onNodeClick = () => {},
            onPaneClick = () => {},
            config = DEFAULT_CONFIG,
        } = props;

        // Validate and parse configuration (memoized for performance)
        const validatedConfig = useMemo(() => AppWorkflowFrameConfigSchema.parse(config), [config]);
        const { requirePolicyId, passProjectIdToFrame } = validatedConfig;

        const router = useRouter();

        // Memoize API client creation (expensive operation)
        const apiClient = useMemo(() => createWorkflowApiClient(), []);

        // Memoize event handlers to prevent child re-renders
        const handleRefresh = useCallback(() => router.refresh(), [router]);
        const handleToast = useCallback(
            (message: string, options?: any) => toast(message, options),
            [],
        );

        // Extract projectId and policyId based on props type
        const projectId = "projectId" in props ? props.projectId : undefined;
        const policyId = isProjectScopeProps(props) ? props.policyId : undefined;

        // Validate required fields based on config
        if (requirePolicyId && !policyId) {
            throw new Error("AppWorkflowFrame: policyId is required when requirePolicyId is true");
        }

        return (
            <WorkflowApiProvider client={apiClient} config={{}}>
                <WorkflowDataProvider
                    autoFetch={true}
                    includeArchived={false}
                    projectId={projectId}
                    policyId={policyId || undefined}
                >
                    <WorkflowFrame
                        workflow={workflowData}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        toast={handleToast}
                        onRefresh={handleRefresh}
                        projectId={passProjectIdToFrame && projectId ? projectId : undefined}
                    />
                </WorkflowDataProvider>
            </WorkflowApiProvider>
        );
    },
    (prevProps, nextProps) => {
        // Custom comparison for performance optimization
        return (
            prevProps.workflowData === nextProps.workflowData &&
            prevProps.config === nextProps.config &&
            prevProps.onNodeClick === nextProps.onNodeClick &&
            prevProps.onPaneClick === nextProps.onPaneClick &&
            ("projectId" in prevProps ? prevProps.projectId : undefined) ===
                ("projectId" in nextProps ? nextProps.projectId : undefined) &&
            (isProjectScopeProps(prevProps) ? prevProps.policyId : undefined) ===
                (isProjectScopeProps(nextProps) ? nextProps.policyId : undefined)
        );
    },
);
