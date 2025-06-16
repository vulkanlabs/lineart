"use client";

import { createContext, useContext, ReactNode } from "react";
import { agentApi, createChatRequest, isMessageContent } from "@/lib/agent-api";
import { MessageContent } from "./message-formatter";

interface ChatContextType {
    sendMessage: (message: string) => Promise<string | MessageContent>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
    children: ReactNode;
    apiEndpoint?: string;
}

export function ChatProvider({ children, apiEndpoint }: ChatProviderProps) {
    const sendMessage = async (message: string): Promise<string | MessageContent> => {
        try {
            // Use the agent API client
            const request = createChatRequest(message);
            const response = await agentApi.sendMessage(request);

            // Return the response content (can be string or MessageContent)
            return response.response;
        } catch (error) {
            console.error("Error sending message to AI agent:", error);
            throw new Error("Failed to send message. Please try again.");
        }
    };

    return <ChatContext.Provider value={{ sendMessage }}>{children}</ChatContext.Provider>;
}

export function useChat() {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
}
