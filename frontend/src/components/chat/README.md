# Frontend Chat Interface

This document describes the chat interface implementation for the Vulkan platform's AI assistant.

## Components

### 1. ChatInterface
The main chat interface component that displays messages and handles user input.

**Location:** `src/components/chat/chat-interface.tsx`

**Props:**
- `onSendMessage?: (message: string) => Promise<string>` - Function to handle sending messages
- `className?: string` - Additional CSS classes

**Features:**
- Message history with timestamps
- User and agent avatars
- Loading indicators
- Auto-scrolling to latest messages
- Keyboard shortcuts (Enter to send)

### 2. ChatButton
A floating action button that opens/closes the chat interface.

**Location:** `src/components/chat/chat-button.tsx`

**Props:**
- `onSendMessage?: (message: string) => Promise<string>` - Function to handle sending messages
- `className?: string` - Additional CSS classes

**Features:**
- Fixed positioning (bottom-right corner)
- Expandable chat interface
- Close button when opened

### 3. ChatProvider
Context provider for managing chat API calls and state.

**Location:** `src/components/chat/chat-provider.tsx`

**Props:**
- `children: ReactNode` - Child components
- `apiEndpoint?: string` - Custom API endpoint (defaults to `/ai-agent/chat`)

**Features:**
- Centralized API communication
- Error handling
- Environment variable support

### 4. ChatLayout
Layout wrapper that automatically includes the floating chat button.

**Location:** `src/components/chat/chat-layout.tsx`

**Props:**
- `children: ReactNode` - Child components
- `apiEndpoint?: string` - Custom API endpoint

**Features:**
- Automatic chat provider setup
- Floating chat button integration

## Usage

### Basic Integration

The easiest way to add chat functionality to your app is by wrapping your layout with `ChatLayout`:

```tsx
import { ChatLayout } from "@/components/chat";

export default function RootLayout({ children }) {
    return (
        <ChatLayout>
            {/* Your existing layout */}
            {children}
        </ChatLayout>
    );
}
```

### Custom Chat Interface

For embedded chat interfaces:

```tsx
import { ChatInterface } from "@/components/chat";

export default function MyPage() {
    const handleSendMessage = async (message: string): Promise<string> => {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        const data = await response.json();
        return data.response;
    };

    return (
        <div>
            <ChatInterface onSendMessage={handleSendMessage} />
        </div>
    );
}
```

### Custom API Endpoint

To use a different API endpoint:

```tsx
<ChatLayout apiEndpoint="/custom/ai-endpoint">
    {children}
</ChatLayout>
```

## API Integration

The chat components expect the API endpoint to:

1. Accept POST requests with JSON body: `{ message: string }`
2. Return JSON response with: `{ response: string }`
3. Handle errors appropriately

Example API implementation:

```typescript
// pages/api/ai-agent/chat.ts
export default async function handler(req, res) {
    if (req.method !== "POST") {
        return res.status(405).json({ error: "Method not allowed" });
    }

    const { message } = req.body;
    
    try {
        // Process message with AI service
        const response = await processWithAI(message);
        res.status(200).json({ response });
    } catch (error) {
        res.status(500).json({ error: "Failed to process message" });
    }
}
```

## Environment Variables

Set the following environment variable for API communication:

```bash
NEXT_PUBLIC_VULKAN_SERVER_URL=http://localhost:3000
```

## Styling

The chat interface uses:
- Tailwind CSS for styling
- shadcn/ui components for consistency
- Radix UI primitives for accessibility
- Lucide React for icons

## Dependencies

The chat interface requires these dependencies:

- `@radix-ui/react-avatar`
- `lucide-react`
- Standard shadcn/ui components (Button, Card, Input, etc.)

## File Structure

```
src/components/chat/
├── index.ts              # Exports all components
├── chat-interface.tsx    # Main chat component
├── chat-button.tsx       # Floating action button
├── chat-provider.tsx     # Context provider
└── chat-layout.tsx       # Layout wrapper
```

## Features

- ✅ Real-time messaging interface
- ✅ Floating chat button
- ✅ Message history with timestamps
- ✅ Loading states and error handling
- ✅ Responsive design
- ✅ Keyboard shortcuts
- ✅ Auto-scrolling
- ✅ Avatar support
- ✅ Context-based API management
- ✅ TypeScript support
- ✅ Accessibility features

## Next Steps

To complete the AI agent integration:

1. Implement the backend API endpoint (`/ai-agent/chat`)
2. Connect to your AI service (OpenAI, Anthropic, etc.)
3. Add authentication if required
4. Implement conversation persistence
5. Add file upload capabilities
6. Extend with custom commands/actions
