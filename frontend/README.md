# Vulkan Engine Frontend

An easy-to-use, fully featured console to manage your policies.

## Architecture

- **packages/base**: Shared base package containing all UI components, utilities, and styles
- **apps/open**: Open-source application that consumes the base package

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

#### @vulkanlabs/base

The base package contains:

- UI components and design system
- Shared utilities and hooks
- Styling and themes
- TypeScript types
