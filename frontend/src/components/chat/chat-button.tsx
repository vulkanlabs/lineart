"use client";

import { useState } from "react";
import { Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInterface } from "./chat-interface";
import { cn } from "@/lib/utils";

interface ChatButtonProps {
    className?: string;
}

export function ChatButton({ className }: ChatButtonProps) {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className={cn("fixed bottom-4 right-4 z-50", className)}>
            {isOpen ? (
                <div className="relative">
                    <ChatInterface className="w-[26rem]" showSessionControls={true} />
                    <Button
                        onClick={() => setIsOpen(false)}
                        size="icon"
                        variant="outline"
                        className="absolute -top-2 -right-2 h-6 w-6 rounded-full"
                    >
                        <X className="h-3 w-3" />
                    </Button>
                </div>
            ) : (
                <Button
                    onClick={() => setIsOpen(true)}
                    size="icon"
                    className="h-12 w-12 rounded-full shadow-lg hover:shadow-xl transition-shadow"
                >
                    <Sparkles className="h-6 w-6" />
                </Button>
            )}
        </div>
    );
}
