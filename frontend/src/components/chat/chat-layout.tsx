"use client";

import { ReactNode } from "react";
import { ChatButton } from "./chat-button";
import { ChatProvider } from "./chat-provider";

interface ChatLayoutProps {
    children: ReactNode;
    apiEndpoint?: string;
}

function ChatLayoutInner({ children }: { children: ReactNode }) {
    return (
        <>
            {children}
            <ChatButton />
        </>
    );
}

export function ChatLayout({ children, apiEndpoint }: ChatLayoutProps) {
    return (
        <ChatProvider apiEndpoint={apiEndpoint}>
            <ChatLayoutInner>{children}</ChatLayoutInner>
        </ChatProvider>
    );
}
