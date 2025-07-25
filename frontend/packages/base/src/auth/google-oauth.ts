// @frontend/packages/base/src/auth/google-oauth.ts

/**
 * Initiates the Google OAuth2 flow.
 * In a real implementation, this would redirect the user to Google's consent screen.
 */
export async function initiateGoogleOAuth() {
    console.log("Initiating Google OAuth flow...");
    try {
        const response = await fetch("/api/v1/auth/google/start");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.authorization_url) {
            window.location.href = data.authorization_url;
        } else {
            console.error("Authorization URL not found in response:", data);
            alert("Failed to get authorization URL.");
        }
    } catch (error) {
        console.error("Error initiating Google OAuth:", error);
        alert("Error initiating OAuth flow.");
    }
}

import { useState, useEffect } from "react";

/**
 * A hook to manage Google authentication state.
 */
export function useGoogleAuth() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<{ email: string } | null>(null);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const authStatus = params.get("auth_status");

        if (authStatus === "success") {
            setIsAuthenticated(true);
            setUser({ email: "test.user@example.com" }); // Placeholder user
            // Clean up the URL to remove the auth_status parameter
            params.delete("auth_status");
            window.history.replaceState({}, document.title, `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`);
        }
    }, []);

    const disconnect = () => {
        console.log("Disconnecting from Google...");
        setIsAuthenticated(false);
        setUser(null);
        alert("Disconnected! (Placeholder)");
    };

    return { isAuthenticated, user, disconnect };
}
