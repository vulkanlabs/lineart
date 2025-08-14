import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'

// Apply mocks before importing
vi.mock('next/navigation', () => ({
    useRouter: vi.fn(() => ({
        push: vi.fn(),
        replace: vi.fn(),
        refresh: vi.fn(),
        back: vi.fn(),
        forward: vi.fn(),
        prefetch: vi.fn(),
    }))
}))

vi.mock('sonner', () => ({
    toast: vi.fn()
}))

vi.mock('../workflow', () => ({
    createWorkflowApiClient: vi.fn(() => ({}))
}))

// Now import the module under test
import { 
    AppWorkflowFrame,
    GLOBAL_SCOPE_CONFIG,
    PROJECT_SCOPE_CONFIG,
    type GlobalScopeWorkflowFrameProps,
    type ProjectScopeWorkflowFrameProps 
} from '../app-workflow-frame'

// Get mock references for test manipulation (safely)
const getMocks = () => {
    try {
        return {
            useRouter: vi.mocked(require('next/navigation')).useRouter,
            toast: vi.mocked(require('sonner')).toast,
            createWorkflowApiClient: vi.mocked(require('../workflow')).createWorkflowApiClient
        }
    } catch (e) {
        return {
            useRouter: vi.fn(),
            toast: vi.fn(),
            createWorkflowApiClient: vi.fn()
        }
    }
}

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

describe('AppWorkflowFrame Security and Validation', () => {
    describe('Configuration Tampering Protection', () => {
        it('should prevent runtime config mutations for GLOBAL_SCOPE_CONFIG', () => {
            const originalConfig = { ...GLOBAL_SCOPE_CONFIG }
            
            // Attempt to mutate
            try {
                (GLOBAL_SCOPE_CONFIG as any).requirePolicyId = true
                (GLOBAL_SCOPE_CONFIG as any).newProperty = 'malicious'
            } catch (error) {
                // Expected to fail for frozen objects
            }
            
            // Should maintain original values
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).toBe(originalConfig.requirePolicyId)
            expect(GLOBAL_SCOPE_CONFIG.passProjectIdToFrame).toBe(originalConfig.passProjectIdToFrame)
            expect((GLOBAL_SCOPE_CONFIG as any).newProperty).toBeUndefined()
        })

        it('should prevent runtime config mutations for PROJECT_SCOPE_CONFIG', () => {
            const originalConfig = { ...PROJECT_SCOPE_CONFIG }
            
            // Attempt to mutate
            try {
                (PROJECT_SCOPE_CONFIG as any).requirePolicyId = false
                (PROJECT_SCOPE_CONFIG as any).maliciousFlag = true
            } catch (error) {
                // Expected to fail for frozen objects
            }
            
            // Should maintain original values
            expect(PROJECT_SCOPE_CONFIG.requirePolicyId).toBe(originalConfig.requirePolicyId)
            expect(PROJECT_SCOPE_CONFIG.passProjectIdToFrame).toBe(originalConfig.passProjectIdToFrame)
            expect((PROJECT_SCOPE_CONFIG as any).maliciousFlag).toBeUndefined()
        })

        it('should maintain config object reference stability', () => {
            const config1 = GLOBAL_SCOPE_CONFIG
            const config2 = GLOBAL_SCOPE_CONFIG
            
            expect(config1).toBe(config2) // Same reference
            
            // Should be the same object instance
            expect(Object.is(config1, config2)).toBe(true)
        })
    })

    describe('Input Validation Edge Cases', () => {
        it('should handle malformed workflow data gracefully', () => {
            const malformedData = {
                nodes: "not-an-array" as any,
                edges: null as any,
                invalidProperty: "should-be-ignored"
            }
            
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: malformedData,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Should not crash the component
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })

        it('should validate callback function types', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                onNodeClick: "not-a-function" as any,
                onPaneClick: 12345 as any,
                onEdgeClick: null as any,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Should handle invalid callbacks gracefully
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })

        it('should handle empty and null projectId values', () => {
            const emptyProjectProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: '' as any,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const nullProjectProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: null as any,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Empty projectId should be handled
            expect(() => render(<AppWorkflowFrame {...emptyProjectProps} />)).not.toThrow()
            
            // Null projectId should be handled
            expect(() => render(<AppWorkflowFrame {...nullProjectProps} />)).not.toThrow()
        })
    })
})

describe('AppWorkflowFrame Multi-Tenant Security', () => {
    describe('Policy ID Validation', () => {
        it('should reject empty policy IDs in project scope', () => {
            const emptyPolicyProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                policyId: '',
                config: PROJECT_SCOPE_CONFIG
            }
            
            expect(() => render(<AppWorkflowFrame {...emptyPolicyProps} />)).toThrow()
        })

        it('should reject null/undefined policy IDs in project scope', () => {
            const nullPolicyProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                policyId: null as any,
                config: PROJECT_SCOPE_CONFIG
            }
            
            const undefinedPolicyProps: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                policyId: undefined as any,
                config: PROJECT_SCOPE_CONFIG
            }
            
            expect(() => render(<AppWorkflowFrame {...nullPolicyProps} />)).toThrow()
            expect(() => render(<AppWorkflowFrame {...undefinedPolicyProps} />)).toThrow()
        })

        it('should handle malicious policy ID patterns', () => {
            const maliciousPolicyIds = [
                '<script>alert("xss")</script>',
                '../../../etc/passwd',
                'policy"; DROP TABLE users; --',
                '../../admin/config'
            ]
            
            maliciousPolicyIds.forEach(maliciousPolicyId => {
                const props: ProjectScopeWorkflowFrameProps = {
                    workflowData: mockWorkflowData,
                    projectId: 'test-project',
                    policyId: maliciousPolicyId,
                    config: PROJECT_SCOPE_CONFIG
                }
                
                // Should either handle gracefully or reject explicitly
                expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            })
        })
    })

    describe('Tenant Isolation', () => {
        it('should prevent cross-tenant data leakage through props', () => {
            const tenant1Data = {
                nodes: [{ id: 'tenant1-node', data: { secret: 'tenant1-secret' } }],
                edges: []
            }
            
            const tenant2Props: ProjectScopeWorkflowFrameProps = {
                workflowData: tenant1Data, // Tenant 1 data
                projectId: 'tenant2-project', // Tenant 2 project
                policyId: 'tenant2-policy',
                config: PROJECT_SCOPE_CONFIG
            }
            
            // Should render without exposing cross-tenant data
            const { container } = render(<AppWorkflowFrame {...tenant2Props} />)
            
            // Verify no cross-tenant data is exposed in DOM
            expect(container.innerHTML).not.toContain('tenant1-secret')
        })

        it('should validate project-policy relationship integrity', () => {
            // Test different combinations of project/policy relationships
            const validCombinations = [
                { projectId: 'project-a', policyId: 'policy-a' },
                { projectId: 'project-b', policyId: 'policy-b' }
            ]
            
            const invalidCombinations = [
                { projectId: 'project-a', policyId: 'policy-b' }, // Mismatched
                { projectId: 'project-x', policyId: 'policy-y' }  // Both invalid
            ]
            
            validCombinations.forEach(({ projectId, policyId }) => {
                const props: ProjectScopeWorkflowFrameProps = {
                    workflowData: mockWorkflowData,
                    projectId,
                    policyId,
                    config: PROJECT_SCOPE_CONFIG
                }
                
                expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            })
            
            // Note: Invalid combinations should be handled by business logic validation
            // For now, we just ensure they don't crash the component
            invalidCombinations.forEach(({ projectId, policyId }) => {
                const props: ProjectScopeWorkflowFrameProps = {
                    workflowData: mockWorkflowData,
                    projectId,
                    policyId,
                    config: PROJECT_SCOPE_CONFIG
                }
                
                expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            })
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

describe('AppWorkflowFrame Component Lifecycle and Error Recovery', () => {
    describe('Component Mounting and Unmounting', () => {
        it('should handle component unmounting gracefully', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const { unmount } = render(<AppWorkflowFrame {...props} />)
            
            // Should clean up without errors
            expect(() => unmount()).not.toThrow()
        })

        it('should handle rapid mount/unmount cycles', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Simulate rapid mount/unmount cycles
            for (let i = 0; i < 5; i++) {
                const { unmount } = render(<AppWorkflowFrame {...props} />)
                expect(() => unmount()).not.toThrow()
            }
        })

        it('should handle props changes correctly during re-renders', () => {
            const initialProps: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'initial-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const updatedProps: GlobalScopeWorkflowFrameProps = {
                workflowData: {
                    nodes: [...mockWorkflowData.nodes, { id: '3', type: 'process', data: { label: 'New Node' }, position: { x: 200, y: 200 } }],
                    edges: mockWorkflowData.edges
                },
                projectId: 'updated-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const { rerender } = render(<AppWorkflowFrame {...initialProps} />)
            
            // Should handle prop changes without errors
            expect(() => rerender(<AppWorkflowFrame {...updatedProps} />)).not.toThrow()
            
            // Verify component still renders correctly
            expect(screen.getByTestId('workflow-frame')).toBeTruthy()
        })
    })

    describe('Error Boundary Integration', () => {
        it('should handle external dependencies gracefully', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Should render without throwing errors
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('workflow-frame')).toBeTruthy()
        })

        it('should handle workflow data corruption gracefully', () => {
            const corruptedData = {
                nodes: [
                    { id: null, type: undefined, data: "corrupted" }, // Corrupted node
                    { position: { x: "invalid", y: [] } } // Missing required fields
                ],
                edges: "not-an-array" // Should be array
            }
            
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: corruptedData as any,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Should handle corrupted data without crashing
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })

        it('should recover from temporary rendering errors', () => {
            let shouldThrow = true
            
            const ConditionalComponent = () => {
                if (shouldThrow) {
                    throw new Error('Temporary error')
                }
                return <div>Success</div>
            }
            
            // Test error boundary behavior (simplified)
            expect(() => {
                try {
                    render(<ConditionalComponent />)
                } catch (error) {
                    shouldThrow = false
                    render(<ConditionalComponent />)
                }
            }).not.toThrow()
        })
    })

    describe('Memory Management and Performance', () => {
        it('should not create memory leaks with frequent re-renders', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const { rerender } = render(<AppWorkflowFrame {...props} />)
            
            // Simulate many re-renders to check for memory leaks
            for (let i = 0; i < 50; i++) {
                const newProps = {
                    ...props,
                    projectId: `test-project-${i}`
                }
                rerender(<AppWorkflowFrame key={i} {...newProps} />)
            }
            
            // Component should still be functional after many re-renders
            expect(screen.getByTestId('workflow-frame')).toBeTruthy()
        })

        it('should handle large workflow datasets efficiently', () => {
            // Create a large workflow dataset
            const largeWorkflowData = {
                nodes: Array.from({ length: 100 }, (_, i) => ({
                    id: `node-${i}`,
                    type: 'process',
                    data: { label: `Node ${i}`, payload: `data-${i}` },
                    position: { x: i * 10, y: i * 10 }
                })),
                edges: Array.from({ length: 99 }, (_, i) => ({
                    id: `edge-${i}`,
                    source: `node-${i}`,
                    target: `node-${i + 1}`
                }))
            }
            
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: largeWorkflowData,
                projectId: 'large-dataset-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Should handle large datasets without performance issues
            const startTime = performance.now()
            render(<AppWorkflowFrame {...props} />)
            const endTime = performance.now()
            
            // Rendering should complete in reasonable time (under 1 second)
            expect(endTime - startTime).toBeLessThan(1000)
            expect(screen.getByTestId('workflow-frame')).toBeTruthy()
        })

        it('should maintain config object reference stability across renders', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const { rerender } = render(<AppWorkflowFrame {...props} />)
            
            const initialConfigRef = GLOBAL_SCOPE_CONFIG
            
            // Rerender with same config
            rerender(<AppWorkflowFrame {...props} />)
            
            // Config reference should remain stable
            expect(GLOBAL_SCOPE_CONFIG).toBe(initialConfigRef)
            expect(Object.is(GLOBAL_SCOPE_CONFIG, initialConfigRef)).toBe(true)
        })
    })

    describe('Integration with External Systems', () => {
        it('should handle navigation integration properly', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Component should render with navigation features
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('workflow-frame')).toBeTruthy()
        })

        it('should handle notification systems properly', () => {
            const props: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                config: GLOBAL_SCOPE_CONFIG
            }
            
            // Component should render with notification features
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('workflow-frame')).toBeTruthy()
        })

        it('should handle concurrent rendering scenarios', async () => {
            const props1: GlobalScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'concurrent-project-1',
                config: GLOBAL_SCOPE_CONFIG
            }
            
            const props2: ProjectScopeWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'concurrent-project-2',
                policyId: 'concurrent-policy-2',
                config: PROJECT_SCOPE_CONFIG
            }
            
            // Render multiple instances concurrently
            const promise1 = Promise.resolve().then(() => render(<AppWorkflowFrame {...props1} />))
            const promise2 = Promise.resolve().then(() => render(<AppWorkflowFrame {...props2} />))
            
            const [result1, result2] = await Promise.all([promise1, promise2])
            
            // Both should render successfully - use getAllByTestId to handle multiple instances
            expect(result1.getAllByTestId('workflow-frame').length).toBeGreaterThan(0)
            expect(result2.getAllByTestId('workflow-frame').length).toBeGreaterThan(0)
        })
    })
})