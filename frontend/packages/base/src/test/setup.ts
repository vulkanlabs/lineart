import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Sonner toast
vi.mock('sonner', () => ({
  toast: vi.fn(),
}))

// Mock workflow API client
vi.mock('../workflow', () => ({
  WorkflowFrame: ({ children, ...props }: any) => {
    const React = require('react')
    return React.createElement('div', { 'data-testid': 'workflow-frame', ...props }, children)
  },
  WorkflowApiProvider: ({ children }: any) => {
    const React = require('react')
    return React.createElement('div', { 'data-testid': 'workflow-api-provider' }, children)
  },
  WorkflowDataProvider: ({ children }: any) => {
    const React = require('react')
    return React.createElement('div', { 'data-testid': 'workflow-data-provider' }, children)
  },
  createWorkflowApiClient: vi.fn(() => ({})),
}))

// Global test utilities
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Suppress console errors in tests unless specifically testing error handling
const originalError = console.error
beforeAll(() => {
  console.error = vi.fn()
})

afterAll(() => {
  console.error = originalError
})