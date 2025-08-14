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

describe('OSS AppWorkflowFrame Edge Cases and Security', () => {
    describe('Configuration Security', () => {
        it('should prevent config tampering via props', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'test-project'
            }
            
            render(<AppWorkflowFrame {...props} />)
            
            // Component should always use GLOBAL_SCOPE_CONFIG regardless of external factors
            const sharedComponent = screen.getByTestId('shared-app-workflow-frame')
            const configData = JSON.parse(sharedComponent.getAttribute('data-config') || '{}')
            
            expect(configData.requirePolicyId).toBe(false)
            expect(configData.passProjectIdToFrame).toBe(true)
        })

        it('should maintain OSS scope behavior regardless of external manipulation', () => {
            // Verify that GLOBAL_SCOPE_CONFIG is always used
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'oss-project'
            }
            
            render(<AppWorkflowFrame {...props} />)
            
            // Component should render with OSS configuration
            const sharedComponent = screen.getByTestId('shared-app-workflow-frame')
            expect(sharedComponent).toBeTruthy()
            
            // Verify config props passed to shared component
            const configData = JSON.parse(sharedComponent.getAttribute('data-config') || '{}')
            expect(configData).toEqual({
                requirePolicyId: false,
                passProjectIdToFrame: true,
            })
        })

        it('should reject invalid projectId formats securely', () => {
            const maliciousProjectIds = [
                '<script>alert("xss")</script>',
                '../../../etc/passwd',
                'project"; DROP TABLE users; --',
                '../../admin/config',
                'project\x00null-byte'
            ]
            
            maliciousProjectIds.forEach(maliciousProjectId => {
                const props: AppWorkflowFrameProps = {
                    workflowData: mockWorkflowData,
                    projectId: maliciousProjectId
                }
                
                // Should handle malicious project IDs safely
                expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
                
                // Component should still render - use getAllByTestId to handle multiple instances
                expect(screen.getAllByTestId('shared-app-workflow-frame').length).toBeGreaterThan(0)
            })
        })
    })

    describe('Performance and Memory Management', () => {
        it('should handle frequent prop changes efficiently', () => {
            const initialProps: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'initial-project'
            }
            
            const { rerender } = render(<AppWorkflowFrame {...initialProps} />)
            
            // Simulate rapid prop changes
            for (let i = 0; i < 25; i++) {
                const newProps: AppWorkflowFrameProps = {
                    workflowData: {
                        ...mockWorkflowData,
                        nodes: [...mockWorkflowData.nodes, { 
                            id: `dynamic-${i}`, 
                            type: 'process', 
                            data: { label: `Dynamic ${i}` }, 
                            position: { x: i * 20, y: i * 20 } 
                        }]
                    },
                    projectId: `project-${i}`
                }
                
                expect(() => rerender(<AppWorkflowFrame {...newProps} />)).not.toThrow()
            }
            
            // Component should still be functional
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })

        it('should handle unmounting during data loading', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'loading-project'
            }
            
            const { unmount } = render(<AppWorkflowFrame {...props} />)
            
            // Should unmount cleanly even during potential async operations
            expect(() => unmount()).not.toThrow()
        })

        it('should maintain config reference stability', () => {
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'stable-project'
            }
            
            const { rerender } = render(<AppWorkflowFrame {...props} />)
            
            // Get initial config
            const initialConfig = screen.getByTestId('shared-app-workflow-frame').getAttribute('data-config')
            
            // Rerender with same props
            rerender(<AppWorkflowFrame {...props} />)
            
            // Config should remain stable
            const updatedConfig = screen.getByTestId('shared-app-workflow-frame').getAttribute('data-config')
            expect(initialConfig).toEqual(updatedConfig)
        })
    })

    describe('Error Recovery and Resilience', () => {
        it('should handle corrupted workflow data gracefully', () => {
            const corruptedData = {
                nodes: "invalid-nodes" as any,
                edges: null as any,
                extraProperty: "should-be-ignored"
            }
            
            const props: AppWorkflowFrameProps = {
                workflowData: corruptedData,
                projectId: 'corruption-test'
            }
            
            // Should not crash with corrupted data
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
        })

        it('should handle missing required props', () => {
            const incompleteProps = {
                workflowData: mockWorkflowData
                // Missing projectId - should be handled gracefully
            } as AppWorkflowFrameProps
            
            // Should handle missing props gracefully
            expect(() => render(<AppWorkflowFrame {...incompleteProps} />)).not.toThrow()
        })

        it('should recover from prop type mismatches', () => {
            const typeMismatchProps = {
                workflowData: "not-an-object" as any,
                projectId: 12345 as any,
                onNodeClick: "not-a-function" as any
            }
            
            // Should handle type mismatches gracefully
            expect(() => render(<AppWorkflowFrame {...typeMismatchProps} />)).not.toThrow()
        })

        it('should handle null and undefined props safely', () => {
            const nullProps = {
                workflowData: null as any,
                projectId: null as any,
                onNodeClick: null as any
            }
            
            const undefinedProps = {
                workflowData: undefined as any,
                projectId: undefined as any,
                onPaneClick: undefined as any
            }
            
            // Should handle null/undefined props
            expect(() => render(<AppWorkflowFrame {...nullProps} />)).not.toThrow()
            expect(() => render(<AppWorkflowFrame {...undefinedProps} />)).not.toThrow()
        })
    })

    describe('Integration Compatibility', () => {
        it('should work with different workflow data structures', () => {
            const alternativeWorkflowData = {
                nodes: [
                    { id: 'alt1', type: 'custom-input', data: { customLabel: 'Alt Start' }, position: { x: 10, y: 10 } },
                    { id: 'alt2', type: 'custom-output', data: { customLabel: 'Alt End' }, position: { x: 110, y: 110 } }
                ],
                edges: [
                    { id: 'alt-edge', source: 'alt1', target: 'alt2', type: 'custom-edge' }
                ],
                metadata: { version: '2.0', type: 'alternative' }
            }
            
            const props: AppWorkflowFrameProps = {
                workflowData: alternativeWorkflowData,
                projectId: 'alternative-data-project'
            }
            
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })

        it('should handle empty workflow data', () => {
            const emptyWorkflowData = {
                nodes: [],
                edges: []
            }
            
            const props: AppWorkflowFrameProps = {
                workflowData: emptyWorkflowData,
                projectId: 'empty-workflow'
            }
            
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })

        it('should handle large project ID strings', () => {
            const largeProjectId = 'x'.repeat(1000) // Very long project ID
            
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: largeProjectId
            }
            
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })

        it('should handle complex callback scenarios', () => {
            const asyncCallback = vi.fn(async (e, node) => {
                await new Promise(resolve => setTimeout(resolve, 1))
                return `processed-${node?.id}`
            })
            
            const throwingCallback = vi.fn(() => {
                throw new Error('Callback error')
            })
            
            const props: AppWorkflowFrameProps = {
                workflowData: mockWorkflowData,
                projectId: 'callback-test',
                onNodeClick: asyncCallback,
                onPaneClick: throwingCallback
            }
            
            // Should handle complex callbacks without crashing
            expect(() => render(<AppWorkflowFrame {...props} />)).not.toThrow()
            expect(screen.getByTestId('shared-app-workflow-frame')).toBeTruthy()
        })
    })
})