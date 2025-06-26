"use client";

import { ReactNode } from "react";
import { ChatButton } from "./chat-button";
import { ChatProvider } from "./chat-provider";
import { PageContextProvider } from "@/lib/context";

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
        <PageContextProvider>
            <ChatProvider apiEndpoint={apiEndpoint}>
                <ChatLayoutInner>{children}</ChatLayoutInner>
            </ChatProvider>
        </PageContextProvider>
    );
}
