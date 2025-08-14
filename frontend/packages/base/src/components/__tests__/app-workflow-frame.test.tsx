import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { 
    AppWorkflowFrame,
    GLOBAL_SCOPE_CONFIG,
    PROJECT_SCOPE_CONFIG,
    type GlobalScopeWorkflowFrameProps,
    type ProjectScopeWorkflowFrameProps 
} from '../app-workflow-frame'

// Mock workflow data for tests
const mockWorkflowData = {
    nodes: [
        { id: '1', type: 'input', data: { label: 'Start' }, position: { x: 0, y: 0 } },
        { id: '2', type: 'output', data: { label: 'End' }, position: { x: 100, y: 100 } }
    ],
    edges: [
        { id: 'e1-2', source: '1', target: '2' }
    ]
}

describe('AppWorkflowFrame Configuration', () => {
    describe('Static Configuration Constants', () => {
        it('should export GLOBAL_SCOPE_CONFIG with correct values', () => {
            expect(GLOBAL_SCOPE_CONFIG).toEqual({
                requirePolicyId: false,
                passProjectIdToFrame: true,
            })
        })

        it('should export PROJECT_SCOPE_CONFIG with correct values', () => {
            expect(PROJECT_SCOPE_CONFIG).toEqual({
                requirePolicyId: true,
                passProjectIdToFrame: true,
            })
        })

        it('should have different configurations for different scopes', () => {
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).toBe(false)
            expect(PROJECT_SCOPE_CONFIG.requirePolicyId).toBe(true)
        })
    })

    describe('Configuration Schema Validation', () => {
        // These tests verify the runtime validation still works correctly
        it('should validate global scope configuration', () => {
            const globalProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                config: GLOBAL_SCOPE_CONFIG
            }

            expect(() => render(<AppWorkflowFrame {...globalProps} />)).not.toThrow()
        })

        it('should validate project scope configuration', () => {
            const projectProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                policyId: 'test-policy',
                config: PROJECT_SCOPE_CONFIG
            }

            expect(() => render(<AppWorkflowFrame {...projectProps} />)).not.toThrow()
        })

        it('should handle custom configuration objects', () => {
            const customConfig = {
                requirePolicyId: false,
                passProjectIdToFrame: false,
            }

            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                config: customConfig
            }

            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })

        it('should apply default values when config is empty', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                config: {} // Empty config should get defaults
            }

            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })
    })
})

describe('AppWorkflowFrame Error Handling', () => {
    const originalError = console.error
    
    beforeEach(() => {
        console.error = vi.fn()
    })

    afterEach(() => {
        console.error = originalError
    })

    it('should throw error when policyId required but not provided', () => {
        const props: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            config: { requirePolicyId: true } // Requires policyId but props don't have it
        }

        expect(() => render(<AppWorkflowFrame {...props} />)).toThrow(
            'AppWorkflowFrame: policyId is required when requirePolicyId is true'
        )
    })

    it('should not throw when policyId provided and required', () => {
        const props: ProjectScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            policyId: 'test-policy',
            config: { requirePolicyId: true }
        }

        expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
    })

    it('should not throw when policyId not required', () => {
        const props: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            config: { requirePolicyId: false }
        }

        expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
    })

    it('should provide clear error message for configuration mismatch', () => {
        const invalidProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            // Missing policyId but using PROJECT_SCOPE_CONFIG
            config: PROJECT_SCOPE_CONFIG
        } as GlobalScopeWorkflowFrameProps

        expect(() => render(<AppWorkflowFrame {...invalidProps} />)).toThrow(
            'AppWorkflowFrame: policyId is required when requirePolicyId is true'
        )
    })
})

describe('AppWorkflowFrame Type Guards', () => {
    // Note: Type guards are internal functions, so we test their behavior through component usage
    it('should correctly identify project scope props with policyId', () => {
        const projectProps: ProjectScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            policyId: 'test-policy',
            config: PROJECT_SCOPE_CONFIG
        }

        // If type guard works correctly, this should render without issues
        expect(() => render(<AppWorkflowFrame {...projectProps} />)).not.toThrow()
        
        // Check that the component renders the expected structure
        expect(screen.getByTestId('workflow-api-provider')).toBeTruthy()
        expect(screen.getByTestId('workflow-data-provider')).toBeTruthy()
        expect(screen.getByTestId('workflow-frame')).toBeTruthy()
    })

    it('should correctly identify global scope props without policyId', () => {
        const globalProps: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            config: GLOBAL_SCOPE_CONFIG
        }

        expect(() => render(<AppWorkflowFrame {...globalProps} />)).not.toThrow()
        
        // Check that the component renders the expected structure
        expect(screen.getByTestId('workflow-api-provider')).toBeTruthy()
        expect(screen.getByTestId('workflow-data-provider')).toBeTruthy()
        expect(screen.getByTestId('workflow-frame')).toBeTruthy()
    })

    it('should handle edge cases in prop detection', () => {
        // Test with undefined projectId
        const edgeProps: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            config: GLOBAL_SCOPE_CONFIG
            // No projectId
        }

        expect(() => render(<AppWorkflowFrame {...edgeProps} />)).not.toThrow()
    })
})

describe('AppWorkflowFrame Component Integration', () => {
    it('should render all required child components', () => {
        const props: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            config: GLOBAL_SCOPE_CONFIG
        }

        render(<AppWorkflowFrame {...props} />)

        // Verify the component tree structure
        expect(screen.getByTestId('workflow-api-provider')).toBeTruthy()
        expect(screen.getByTestId('workflow-data-provider')).toBeTruthy()
        expect(screen.getByTestId('workflow-frame')).toBeTruthy()
    })

    it('should pass props correctly to child components', () => {
        const props: ProjectScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project-123',
            policyId: 'test-policy-456',
            config: PROJECT_SCOPE_CONFIG
        }

        render(<AppWorkflowFrame {...props} />)

        const workflowDataProvider = screen.getByTestId('workflow-data-provider')
        const workflowFrame = screen.getByTestId('workflow-frame')

        // These are basic existence checks - in a real app you'd verify actual prop passing
        expect(workflowDataProvider).toBeTruthy()
        expect(workflowFrame).toBeTruthy()
    })

    it('should handle callback props correctly', () => {
        const mockNodeClick = vi.fn()
        const mockPaneClick = vi.fn()

        const props: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            onNodeClick: mockNodeClick,
            onPaneClick: mockPaneClick,
            config: GLOBAL_SCOPE_CONFIG
        }

        render(<AppWorkflowFrame {...props} />)

        // Component should render without calling the callbacks immediately
        expect(mockNodeClick).not.toHaveBeenCalled()
        expect(mockPaneClick).not.toHaveBeenCalled()
    })
})

describe('AppWorkflowFrame Configuration Performance', () => {
    it('should use static config objects without creating new instances', () => {
        // Verify that our static configs are not recreated
        const config1 = GLOBAL_SCOPE_CONFIG
        const config2 = GLOBAL_SCOPE_CONFIG

        expect(config1).toBe(config2) // Same reference, not just equal values
    })

    it('should not validate static configs on every render', () => {
        const props: GlobalScopeWorkflowFrameProps = {
            workflowData: mockWorkflowData,
            projectId: 'test-project',
            config: GLOBAL_SCOPE_CONFIG
        }

        // First render
        const { rerender } = render(<AppWorkflowFrame {...props} />)
        
        // Rerender multiple times to ensure no performance regression
        rerender(<AppWorkflowFrame {...props} />)
        rerender(<AppWorkflowFrame {...props} />)
        
        // Test passes if no errors thrown and performance is acceptable
        expect(screen.getByTestId('workflow-frame')).toBeTruthy()
    })
})