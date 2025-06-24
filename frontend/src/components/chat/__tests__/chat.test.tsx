import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ChatInterface } from "../chat-interface";
import { ChatButton } from "../chat-button";
import { ChatProvider } from "../chat-provider";

// Mock the agent API
jest.mock("@/lib/agent-api", () => ({
    agentApi: {
        listSessions: jest.fn().mockResolvedValue([
            {
                id: "session-1",
                name: "Test Session",
                created_at: "2024-01-01T00:00:00Z",
                message_count: 1,
            },
        ]),
        getSessionMessages: jest.fn().mockResolvedValue({
            messages: [
                {
                    id: 1,
                    role: "assistant",
                    content:
                        "Hello! I'm your Vulkan AI assistant. I can help you with policies, " +
                        "backtests, and workflow management. How can I assist you today?",
                    created_at: "2024-01-01T00:00:00Z",
                },
            ],
        }),
        createSession: jest.fn().mockResolvedValue({
            id: "new-session-1",
            name: "New Session",
        }),
        sendMessage: jest.fn().mockResolvedValue({
            response: "Mock response",
        }),
    },
    createChatRequest: jest.fn(),
    isMessageContent: jest.fn().mockReturnValue(false),
}));

// Mock the chat interface for the button test
jest.mock("../chat-interface", () => ({
    ChatInterface: () => <div data-testid="chat-interface">Chat Interface Mock</div>,
}));

describe("Chat Components", () => {
    describe("ChatInterface", () => {
        it("renders greeting message from server", async () => {
            render(
                <ChatProvider>
                    <ChatInterface />
                </ChatProvider>,
            );

            await waitFor(() => {
                expect(screen.getByText(/Hello! I'm your Vulkan AI assistant/)).toBeInTheDocument();
            });
        });
    });

    describe("ChatButton", () => {
        it("renders chat button initially", () => {
            render(<ChatButton />);
            expect(screen.getByRole("button")).toBeInTheDocument();
        });

        it("opens chat interface when clicked", () => {
            render(<ChatButton />);
            const button = screen.getByRole("button");

            fireEvent.click(button);

            expect(screen.getByTestId("chat-interface")).toBeInTheDocument();
        });

        it("shows close button when chat is open", () => {
            render(<ChatButton />);
            const openButton = screen.getByRole("button");

            fireEvent.click(openButton);

            const closeButton = screen.getByRole("button", { name: /close/i });
            expect(closeButton).toBeInTheDocument();
        });

        it("closes chat interface when close button is clicked", () => {
            render(<ChatButton />);
            const openButton = screen.getByRole("button");

            // Open chat
            fireEvent.click(openButton);
            expect(screen.getByTestId("chat-interface")).toBeInTheDocument();

            // Close chat
            const closeButton = screen.getByRole("button", { name: /close/i });
            fireEvent.click(closeButton);

            expect(screen.queryByTestId("chat-interface")).not.toBeInTheDocument();
        });
    });
});
