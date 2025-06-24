# Frontend Chat Interface

This document describes the chat interface implementation for the Vulkan platform's AI assistant with session management.

## Components

### 1. ChatInterface

The main chat interface component that displays messages and handles user input with session management.

**Location:** `src/components/chat/chat-interface.tsx`

**Props:**

-   `className?: string` - Additional CSS classes
-   `showSessionControls?: boolean` - Whether to show session controls in the header (default: true)

**Features:**

-   Message history with timestamps
-   User and agent avatars  
-   Loading indicators
-   Auto-scrolling to latest messages
-   Keyboard shortcuts (Enter to send)
-   **Clean Session Management:**
    - Single menu button in header (Menu icon)
    - All session functionality in one organized dropdown
    - No layout shifts or header crowding
    - Create new sessions, switch between sessions, manage individual sessions
    - Current session name displayed in header
    - Minimal visual footprint

### 2. ChatButton

A floating action button that opens/closes the chat interface.

**Location:** `src/components/chat/chat-button.tsx`

**Props:**

-   `className?: string` - Additional CSS classes

**Features:**

-   Fixed positioning (bottom-right corner)
-   Expandable chat interface with full session support
-   **Always available**: Session controls are enabled by default
-   Close button when opened
-   Uses ChatProvider context automatically
-   **Clean interface**: Single menu button for all session management

### 3. ChatProvider

Context provider for managing chat API calls, state, and session persistence.

**Location:** `src/components/chat/chat-provider.tsx`

**Props:**

-   `children: ReactNode` - Child components
-   `apiEndpoint?: string` - Custom API endpoint (defaults to vulkan-agent service)

**Context Value:**

```tsx
interface ChatContextType {
    // Chat functionality
    sendMessage: (message: string) => Promise<string | MessageContent>;
    messages: ChatMessage[];
    isLoading: boolean;

    // Session management
    currentSessionId: string | null;
    sessions: SessionResponse[];
    createNewSession: (name?: string) => Promise<void>;
    switchToSession: (sessionId: string) => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
    loadSessions: () => Promise<void>;
}
```

**Features:**

-   **Session Management**: Automatic session creation, switching, and persistence
-   **Message Persistence**: Messages are stored on the server and restored when switching sessions
-   **Centralized API Communication**: All chat and session API calls
-   **Error Handling**: Robust error handling with user feedback
-   **Auto-loading**: Sessions and messages are loaded automatically

### 4. ChatLayout

Layout wrapper that automatically includes the floating chat button with session support.

**Location:** `src/components/chat/chat-layout.tsx`

**Props:**

-   `children: ReactNode` - Child components
-   `apiEndpoint?: string` - Custom API endpoint

**Features:**

-   Automatic chat provider setup
-   Floating chat button integration
-   Session persistence across page navigation

## Final Design: Single Menu Button Approach

### Clean Header Design
- **Single menu button**: Only one small menu button (Menu icon) when session controls are enabled
- **No crowding**: Header maintains clean appearance with minimal visual elements
- **Stable layout**: Header size never changes regardless of session state
- **Intuitive icon**: Menu icon clearly indicates dropdown functionality

### Organized Menu Structure
- **New Session**: Quick access at the top of the menu
- **Session List**: All sessions displayed with names and message counts
- **Individual Actions**: Each session has its own context menu for deletion
- **Current Session Highlight**: Active session is visually distinguished

### Enhanced User Experience
- **Always available**: Session controls are enabled by default across all interfaces
- **No toggles needed**: Simple, consistent behavior
- **Responsive design**: Works well in both floating chat button and full-page modes
- **No viewport issues**: Clean design stays within bounds on all screen sizes

## Session Management

The chat interface supports persistent conversation sessions:

- **Automatic Session Creation**: A new session is created when the user first sends a message
- **Session Persistence**: All messages are stored on the server and restored when switching sessions
- **Session List**: View all conversation sessions with names and message counts in a compact dropdown
- **Session Switching**: Click on any session to continue that conversation
- **Session Management**: Delete sessions you no longer need via the dropdown menu
- **Fresh Start**: Create a new session or delete the current one to start a fresh conversation

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
```
### Full Chat Page

For a dedicated chat page with full session controls:

```tsx
// pages/chat.tsx or app/chat/page.tsx
import { ChatInterface, ChatProvider } from "@/components/chat";

export default function ChatPage() {
    return (
        <div className="container mx-auto p-6">
            <h1 className="text-3xl font-bold mb-6">AI Assistant</h1>
            
            <ChatProvider>
                {/* Enable session controls for full-page experience */}
                <ChatInterface className="h-[700px]" showSessionControls={true} />
            </ChatProvider>
        </div>
    );
}
```

### Floating Chat with Session Controls

The floating chat button now includes session controls by default:

```tsx
import { ChatLayout } from "@/components/chat";

export default function RootLayout({ children }) {
    return (
        <ChatLayout>
            {/* Chat button has session controls enabled by default */}
            {/* Clean single-menu design with Menu icon */}
            {children}
        </ChatLayout>
    );
}
```

### Custom API Endpoint

To use a different API endpoint:

```tsx
<ChatLayout apiEndpoint="/custom/ai-endpoint">{children}</ChatLayout>
```

### Using Chat Context

Access chat functionality and session management in custom components:

```tsx
import { useChat } from "@/components/chat";

export function CustomChatComponent() {
    const { 
        sendMessage, 
        messages, 
        currentSessionId, 
        sessions,
        createNewSession,
        switchToSession 
    } = useChat();

    return (
        <div>
            <h2>Current Session: {currentSessionId}</h2>
            <p>Total Sessions: {sessions.length}</p>
            <button onClick={() => createNewSession("My Custom Session")}>
                New Session
            </button>
        </div>
    );
}
```

## API Integration

The chat components now integrate with the vulkan-agent service which supports:

### Chat API
- **POST** `/api/chat/message` - Send a message with optional session_id

### Session API  
- **POST** `/api/sessions` - Create a new session
- **GET** `/api/sessions` - List all sessions
- **GET** `/api/sessions/{session_id}` - Get session details
- **GET** `/api/sessions/{session_id}/messages` - Get session messages
- **DELETE** `/api/sessions/{session_id}` - Delete a session

### Request/Response Formats

**Chat Message Request:**
```json
{
  "message": "Hello, how can you help me?",
  "session_id": "optional-session-id"
}
```

**Chat Message Response:**
```json
{
  "response": "I can help you with policies, workflows, and more!",
  "session_id": "session-uuid",
  "tools_used": false
}
```

**Session Response:**
```json
{
  "id": "session-uuid",
  "name": "Session 2024-06-24 10:30",
  "created_at": "2024-06-24T10:30:00Z",
  "message_count": 5
}
```
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

-   Tailwind CSS for styling
-   shadcn/ui components for consistency
-   Radix UI primitives for accessibility
-   Lucide React for icons

## Dependencies

The chat interface requires these dependencies:

-   `@radix-ui/react-avatar`
-   `lucide-react`
-   Standard shadcn/ui components (Button, Card, Input, etc.)

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

-   ✅ Real-time messaging interface
-   ✅ Floating chat button
-   ✅ Message history with timestamps
-   ✅ Loading states and error handling
-   ✅ Responsive design
-   ✅ Keyboard shortcuts
-   ✅ Auto-scrolling
-   ✅ Avatar support
-   ✅ Context-based API management
-   ✅ TypeScript support
-   ✅ Accessibility features

## Next Steps

To complete the AI agent integration:

1. Implement the backend API endpoint (`/ai-agent/chat`)
2. Connect to your AI service (OpenAI, Anthropic, etc.)
3. Add authentication if required
4. Implement conversation persistence
5. Add file upload capabilities
6. Extend with custom commands/actions
