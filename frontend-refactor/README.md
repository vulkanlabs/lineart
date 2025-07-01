# Vulkan Frontend Refactor

This is the refactored frontend structure for the open-core business model.

## Architecture

- **packages/base**: Shared base package containing all UI components, utilities, and styles
- **apps/open**: Open-source application that consumes the base package
- **Future**: Enterprise features will be in a separate private repository

## Getting Started

### Prerequisites

- Node.js >= 18
- npm

### Installation

```bash
npm install
```

### Development

```bash
# Start development servers for all apps
npm run dev

# Build all packages
npm run build

# Lint all code
npm run lint
```

### Package Structure

#### @vulkan/base

The base package contains:
- UI components and design system
- Shared utilities and hooks
- Styling and themes
- TypeScript types

#### @vulkan/app-open

The open-source application that:
- Consumes the @vulkan/base package
- Provides the core functionality
- Serves as the foundation for all variants

## Next Steps

1. Copy actual frontend code from `/frontend` into `/packages/base/src`
2. Update export statements in `/packages/base/src/index.ts` and `/packages/base/src/ui/index.ts`
3. Replace placeholder homepage in `/apps/open/src/app/page.tsx` with actual app layout
4. Set up GitHub Packages publishing workflow
5. Create enterprise repository structure