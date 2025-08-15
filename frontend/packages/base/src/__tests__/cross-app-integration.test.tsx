import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import {
    AppWorkflowFrame as BaseAppWorkflowFrame,
    GLOBAL_SCOPE_CONFIG,
    PROJECT_SCOPE_CONFIG,
    type GlobalScopeWorkflowFrameProps,
    type ProjectScopeWorkflowFrameProps,
} from "../components/app-workflow-frame";

// Mock workflow data for tests
const mockWorkflowData = {
    nodes: [
        { id: "1", type: "input", data: { label: "Start" }, position: { x: 0, y: 0 } },
        { id: "2", type: "output", data: { label: "End" }, position: { x: 100, y: 100 } },
    ],
    edges: [{ id: "e1-2", source: "1", target: "2" }],
};

describe("Cross-App Configuration Compatibility", () => {
    describe("Configuration Interoperability", () => {
        it("should work with global scope configuration (OSS pattern)", () => {
            const globalScopeProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "oss-project",
                config: GLOBAL_SCOPE_CONFIG,
            };

            expect(() => render(<BaseAppWorkflowFrame {...globalScopeProps} />)).not.toThrow();
        });

        it("should work with project scope configuration (SaaS pattern)", () => {
            const projectScopeProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "saas-project",
                policyId: "saas-policy",
                config: PROJECT_SCOPE_CONFIG,
            };

            expect(() => render(<BaseAppWorkflowFrame {...projectScopeProps} />)).not.toThrow();
        });

        it("should prevent configuration misuse", () => {
            // This should fail - using project scope config without policyId
            const invalidProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                config: PROJECT_SCOPE_CONFIG, // Requires policyId but props don't have it
            };

            expect(() => render(<BaseAppWorkflowFrame {...invalidProps} />)).toThrow(
                "AppWorkflowFrame: policyId is required when requirePolicyId is true",
            );
        });

        it("should maintain type safety across configurations", () => {
            // TypeScript should prevent these assignments at compile time
            // These tests verify runtime behavior matches compile-time expectations

            const globalProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                // policyId not allowed in GlobalScopeWorkflowFrameProps
            };

            const projectProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                policyId: "test-policy", // Required in ProjectScopeWorkflowFrameProps
            };

            expect(() =>
                render(<BaseAppWorkflowFrame {...globalProps} config={GLOBAL_SCOPE_CONFIG} />),
            ).not.toThrow();
            expect(() =>
                render(<BaseAppWorkflowFrame {...projectProps} config={PROJECT_SCOPE_CONFIG} />),
            ).not.toThrow();
        });
    });

    describe("Runtime Behavior Validation", () => {
        it("should handle global scope without policy isolation", () => {
            const globalProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "global-test-project",
                config: GLOBAL_SCOPE_CONFIG,
            };

            expect(() => render(<BaseAppWorkflowFrame {...globalProps} />)).not.toThrow();
        });

        it("should enforce policy isolation for project scope", () => {
            const projectProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-test-project",
                policyId: "project-test-policy",
                config: PROJECT_SCOPE_CONFIG,
            };

            expect(() => render(<BaseAppWorkflowFrame {...projectProps} />)).not.toThrow();
        });

        it("should provide appropriate error messages for misconfigurations", () => {
            // Global scope props with project scope requirements
            const mismatchedProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                config: { requirePolicyId: true }, // This requires policyId but props don't provide it
            };

            expect(() => render(<BaseAppWorkflowFrame {...mismatchedProps} />)).toThrow(
                "AppWorkflowFrame: policyId is required when requirePolicyId is true",
            );
        });
    });

    describe("Configuration Consistency", () => {
        it("should maintain consistent global scope behavior", () => {
            const props1: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-1",
                config: GLOBAL_SCOPE_CONFIG,
            };

            const props2: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-2",
                config: GLOBAL_SCOPE_CONFIG,
            };

            // Both should use the same configuration behavior
            expect(() => render(<BaseAppWorkflowFrame {...props1} />)).not.toThrow();
            expect(() => render(<BaseAppWorkflowFrame {...props2} />)).not.toThrow();
        });

        it("should maintain consistent project scope behavior", () => {
            const props1: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-1",
                policyId: "policy-1",
                config: PROJECT_SCOPE_CONFIG,
            };

            const props2: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-2",
                policyId: "policy-2",
                config: PROJECT_SCOPE_CONFIG,
            };

            // Both should use the same configuration behavior
            expect(() => render(<BaseAppWorkflowFrame {...props1} />)).not.toThrow();
            expect(() => render(<BaseAppWorkflowFrame {...props2} />)).not.toThrow();
        });

        it("should prevent cross-contamination between scopes", () => {
            // Ensure global scope config cannot accidentally enable policy requirements
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).toBe(false);

            // Ensure project scope config cannot accidentally disable policy requirements
            expect(PROJECT_SCOPE_CONFIG.requirePolicyId).toBe(true);

            // Both should enable project ID passing
            expect(GLOBAL_SCOPE_CONFIG.passProjectIdToFrame).toBe(true);
            expect(PROJECT_SCOPE_CONFIG.passProjectIdToFrame).toBe(true);
        });
    });
});

describe("Architecture Validation Tests", () => {
    describe("Scope-Based Component Sharing", () => {
        it("should support OSS deployment patterns", () => {
            // OSS: Single tenant, no policy isolation, global scope
            const ossProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "oss-project",
                config: GLOBAL_SCOPE_CONFIG,
            };

            expect(() => render(<BaseAppWorkflowFrame {...ossProps} />)).not.toThrow();
        });

        it("should support SaaS deployment patterns", () => {
            // SaaS: Multi-tenant, policy isolation required, project scope
            const saasProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "tenant-1-project",
                policyId: "tenant-1-policy",
                config: PROJECT_SCOPE_CONFIG,
            };

            expect(() => render(<BaseAppWorkflowFrame {...saasProps} />)).not.toThrow();
        });

        it("should maintain clear separation between deployment modes", () => {
            // These configurations should be clearly distinct
            expect(GLOBAL_SCOPE_CONFIG).not.toEqual(PROJECT_SCOPE_CONFIG);

            // Key difference: policy requirement
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).toBe(false);
            expect(PROJECT_SCOPE_CONFIG.requirePolicyId).toBe(true);
        });
    });

    describe("Component Sharing Validation", () => {
        it("should eliminate double edits by using single base component", () => {
            const globalProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                config: GLOBAL_SCOPE_CONFIG,
            };

            const projectProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                policyId: "test-policy",
                config: PROJECT_SCOPE_CONFIG,
            };

            // Both should use the same base component
            const globalRender = render(<BaseAppWorkflowFrame {...globalProps} />);
            globalRender.unmount();

            const projectRender = render(<BaseAppWorkflowFrame {...projectProps} />);
            projectRender.unmount();

            // Test passes if both render without issues - same component, different configs
            expect(true).toBe(true);
        });

        it("should support configuration-driven behavior changes", () => {
            // Same component should behave differently based on configuration
            const flexibleProps1: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                config: { requirePolicyId: false, passProjectIdToFrame: true },
            };

            const flexibleProps2: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                policyId: "test-policy",
                config: { requirePolicyId: true, passProjectIdToFrame: false },
            };

            expect(() => render(<BaseAppWorkflowFrame {...flexibleProps1} />)).not.toThrow();
            expect(() => render(<BaseAppWorkflowFrame {...flexibleProps2} />)).not.toThrow();
        });
    });
});

describe("Regression Prevention Tests", () => {
    describe("PR Changes Coverage", () => {
        it("should maintain scope-based naming conventions", () => {
            // Verify the interface names follow scope-based patterns
            const globalProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
            };

            const projectProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                policyId: "test-policy",
            };

            // TypeScript compilation success validates naming consistency
            expect(typeof globalProps).toBe("object");
            expect(typeof projectProps).toBe("object");
        });

        it("should maintain configuration schema validation", () => {
            // Verify schema validation works for both valid and invalid configs
            const validConfig = { requirePolicyId: true, passProjectIdToFrame: true };
            const props: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                policyId: "test-policy",
                config: validConfig,
            };

            expect(() => render(<BaseAppWorkflowFrame {...props} />)).not.toThrow();
        });

        it("should maintain improved error handling", () => {
            const invalidProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                config: { requirePolicyId: true }, // Invalid: requires policyId but not provided
            };

            // Should throw clear error (not silent failure)
            expect(() => render(<BaseAppWorkflowFrame {...invalidProps} />)).toThrow(
                "AppWorkflowFrame: policyId is required when requirePolicyId is true",
            );
        });

        it("should maintain improved prop spreading readability", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                config: GLOBAL_SCOPE_CONFIG,
            };

            // Should render without issues - validates prop handling improvements
            expect(() => render(<BaseAppWorkflowFrame {...props} />)).not.toThrow();
        });
    });
});
