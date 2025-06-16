import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ChatInterface } from "../chat-interface";
import { ChatButton } from "../chat-button";

// Mock the chat interface for the button test
jest.mock("../chat-interface", () => ({
    ChatInterface: ({ onSendMessage }: { onSendMessage?: Function }) => (
        <div data-testid="chat-interface">Chat Interface Mock</div>
    ),
}));

describe("Chat Components", () => {
    describe("ChatInterface", () => {
        it("renders welcome message", () => {
            render(<ChatInterface />);
            expect(screen.getByText(/Hello! I'm your Vulkan AI assistant/)).toBeInTheDocument();
        });

        it("displays user message after sending", async () => {
            const mockSendMessage = jest.fn().mockResolvedValue("Mock response");
            render(<ChatInterface onSendMessage={mockSendMessage} />);

            const input = screen.getByPlaceholderText(/Ask me about/);
            const sendButton = screen.getByRole("button", { name: /send/i });

            fireEvent.change(input, { target: { value: "Test message" } });
            fireEvent.click(sendButton);

            await waitFor(() => {
                expect(screen.getByText("Test message")).toBeInTheDocument();
            });
        });

        it("calls onSendMessage when message is sent", async () => {
            const mockSendMessage = jest.fn().mockResolvedValue("Mock response");
            render(<ChatInterface onSendMessage={mockSendMessage} />);

            const input = screen.getByPlaceholderText(/Ask me about/);
            const sendButton = screen.getByRole("button", { name: /send/i });

            fireEvent.change(input, { target: { value: "Test message" } });
            fireEvent.click(sendButton);

            await waitFor(() => {
                expect(mockSendMessage).toHaveBeenCalledWith("Test message");
            });
        });

        it("handles Enter key to send message", async () => {
            const mockSendMessage = jest.fn().mockResolvedValue("Mock response");
            render(<ChatInterface onSendMessage={mockSendMessage} />);

            const input = screen.getByPlaceholderText(/Ask me about/);

            fireEvent.change(input, { target: { value: "Test message" } });
            fireEvent.keyPress(input, { key: "Enter", code: "Enter", charCode: 13 });

            await waitFor(() => {
                expect(mockSendMessage).toHaveBeenCalledWith("Test message");
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
