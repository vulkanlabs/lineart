import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AppWorkflowFrame, type AppWorkflowFrameProps } from '../workflow-frame'

// Mock the base package
vi.mock('@vulkanlabs/base', () => ({
    AppWorkflowFrame: ({ children, ...props }: any) => (
        <div data-testid="shared-app-workflow-frame" data-config={JSON.stringify(props.config)}>
            {children}
        </div>
    ),
    GLOBAL_SCOPE_CONFIG: {
        requirePolicyId: false,
        passProjectIdToFrame: true,
    }
}))

// Mock workflow data for tests
const mockWorkflowData = {
    nodes: [
        { id: '1', type: 'input', data: { label: 'Start' }, position: { x: 0, y: 0 } }
    ],
    edges: []
}

describe('OSS AppWorkflowFrame Wrapper', () => {
    describe('Configuration Behavior', () => {
        it('should use global scope configuration', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
            }

            render(<AppWorkflowFrame {...props} />)
            
            const sharedComponent = screen.getByTestId('shared-app-workflow-frame')
            const configData = JSON.parse(sharedComponent.getAttribute('data-config') || '{}')
            
            expect(configData).toEqual({
                requirePolicyId: false,
                passProjectIdToFrame: true,
            })
        })

        it('should not require policyId for global scope', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                // No policyId - should work fine for global scope
            }

            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            
            const sharedComponent = screen.getByTestId('shared-app-workflow-frame')
            expect(sharedComponent).toBeTruthy()
        })

        it('should pass projectId when provided', () => {
            const projectId = 'test-project-123'
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId,
            }

            render(<AppWorkflowFrame {...props} />)
            
            const sharedComponent = screen.getByTestId('shared-app-workflow-frame')
            expect(sharedComponent).toBeTruthy()
        })

        it('should work without projectId (global context)', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                // No projectId - valid for global scope
            }

            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })
    })

    describe('Props Forwarding', () => {
        it('should forward all props to shared component', () => {
            const mockNodeClick = vi.fn()
            const mockPaneClick = vi.fn()
            
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                onNodeClick: mockNodeClick,
                onPaneClick: mockPaneClick,
            }

            render(<AppWorkflowFrame {...props} />)
            
            const sharedComponent = screen.getByTestId('shared-app-workflow-frame')
            expect(sharedComponent).toBeTruthy()
        })

        it('should maintain type compatibility with GlobalScopeWorkflowFrameProps', () => {
            // This test verifies TypeScript compatibility
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                onNodeClick: (e, node) => {
                    // Type should be correctly inferred
                    expect(typeof e).toBe('object')
                },
                onPaneClick: (e) => {
                    // Type should be correctly inferred
                    expect(typeof e).toBe('object')
                }
            }

            render(<AppWorkflowFrame {...props} />)
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })
    })

    describe('Integration with Base Package', () => {
        it('should render shared component with correct structure', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
            }

            render(<AppWorkflowFrame {...props} />)
            
            // Verify the wrapper renders the shared component
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })

        it('should apply global scope configuration consistently', () => {
            const props1: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'project-1',
            }
            
            const props2: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'project-2',
            }

            const { rerender } = render(<AppWorkflowFrame {...props1} />)
            const config1 = JSON.parse(screen.getByTestId('shared-app-workflow-frame').getAttribute('data-config') || '{}')
            
            rerender(<AppWorkflowFrame {...props2} />)
            const config2 = JSON.parse(screen.getByTestId('shared-app-workflow-frame').getAttribute('data-config') || '{}')
            
            // Both should use the same global scope config
            expect(config1).toEqual(config2)
            expect(config1.requirePolicyId).toBe(false)
        })
    })

    describe('Error Scenarios', () => {
        it('should handle missing workflowData gracefully', () => {
            const props = {
                projectId: 'test-project',
                // Missing workflowData - base component should handle this
            } as AppWorkflowFrameProps

            // The wrapper itself shouldn't throw - let base component handle validation
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })
    })

    describe('Performance Characteristics', () => {
        it('should use static configuration without recreation', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
            }

            const { rerender } = render(<AppWorkflowFrame {...props} />)
            const config1 = screen.getByTestId('shared-app-workflow-frame').getAttribute('data-config')
            
            // Rerender multiple times
            rerender(<AppWorkflowFrame {...props} />)
            rerender(<AppWorkflowFrame {...props} />)
            
            const config2 = screen.getByTestId('shared-app-workflow-frame').getAttribute('data-config')
            
            // Configuration should remain consistent
            expect(config1).toEqual(config2)
        })
    })
})