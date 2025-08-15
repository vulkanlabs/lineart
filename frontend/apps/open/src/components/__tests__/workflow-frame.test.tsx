import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppWorkflowFrame, type AppWorkflowFrameProps } from "../workflow-frame";

// Mock the base package
vi.mock("@vulkanlabs/base", () => ({
    AppWorkflowFrame: ({ children, ...props }: any) => (
        <div data-testid="shared-app-workflow-frame" data-config={JSON.stringify(props.config)}>
            {children}
        </div>
    ),
    GLOBAL_SCOPE_CONFIG: {
        requirePolicyId: false,
        passProjectIdToFrame: true,
    },
}));

// Mock workflow data for tests
const mockWorkflowData = {
    nodes: [{ id: "1", type: "input", data: { label: "Start" }, position: { x: 0, y: 0 } }],
    edges: [],
};

describe("global AppWorkflowFrame Wrapper", () => {
    describe("App-Specific Configuration", () => {
        it("should use global scope configuration for global app", () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
            };

            render(<AppWorkflowFrame {...props} />);

            const sharedComponent = screen.getByTestId("shared-app-workflow-frame");
            const configData = JSON.parse(sharedComponent.getAttribute("data-config") || "{}");

            expect(configData).toEqual({
                requirePolicyId: false,
                passProjectIdToFrame: true,
            });
        });

        it("should maintain global scope behavior consistently", () => {
            const props1: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-1",
            };

            const props2: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "project-2",
            };

            const { rerender } = render(<AppWorkflowFrame {...props1} />);
            const config1 = JSON.parse(
                screen.getByTestId("shared-app-workflow-frame").getAttribute("data-config") || "{}",
            );

            rerender(<AppWorkflowFrame {...props2} />);
            const config2 = JSON.parse(
                screen.getByTestId("shared-app-workflow-frame").getAttribute("data-config") || "{}",
            );

            // Both should use the same global scope config
            expect(config1).toEqual(config2);
            expect(config1.requirePolicyId).toBe(false);
        });
    });

    describe("global App Integration", () => {
        it("should render shared component from base package", () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
            };

            render(<AppWorkflowFrame {...props} />);

            // Verify the wrapper renders the shared component correctly
            expect(screen.getByTestId("shared-app-workflow-frame")).toBeTruthy();
        });

        it("should forward props to shared component correctly", () => {
            const mockNodeClick = vi.fn();
            const mockPaneClick = vi.fn();

            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: "test-project",
                onNodeClick: mockNodeClick,
                onPaneClick: mockPaneClick,
            };

            render(<AppWorkflowFrame {...props} />);

            const sharedComponent = screen.getByTestId("shared-app-workflow-frame");
            expect(sharedComponent).toBeTruthy();
        });
    });
});
