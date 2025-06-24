"use client";

import { createContext, useContext, ReactNode, useState, useEffect, useCallback } from "react";
import {
    agentApi,
    createChatRequest,
    isMessageContent,
    SessionResponse,
    MessageResponse,
} from "@/lib/agent-api";
import { MessageContent } from "./message-formatter";

export interface ChatMessage {
    id: string;
    content: MessageContent | string;
    sender: "user" | "agent";
    timestamp: Date;
}

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

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
    children: ReactNode;
    apiEndpoint?: string;
}

export function ChatProvider({ children, apiEndpoint }: ChatProviderProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [sessions, setSessions] = useState<SessionResponse[]>([]);

    const loadSessions = useCallback(async () => {
        try {
            const sessionList = await agentApi.listSessions();
            setSessions(sessionList);

            // If no sessions exist, create a new one
            if (sessionList.length === 0) {
                const response = await agentApi.createSession();
                setCurrentSessionId(response.id);
                await loadSessions(); // Refresh to get the new session
                return;
            }

            // If no current session and sessions exist, select the most recent one
            if (!currentSessionId && sessionList.length > 0) {
                setCurrentSessionId(sessionList[0].id);
            }
        } catch (error) {
            console.error("Error loading sessions:", error);
        }
    }, [currentSessionId]);

    const loadSessionMessages = useCallback(async (sessionId: string) => {
        try {
            const response = await agentApi.getSessionMessages(sessionId);
            const chatMessages: ChatMessage[] = response.messages.map((msg: MessageResponse) => ({
                id: msg.id.toString(),
                content: msg.content,
                sender: msg.role === "user" ? "user" : "agent",
                timestamp: new Date(msg.created_at),
            }));
            setMessages(chatMessages);
        } catch (error) {
            console.error("Error loading session messages:", error);
            setMessages([]);
        }
    }, []);

    // Load sessions on mount
    useEffect(() => {
        void loadSessions();
    }, [loadSessions]);

    // Load session messages when session changes
    useEffect(() => {
        if (currentSessionId) {
            void loadSessionMessages(currentSessionId);
        } else {
            // Clear messages when no session is selected
            setMessages([]);
        }
    }, [currentSessionId, loadSessionMessages]);

    const createNewSession = async (name?: string) => {
        try {
            const response = await agentApi.createSession({ name });
            setCurrentSessionId(response.id);
            await loadSessions(); // Refresh the sessions list
        } catch (error) {
            console.error("Error creating session:", error);
            throw new Error("Failed to create new session");
        }
    };

    const switchToSession = async (sessionId: string) => {
        setCurrentSessionId(sessionId);
    };

    const deleteSession = async (sessionId: string) => {
        try {
            await agentApi.deleteSession(sessionId);

            // If we deleted the current session, switch to another or create new
            if (sessionId === currentSessionId) {
                const remainingSessions = sessions.filter((s) => s.id !== sessionId);
                if (remainingSessions.length > 0) {
                    setCurrentSessionId(remainingSessions[0].id);
                } else {
                    setCurrentSessionId(null);
                }
            }

            await loadSessions(); // Refresh the sessions list
        } catch (error) {
            console.error("Error deleting session:", error);
            throw new Error("Failed to delete session");
        }
    };

    const sendMessage = async (message: string): Promise<string | MessageContent> => {
        setIsLoading(true);

        try {
            // Create session if none exists
            let sessionId = currentSessionId;
            if (!sessionId) {
                const response = await agentApi.createSession();
                sessionId = response.id;
                setCurrentSessionId(sessionId);
                await loadSessions();
            }

            // Send message with session ID
            const request = createChatRequest(message, sessionId);
            const response = await agentApi.sendMessage(request);

            // Add user message to local state immediately for responsiveness
            const userMessage: ChatMessage = {
                id: `user-${Date.now()}`,
                content: message,
                sender: "user",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMessage]);

            // Add agent response to local state
            const agentMessage: ChatMessage = {
                id: `agent-${Date.now()}`,
                content: response.response,
                sender: "agent",
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, agentMessage]);

            // Refresh sessions to update message count
            await loadSessions();

            return response.response;
        } catch (error) {
            console.error("Error sending message to AI agent:", error);
            throw new Error("Failed to send message. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ChatContext.Provider
            value={{
                sendMessage,
                messages,
                isLoading,
                currentSessionId,
                sessions,
                createNewSession,
                switchToSession,
                deleteSession,
                loadSessions,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
}

export function useChat() {
    const context = useContext(ChatContext);
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
}
