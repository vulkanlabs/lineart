"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, User, Loader2, Plus, Trash2, Menu, MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { MessageFormatter, MessageContent } from "./message-formatter";
import { useChat, ChatMessage } from "./chat-provider";
import { cn } from "@/lib/utils";

interface ChatInterfaceProps {
    className?: string;
    showSessionControls?: boolean;
}

export function ChatInterface({ className, showSessionControls = true }: ChatInterfaceProps) {
    const {
        sendMessage,
        messages,
        isLoading,
        currentSessionId,
        sessions,
        createNewSession,
        switchToSession,
        deleteSession,
    } = useChat();

    const [inputValue, setInputValue] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const messageText = inputValue;
        setInputValue("");

        try {
            await sendMessage(messageText);
        } catch (error) {
            console.error("Error sending message:", error);
            // Error handling is already done in the provider
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const handleNewSession = async () => {
        try {
            await createNewSession();
        } catch (error) {
            console.error("Error creating new session:", error);
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        if (window.confirm("Are you sure you want to delete this session?")) {
            try {
                await deleteSession(sessionId);
            } catch (error) {
                console.error("Error deleting session:", error);
            }
        }
    };

    return (
        <Card className={cn("flex flex-col h-[600px]", className)}>
            <CardHeader className="pb-4 flex-shrink-0">
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Sparkles className="h-5 w-5" />
                        <div className="flex flex-col gap-1">
                            <span>Vulkan AI Assistant</span>
                            {currentSessionId && (
                                <span className="text-xs text-muted-foreground font-normal">
                                    {sessions.find((s) => s.id === currentSessionId)?.name ||
                                        "Current Session"}
                                </span>
                            )}
                        </div>
                    </div>

                    {showSessionControls && (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button size="sm" variant="outline">
                                    <Menu className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuItem onClick={handleNewSession}>
                                    <Plus className="h-4 w-4 mr-2" />
                                    New Session
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                {sessions.length > 0 && (
                                    <>
                                        <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                                            Switch Session
                                        </div>
                                        <div className="max-h-48 overflow-y-auto">
                                            {sessions.map((session) => (
                                                <div key={session.id} className="relative">
                                                    <DropdownMenuItem
                                                        onClick={() => switchToSession(session.id)}
                                                        className={cn(
                                                            "flex items-center justify-between pr-8",
                                                            session.id === currentSessionId &&
                                                                "bg-accent",
                                                        )}
                                                    >
                                                        <div className="flex-1 min-w-0">
                                                            <div className="text-sm font-medium truncate">
                                                                {session.name}
                                                            </div>
                                                            <div className="text-xs text-muted-foreground">
                                                                {session.message_count} messages
                                                            </div>
                                                        </div>
                                                    </DropdownMenuItem>
                                                    <div className="absolute right-2 top-1/2 -translate-y-1/2">
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger asChild>
                                                                <Button
                                                                    size="sm"
                                                                    variant="ghost"
                                                                    className="h-6 w-6 p-0"
                                                                    onClick={(e) =>
                                                                        e.stopPropagation()
                                                                    }
                                                                >
                                                                    <MoreHorizontal className="h-3 w-3" />
                                                                </Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end">
                                                                <DropdownMenuItem
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleDeleteSession(
                                                                            session.id,
                                                                        );
                                                                    }}
                                                                    className="text-destructive"
                                                                >
                                                                    <Trash2 className="h-3 w-3 mr-2" />
                                                                    Delete Session
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        <DropdownMenuSeparator />
                                    </>
                                )}
                            </DropdownMenuContent>
                        </DropdownMenu>
                    )}
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
                <div className="flex-1 overflow-y-auto px-4 min-h-0">
                    <div className="space-y-4 py-4">
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={cn(
                                    "flex gap-3",
                                    message.sender === "user" ? "justify-end" : "justify-start",
                                )}
                            >
                                {message.sender === "agent" && (
                                    <Avatar className="h-8 w-8">
                                        <AvatarFallback>
                                            <Sparkles className="h-4 w-4" />
                                        </AvatarFallback>
                                    </Avatar>
                                )}
                                <div
                                    className={cn(
                                        "rounded-lg px-3 py-2 max-w-[80%]",
                                        message.sender === "user"
                                            ? "bg-primary text-primary-foreground"
                                            : "bg-muted",
                                    )}
                                >
                                    <MessageFormatter content={message.content} />
                                    <span className="text-xs opacity-70 mt-1 block">
                                        {message.timestamp.toLocaleTimeString()}
                                    </span>
                                </div>
                                {message.sender === "user" && (
                                    <Avatar className="h-8 w-8">
                                        <AvatarFallback>
                                            <User className="h-4 w-4" />
                                        </AvatarFallback>
                                    </Avatar>
                                )}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex gap-3">
                                <Avatar className="h-8 w-8">
                                    <AvatarFallback>
                                        <Sparkles className="h-4 w-4" />
                                    </AvatarFallback>
                                </Avatar>
                                <div className="bg-muted rounded-lg px-3 py-2">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>
                <div className="border-t p-4 flex-shrink-0">
                    <div className="flex gap-2">
                        <Input
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask me about your policies, workflows, or anything else..."
                            disabled={isLoading}
                            className="flex-1"
                        />
                        <Button
                            onClick={handleSendMessage}
                            disabled={isLoading || !inputValue.trim()}
                            size="icon"
                        >
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
