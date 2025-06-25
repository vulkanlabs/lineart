"use client";

import React from "react";
import { MessageFormatter } from "@/components/chat/message-formatter";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, User } from "lucide-react";

interface TestMessage {
    id: string;
    sender: "user" | "agent";
    timestamp: Date;
    content: any;
    description: string;
}

export default function MessageTestPage() {
    const testMessages: TestMessage[] = [
        {
            id: "1",
            sender: "user",
            timestamp: new Date(),
            content: "Hello! Can you show me different types of responses?",
            description: "Simple text message (auto-markdown)",
        },
        {
            id: "2",
            sender: "agent",
            timestamp: new Date(),
            content: `# Welcome! I can show you various message types

Here's a **comprehensive overview** of what I can display:

## Text Formatting
- **Bold text** and *italic text*
- \`Inline code\` snippets
- [External links](https://github.com)
- ~~Strikethrough text~~

## Lists
1. Ordered lists
2. With multiple items
3. And proper numbering

- Unordered lists
- With bullet points
- And nested items
  - Like this one
  - And this one

## Blockquotes
> This is a blockquote with important information
> It can span multiple lines

## Tables
| Feature | Status | Notes |
|---------|--------|-------|
| Markdown | ✅ | Full GFM support |
| Syntax Highlighting | ✅ | Multiple languages |
| JSON Auto-detection | ✅ | Pretty printing |`,
            description: "Rich markdown content with tables, lists, and formatting",
        },
        {
            id: "3",
            sender: "user",
            timestamp: new Date(),
            content: "Can you show me some code examples?",
            description: "User request for code",
        },
        {
            id: "4",
            sender: "agent",
            timestamp: new Date(),
            content: `Here are some code examples:

## JavaScript Example
\`\`\`javascript
function greetUser(name) {
    console.log(\`Hello, \${name}!\`);
    return {
        message: "Welcome to our app",
        timestamp: new Date(),
        user: name
    };
}

const result = greetUser("Alice");
\`\`\`

## Python Example
\`\`\`python
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Generate first 10 fibonacci numbers
numbers = [calculate_fibonacci(i) for i in range(10)]
print(f"Fibonacci sequence: {numbers}")
\`\`\`

## SQL Example
\`\`\`sql
SELECT u.name, u.email, p.title
FROM users u
JOIN posts p ON u.id = p.author_id
WHERE p.created_at > '2024-01-01'
ORDER BY p.created_at DESC
LIMIT 10;
\`\`\``,
            description: "Code blocks with syntax highlighting",
        },
        {
            id: "5",
            sender: "user",
            timestamp: new Date(),
            content:
                '{"name": "John Doe", "age": 30, "skills": ["JavaScript", "Python", "React"], ' +
                '"address": {"city": "New York", "zipcode": "10001"}}',
            description: "Raw JSON string (auto-detected and formatted)",
        },
        {
            id: "6",
            sender: "agent",
            timestamp: new Date(),
            content: {
                type: "list",
                content: [
                    "Machine Learning fundamentals",
                    "Data preprocessing techniques",
                    "Model training and validation",
                    "Feature engineering best practices",
                    "Performance optimization strategies",
                ],
            },
            description: "List message type",
        },
        {
            id: "7",
            sender: "agent",
            timestamp: new Date(),
            content: {
                type: "preview",
                content: {
                    title: "Data Analysis Report",
                    description: "Summary of the latest data processing pipeline results",
                    items: [
                        { label: "Records Processed", value: "1,234,567", type: "text" },
                        { label: "Success Rate", value: "99.2%", type: "badge" },
                        { label: "Processing Time", value: "2.3 seconds", type: "text" },
                        { label: "Output Format", value: "JSON", type: "code" },
                        { label: "Status", value: "Complete", type: "badge" },
                    ],
                    actions: [
                        { label: "Download", action: "download", variant: "default" },
                        { label: "View Details", action: "view", variant: "outline" },
                        { label: "Share", action: "share", variant: "outline" },
                    ],
                },
            },
            description: "Preview message type with metadata and actions",
        },
        {
            id: "8",
            sender: "agent",
            timestamp: new Date(),
            content: {
                type: "code",
                content: {
                    language: "typescript",
                    title: "API Response Interface",
                    code: `interface ApiResponse<T> {
    data: T;
    status: 'success' | 'error';
    message?: string;
    timestamp: Date;
    meta?: {
        total: number;
        page: number;
        limit: number;
    };
}

// Usage example
const response: ApiResponse<User[]> = {
    data: users,
    status: 'success',
    timestamp: new Date(),
    meta: {
        total: 150,
        page: 1,                        limit: 20
                    }
                };`,
                },
            },
            description: "Code message type with title",
        },
        {
            id: "9",
            sender: "agent",
            timestamp: new Date(),
            content: {
                type: "success",
                content:
                    "Your data has been successfully processed and saved to the database. " +
                    "All 1,234 records were imported without any errors.",
            },
            description: "Success message type",
        },
        {
            id: "10",
            sender: "agent",
            timestamp: new Date(),
            content: {
                type: "error",
                content:
                    "Failed to connect to the external API. Please check your network " +
                    "connection and try again. Error code: NETWORK_TIMEOUT",
            },
            description: "Error message type",
        },
        {
            id: "11",
            sender: "agent",
            timestamp: new Date(),
            content: {
                type: "info",
                content:
                    "This feature is currently in beta. Some functionality may be limited. " +
                    "Your feedback helps us improve the experience.",
            },
            description: "Info message type",
        },
        {
            id: "12",
            sender: "user",
            timestamp: new Date(),
            content: `Can you show me a complex JSON structure?`,
            description: "User request for complex JSON",
        },
        {
            id: "13",
            sender: "agent",
            timestamp: new Date(),
            content: `Here's a complex JSON structure example:

\`\`\`json
{
  "user": {
    "id": "usr_12345",
    "profile": {
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "avatar": "https://example.com/avatar.jpg",
      "preferences": {
        "theme": "dark",
        "notifications": {
          "email": true,
          "push": false,
          "sms": true
        },
        "privacy": {
          "profile_visibility": "friends",
          "activity_tracking": false
        }
      }
    },
    "subscription": {
      "plan": "premium",
      "status": "active",
      "billing": {
        "amount": 29.99,
        "currency": "USD",
        "interval": "monthly",
        "next_billing_date": "2024-07-24T10:00:00Z"
      },
      "features": [
        "unlimited_storage",
        "priority_support",
        "advanced_analytics",
        "custom_integrations"
      ]
    },
    "recent_activity": [
      {
        "type": "login",
        "timestamp": "2024-06-24T09:30:00Z",
        "location": "New York, NY",
        "device": "iPhone 15 Pro"
      },
      {
        "type": "file_upload",
        "timestamp": "2024-06-24T09:15:00Z",
        "file_name": "report_q2_2024.pdf",
        "file_size": 2048576
      }
    ]
  }
}
\`\`\``,
            description: "Complex nested JSON with syntax highlighting",
        },
    ];

    const formatTimestamp = (date: Date) => {
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    };

    return (
        <div className="min-h-screen bg-background p-8">
            <div className="max-w-4xl mx-auto">
                <Card className="mb-8">
                    <CardHeader>
                        <CardTitle className="text-2xl font-bold">
                            Message Formatter Test Suite
                        </CardTitle>
                        <p className="text-muted-foreground">
                            Visual test of all implemented message types and rendering capabilities
                        </p>
                    </CardHeader>
                </Card>

                <div className="space-y-6">
                    {testMessages.map((message) => (
                        <Card key={message.id} className="overflow-hidden">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <Avatar className="h-8 w-8">
                                            {message.sender === "agent" ? (
                                                <>
                                                    <AvatarImage src="/vulkan-light.png" />
                                                    <AvatarFallback>
                                                        <Bot className="h-4 w-4" />
                                                    </AvatarFallback>
                                                </>
                                            ) : (
                                                <AvatarFallback>
                                                    <User className="h-4 w-4" />
                                                </AvatarFallback>
                                            )}
                                        </Avatar>
                                        <div>
                                            <div className="font-medium">
                                                {message.sender === "agent"
                                                    ? "AI Assistant"
                                                    : "User"}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                {formatTimestamp(message.timestamp)}
                                            </div>
                                        </div>
                                    </div>
                                    <Badge variant="outline" className="text-xs">
                                        {message.description}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <MessageFormatter content={message.content} />
                            </CardContent>
                        </Card>
                    ))}
                </div>

                <Card className="mt-8">
                    <CardContent className="pt-6">
                        <h3 className="font-semibold mb-4">Test Summary</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <div className="font-medium">String Messages</div>
                                <div className="text-muted-foreground">Auto-markdown</div>
                            </div>
                            <div>
                                <div className="font-medium">Code Blocks</div>
                                <div className="text-muted-foreground">Syntax highlighting</div>
                            </div>
                            <div>
                                <div className="font-medium">JSON Detection</div>
                                <div className="text-muted-foreground">Auto-formatting</div>
                            </div>
                            <div>
                                <div className="font-medium">Typed Messages</div>
                                <div className="text-muted-foreground">Rich components</div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
