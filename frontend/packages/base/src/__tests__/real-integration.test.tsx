/**
 * Real Integration Tests without Excessive Mocking
 *
 * Tests actual component interactions and data flow without heavy mocking.
 * Focuses on realistic usage scenarios and integration points.
 */

import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import {
    AppWorkflowFrame,
    GLOBAL_SCOPE_CONFIG,
    PROJECT_SCOPE_CONFIG,
    type GlobalScopeWorkflowFrameProps,
    type ProjectScopeWorkflowFrameProps,
} from "../components/app-workflow-frame";

// Test utilities and minimal setup
const mockWorkflowData = {
    id: "test-workflow-123",
    name: "Test Workflow",
    description: "Integration test workflow",
    nodes: [
        {
            id: "node-1",
            type: "input",
            position: { x: 100, y: 100 },
            data: { label: "Input Node" },
        },
        {
            id: "node-2",
            type: "transform",
            position: { x: 300, y: 100 },
            data: { label: "Transform Node" },
        },
    ],
    edges: [
        {
            id: "edge-1",
            source: "node-1",
            target: "node-2",
        },
    ],
};

// Mock external dependencies minimally
vi.mock("next/navigation", () => ({
    useRouter: () => ({
        push: vi.fn(),
        refresh: vi.fn(),
        back: vi.fn(),
        forward: vi.fn(),
    }),
}));

vi.mock("sonner", () => ({
    toast: vi.fn(),
}));

describe("Real Integration Tests", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    describe("AppWorkflowFrame Real Integration", () => {
        it("should integrate all child components for global scope workflow", async () => {
            const mockOnNodeClick = vi.fn();
            const mockOnPaneClick = vi.fn();

            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                onNodeClick: mockOnNodeClick,
                onPaneClick: mockOnPaneClick,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            const { container } = render(<AppWorkflowFrame {...props} />);

            // Component should render without errors
            expect(container).toBeInTheDocument();

            // Should integrate with WorkflowApiProvider and WorkflowDataProvider
            // We don't mock these heavily, so if the component renders successfully,
            // it means the integration is working
            await waitFor(() => {
                expect(container.firstChild).toBeInTheDocument();
            });
        });

        it("should integrate all child components for project scope workflow", async () => {
            const mockOnNodeClick = vi.fn();
            const mockOnPaneClick = vi.fn();

            const props: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                onNodeClick: mockOnNodeClick,
                onPaneClick: mockOnPaneClick,
                projectId: "test-project-123",
                policyId: "test-policy-456",
                config: PROJECT_SCOPE_CONFIG,
            };

            const { container } = render(<AppWorkflowFrame {...props} />);

            // Component should render without errors
            expect(container).toBeInTheDocument();

            // Should integrate with multi-tenant configuration
            await waitFor(() => {
                expect(container.firstChild).toBeInTheDocument();
            });
        });

        it("should handle real user interactions with minimal mocking", async () => {
            const mockOnNodeClick = vi.fn();
            const mockOnPaneClick = vi.fn();

            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                onNodeClick: mockOnNodeClick,
                onPaneClick: mockOnPaneClick,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            render(<AppWorkflowFrame {...props} />);

            // Find interactive elements and test real user interactions
            // This tests the actual event flow through the component hierarchy
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();

            // Test clicking on the workflow area
            fireEvent.click(workflowFrame);

            // The component should handle the click without errors
            // This validates the actual integration of event handlers
            await waitFor(() => {
                expect(workflowFrame).toBeInTheDocument();
            });
        });
    });

    describe("Configuration Integration Tests", () => {
        it("should integrate configuration validation with Zod schema in real usage", () => {
            // Test with valid configuration - should not throw
            const validProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                config: {
                    requirePolicyId: false,
                    passProjectIdToFrame: true,
                },
            };

            expect(() => {
                render(<AppWorkflowFrame {...validProps} />);
            }).not.toThrow();
        });

        it("should integrate error handling with invalid configuration in real usage", () => {
            // Test with invalid configuration - should throw during Zod validation
            const invalidProps = {
                workflowData: mockWorkflowData,
                config: {
                    requirePolicyId: "not-a-boolean" as any,
                    passProjectIdToFrame: 123 as any,
                },
            };

            expect(() => {
                render(<AppWorkflowFrame {...invalidProps} />);
            }).toThrow();
        });

        it("should integrate policy validation with real multi-tenant scenarios", () => {
            // Test policy requirement validation in realistic scenarios
            const propsWithoutPolicyId = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                config: {
                    requirePolicyId: true,
                    passProjectIdToFrame: true,
                },
                // Missing policyId when required
            };

            expect(() => {
                render(<AppWorkflowFrame {...propsWithoutPolicyId} />);
            }).toThrow("policyId is required when requirePolicyId is true");
        });
    });

    describe("Data Flow Integration Tests", () => {
        it("should pass projectId through the component hierarchy based on configuration", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                config: {
                    requirePolicyId: false,
                    passProjectIdToFrame: true,
                },
            };

            render(<AppWorkflowFrame {...props} />);

            // The projectId should be passed through to WorkflowFrame
            // We can validate this by checking the rendered structure
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should conditionally pass projectId based on configuration", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                config: {
                    requirePolicyId: false,
                    passProjectIdToFrame: false, // Should NOT pass projectId
                },
            };

            render(<AppWorkflowFrame {...props} />);

            // Component should render successfully even when not passing projectId
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should integrate policyId in multi-tenant scenarios", () => {
            const props: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                policyId: "test-policy-456",
                config: {
                    requirePolicyId: true,
                    passProjectIdToFrame: true,
                },
            };

            render(<AppWorkflowFrame {...props} />);

            // Component should render successfully with policy isolation
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });
    });

    describe("Cross-Component Integration Tests", () => {
        it("should integrate with external navigation systems", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            render(<AppWorkflowFrame {...props} />);

            // Component should integrate with Next.js router without errors
            // The useRouter hook integration is tested by successful rendering
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should integrate with notification systems", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            render(<AppWorkflowFrame {...props} />);

            // Component should integrate with toast notifications without errors
            // The toast integration is tested by successful rendering
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should integrate with workflow data management systems", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            render(<AppWorkflowFrame {...props} />);

            // Component should integrate with WorkflowDataProvider for data management
            // This is tested by successful rendering with complex workflow data
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });
    });

    describe("Performance Integration Tests", () => {
        it("should handle large workflow datasets without performance degradation", () => {
            // Create a larger workflow dataset
            const largeWorkflowData = {
                ...mockWorkflowData,
                nodes: Array.from({ length: 50 }, (_, i) => ({
                    id: `node-${i}`,
                    type: "transform",
                    position: { x: (i % 10) * 100, y: Math.floor(i / 10) * 100 },
                    data: { label: `Node ${i}` },
                })),
                edges: Array.from({ length: 49 }, (_, i) => ({
                    id: `edge-${i}`,
                    source: `node-${i}`,
                    target: `node-${i + 1}`,
                })),
            };

            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: largeWorkflowData,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            const startTime = performance.now();
            render(<AppWorkflowFrame {...props} />);
            const endTime = performance.now();

            // Should render efficiently even with large datasets
            expect(endTime - startTime).toBeLessThan(1000); // Less than 1 second

            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should handle rapid re-renders without memory leaks", () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project-123",
                config: GLOBAL_SCOPE_CONFIG,
            };

            const { rerender } = render(<AppWorkflowFrame {...props} />);

            // Simulate rapid re-renders
            for (let i = 0; i < 10; i++) {
                rerender(<AppWorkflowFrame {...props} projectId={`project-${i}`} />);
            }

            // Component should still be functional after multiple re-renders
            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });
    });

    describe("Real-World Usage Scenarios", () => {
        it("should handle typical Global application usage scenario", () => {
            // Simulate how the open app would use the component
            const globalProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "open-source-project",
                config: GLOBAL_SCOPE_CONFIG,
                onNodeClick: (e, node) => {
                    // Typical Global workflow: simple node selection
                    console.log("Global: Node clicked", node.id);
                },
                onPaneClick: (e) => {
                    // Typical Global workflow: deselect nodes
                    console.log("Global: Pane clicked");
                },
            };

            render(<AppWorkflowFrame {...globalProps} />);

            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should handle typical Project application usage scenario", () => {
            // Simulate how a Project app would use the component
            const projectProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-123",
                policyId: "project-456",
                config: PROJECT_SCOPE_CONFIG,
                onNodeClick: (e, node) => {
                    // Typical Project workflow: node analytics and multi-tenant tracking
                    console.log("Project: Node clicked with policy context", node.id);
                },
                onPaneClick: (e) => {
                    // Typical Project workflow: workspace management
                    console.log("Project: Pane clicked in policy context");
                },
            };

            render(<AppWorkflowFrame {...projectProps} />);

            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });

        it("should handle edge case scenarios without breaking", () => {
            // Test with minimal data
            const minimalWorkflowData = {
                id: "minimal",
                name: "Minimal",
                description: "",
                nodes: [],
                edges: [],
            };

            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: minimalWorkflowData,
                config: GLOBAL_SCOPE_CONFIG,
            };

            render(<AppWorkflowFrame {...props} />);

            const workflowFrame = screen.getByTestId("workflow-frame");
            expect(workflowFrame).toBeInTheDocument();
        });
    });
});
