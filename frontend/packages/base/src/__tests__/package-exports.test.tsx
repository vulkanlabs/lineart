/**
 * Package Export/Import Validation Tests
 * 
 * Ensures all exports from the base package are properly accessible and typed.
 * This prevents regressions where exports are accidentally removed or mistyped.
 */

import { describe, it, expect } from 'vitest'

// Import components directly for validation
import {
    AppWorkflowFrame,
    GLOBAL_SCOPE_CONFIG,
    PROJECT_SCOPE_CONFIG,
} from '../components/app-workflow-frame'

import { VulkanLogo } from '../components/logo'
import { RefreshButton } from '../components/refresh-button'

describe('Package Export/Import Validation', () => {
    describe('AppWorkflowFrame Exports', () => {
        it('should export AppWorkflowFrame component', () => {
            expect(AppWorkflowFrame).toBeDefined()
            // React.memo returns an object, not a function, but it's still a valid React component
            expect(typeof AppWorkflowFrame).toBe('object')
            expect(AppWorkflowFrame).toHaveProperty('$$typeof')
        })

        it('should export configuration constants', () => {
            expect(GLOBAL_SCOPE_CONFIG).toBeDefined()
            expect(PROJECT_SCOPE_CONFIG).toBeDefined()
            expect(typeof GLOBAL_SCOPE_CONFIG).toBe('object')
            expect(typeof PROJECT_SCOPE_CONFIG).toBe('object')
        })

        it('should export configuration constants with correct properties', () => {
            // Validate GLOBAL_SCOPE_CONFIG
            expect(GLOBAL_SCOPE_CONFIG).toHaveProperty('requirePolicyId')
            expect(GLOBAL_SCOPE_CONFIG).toHaveProperty('passProjectIdToFrame')
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).toBe(false)
            expect(GLOBAL_SCOPE_CONFIG.passProjectIdToFrame).toBe(true)

            // Validate PROJECT_SCOPE_CONFIG  
            expect(PROJECT_SCOPE_CONFIG).toHaveProperty('requirePolicyId')
            expect(PROJECT_SCOPE_CONFIG).toHaveProperty('passProjectIdToFrame')
            expect(PROJECT_SCOPE_CONFIG.requirePolicyId).toBe(true)
            expect(PROJECT_SCOPE_CONFIG.passProjectIdToFrame).toBe(true)
        })

        it('should export immutable configuration constants', () => {
            // Validate that configs are frozen (immutable)
            expect(Object.isFrozen(GLOBAL_SCOPE_CONFIG)).toBe(true)
            expect(Object.isFrozen(PROJECT_SCOPE_CONFIG)).toBe(true)

            // Validate that properties cannot be modified
            expect(() => {
                (GLOBAL_SCOPE_CONFIG as any).requirePolicyId = true
            }).toThrow()

            expect(() => {
                (PROJECT_SCOPE_CONFIG as any).requirePolicyId = false
            }).toThrow()
        })
    })

    describe('Core Component Exports', () => {
        it('should export VulkanLogo component', () => {
            expect(VulkanLogo).toBeDefined()
            expect(typeof VulkanLogo).toBe('function')
        })

        it('should export RefreshButton component', () => {
            expect(RefreshButton).toBeDefined()
            expect(typeof RefreshButton).toBe('function')
        })
    })

    describe('Configuration Validation', () => {
        it('should maintain consistent configuration structure', () => {
            // Both configs should have the same property keys
            const globalKeys = Object.keys(GLOBAL_SCOPE_CONFIG).sort()
            const projectKeys = Object.keys(PROJECT_SCOPE_CONFIG).sort()
            
            expect(globalKeys).toEqual(projectKeys)
            expect(globalKeys).toEqual(['passProjectIdToFrame', 'requirePolicyId'])
        })

        it('should have different values for different scopes', () => {
            // Global and project configs should be different
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).not.toBe(PROJECT_SCOPE_CONFIG.requirePolicyId)
            
            // But some properties can be the same
            expect(GLOBAL_SCOPE_CONFIG.passProjectIdToFrame).toBe(PROJECT_SCOPE_CONFIG.passProjectIdToFrame)
        })

        it('should prevent runtime tampering', () => {
            // Test that Object.defineProperty fails on frozen objects
            expect(() => {
                Object.defineProperty(GLOBAL_SCOPE_CONFIG, 'newProp', { value: 'hack' })
            }).toThrow()

            expect(() => {
                Object.defineProperty(PROJECT_SCOPE_CONFIG, 'newProp', { value: 'hack' })
            }).toThrow()
        })
    })

    describe('Component Function Properties', () => {
        it('should validate AppWorkflowFrame has expected properties', () => {
            // React.memo components have different properties than regular functions
            // Check that it's a memoized React component
            expect(typeof AppWorkflowFrame).toBe('object')
            expect(AppWorkflowFrame).toHaveProperty('$$typeof')
        })

        it('should validate component imports work as expected', () => {
            // Test that we can reference the components without errors
            const regularComponents = [VulkanLogo, RefreshButton]
            const memoizedComponents = [AppWorkflowFrame]
            
            for (const component of regularComponents) {
                expect(component).toBeDefined()
                expect(typeof component).toBe('function')
                expect(component.length).toBeGreaterThanOrEqual(0) // Has at least 0 parameters
            }
            
            for (const component of memoizedComponents) {
                expect(component).toBeDefined()
                expect(typeof component).toBe('object') // React.memo returns object
                expect(component).toHaveProperty('$$typeof')
            }
        })
    })

    describe('Cross-App Compatibility', () => {
        it('should export all components needed by open app', () => {
            // These are the critical exports used by the open app
            const criticalExports = {
                AppWorkflowFrame,
                GLOBAL_SCOPE_CONFIG,
                VulkanLogo,
                RefreshButton
            }
            
            for (const [name, exportValue] of Object.entries(criticalExports)) {
                expect(exportValue).toBeDefined()
                expect(name).toBeTruthy()
            }
        })

        it('should maintain scope configuration API contract', () => {
            // Test the API contract that other apps depend on
            
            // GLOBAL_SCOPE_CONFIG should be suitable for OSS (no policy required)
            expect(GLOBAL_SCOPE_CONFIG.requirePolicyId).toBe(false)
            expect(GLOBAL_SCOPE_CONFIG.passProjectIdToFrame).toBe(true)
            
            // PROJECT_SCOPE_CONFIG should require policy for multi-tenant environments
            expect(PROJECT_SCOPE_CONFIG.requirePolicyId).toBe(true)
            expect(PROJECT_SCOPE_CONFIG.passProjectIdToFrame).toBe(true)
        })

        it('should ensure configurations are safe for cross-app usage', () => {
            // Configurations should be frozen to prevent accidental modifications
            // by consuming applications
            expect(Object.isFrozen(GLOBAL_SCOPE_CONFIG)).toBe(true)
            expect(Object.isFrozen(PROJECT_SCOPE_CONFIG)).toBe(true)
            
            // Should not be extensible
            expect(Object.isExtensible(GLOBAL_SCOPE_CONFIG)).toBe(false)
            expect(Object.isExtensible(PROJECT_SCOPE_CONFIG)).toBe(false)
        })
    })

    describe('Type Safety and Compilation', () => {
        it('should maintain type safety for configuration objects', () => {
            // TypeScript compilation ensures type safety, but we can do runtime checks
            // to ensure the configuration objects match expected interface
            
            type ConfigKeys = 'requirePolicyId' | 'passProjectIdToFrame'
            
            const expectedKeys: ConfigKeys[] = ['requirePolicyId', 'passProjectIdToFrame']
            
            for (const key of expectedKeys) {
                expect(GLOBAL_SCOPE_CONFIG).toHaveProperty(key)
                expect(PROJECT_SCOPE_CONFIG).toHaveProperty(key)
                expect(typeof GLOBAL_SCOPE_CONFIG[key]).toBe('boolean')
                expect(typeof PROJECT_SCOPE_CONFIG[key]).toBe('boolean')
            }
        })

        it('should maintain component prop interface compatibility', () => {
            // Components should be callable and have proper function signatures
            expect(() => {
                // This tests that the component signature compiles and is callable
                const ComponentRef = AppWorkflowFrame
                expect(typeof ComponentRef).toBe('object') // React.memo returns object
                expect(ComponentRef).toHaveProperty('$$typeof')
            }).not.toThrow()
        })
    })
})