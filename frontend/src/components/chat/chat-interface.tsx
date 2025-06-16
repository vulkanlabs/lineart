"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, User, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MessageFormatter, MessageContent } from "./message-formatter";
import { cn } from "@/lib/utils";

interface Message {
    id: string;
    content: MessageContent | string;
    sender: "user" | "agent";
    timestamp: Date;
}

interface ChatInterfaceProps {
    onSendMessage?: (message: string) => Promise<string | MessageContent>;
    className?: string;
}

export function ChatInterface({ onSendMessage, className }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "welcome",
            content:
                "Hello! I'm your Vulkan AI assistant. I can help you with policies, backtests, and " +
                "workflow management. How can I assist you today?",
            sender: "agent",
            timestamp: new Date(),
        },
    ]);
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            content: inputValue,
            sender: "user",
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputValue("");
        setIsLoading(true);

        try {
            const response = onSendMessage
                ? await onSendMessage(inputValue)
                : "I'm processing your request...";

            const agentMessage: Message = {
                id: (Date.now() + 1).toString(),
                content: response,
                sender: "agent",
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, agentMessage]);
        } catch (error) {
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                content:
                    "I apologize, but I encountered an error processing your request. Please try again.",
                sender: "agent",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    return (
        <Card className={cn("flex flex-col h-[600px]", className)}>
            <CardHeader className="pb-4 flex-shrink-0">
                <CardTitle className="flex items-center gap-3">
                    <Sparkles className="h-5 w-5" />
                    Vulkan AI Assistant
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
