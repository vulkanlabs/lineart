"use client";

import { ChatInterface, ChatProvider } from "@/components/chat";

export default function ChatPage() {
    return (
        <div className="container mx-auto p-6">
            <div className="mb-6">
                <h1 className="text-3xl font-bold">AI Assistant</h1>
                <p className="text-muted-foreground">
                    Chat with your Vulkan AI assistant. Sessions are automatically saved and you can
                    switch between different conversations.
                </p>
            </div>

            <ChatProvider>
                <ChatInterface className="h-[700px]" showSessionControls={true} />
            </ChatProvider>
        </div>
    );
}
