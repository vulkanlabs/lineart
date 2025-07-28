// @frontend/packages/base/src/auth/google-oauth.ts

/**
 * Initiates the Google OAuth2 flow.
 * In a real implementation, this would redirect the user to Google's consent screen.
 */
export async function initiateGoogleOAuth() {
    console.log("Initiating Google OAuth flow...");
    try {
        const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
        const response = await fetch(`${baseUrl}/auth/google/start`, {
            headers: { "ngrok-skip-browser-warning": "true" },
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.authorization_url) {
            // Open the authorization URL in a new tab
            // The redirect URI now points to the backend, which will redirect to the frontend
            window.open(data.authorization_url, "_blank", "noopener,noreferrer");
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
        // Check for existing tokens on mount
        const tokens = localStorage.getItem("google_oauth_tokens");
        const userInfo = localStorage.getItem("google_user_info");

        if (tokens && userInfo) {
            try {
                const parsedUserInfo = JSON.parse(userInfo);
                setIsAuthenticated(true);
                setUser({ email: parsedUserInfo.email });
            } catch (error) {
                console.error("Error parsing stored user info:", error);
                // Clear invalid data
                localStorage.removeItem("google_oauth_tokens");
                localStorage.removeItem("google_user_info");
            }
        }

        // Handle OAuth redirect with URL parameters
        const params = new URLSearchParams(window.location.search);
        const authSuccess = params.get("auth_success");
        const authError = params.get("auth_error");
        const tokensParam = params.get("tokens");

        if (authSuccess === "true" && tokensParam) {
            try {
                // Decode and save tokens
                const decodedTokens = JSON.parse(atob(tokensParam));
                localStorage.setItem("google_oauth_tokens", JSON.stringify(decodedTokens));

                // Get user info using the access token
                fetch("https://www.googleapis.com/oauth2/v2/userinfo", {
                    headers: {
                        Authorization: `Bearer ${decodedTokens.access_token}`,
                    },
                })
                    .then((response) => response.json())
                    .then((userInfo) => {
                        localStorage.setItem("google_user_info", JSON.stringify(userInfo));
                        setIsAuthenticated(true);
                        setUser({ email: userInfo.email });
                    })
                    .catch((error) => {
                        console.error("Error fetching user info:", error);
                    });

                // Clean up URL
                params.delete("auth_success");
                params.delete("tokens");
                const newUrl = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`;
                window.history.replaceState({}, document.title, newUrl);
            } catch (error) {
                console.error("Error processing OAuth tokens:", error);
            }
        } else if (authError) {
            console.error("OAuth error:", authError);
            // Clean up URL
            params.delete("auth_error");
            const newUrl = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ""}`;
            window.history.replaceState({}, document.title, newUrl);
        }
    }, []);

    const disconnect = () => {
        console.log("Disconnecting from Google...");
        setIsAuthenticated(false);
        setUser(null);
        // Clear stored tokens and user info
        localStorage.removeItem("google_oauth_tokens");
        localStorage.removeItem("google_user_info");
    };

    return { isAuthenticated, user, disconnect };
}

/**
 * Gets the stored Google OAuth tokens.
 * @returns The tokens object or null if not available
 */
export function getGoogleTokens(): {
    access_token: string;
    refresh_token?: string;
    expires_in?: number;
} | null {
    try {
        const tokens = localStorage.getItem("google_oauth_tokens");
        return tokens ? JSON.parse(tokens) : null;
    } catch (error) {
        console.error("Error parsing stored tokens:", error);
        return null;
    }
}

/**
 * Gets the stored Google user information.
 * @returns The user info object or null if not available
 */
export function getGoogleUserInfo(): { email: string; name?: string; picture?: string } | null {
    try {
        const userInfo = localStorage.getItem("google_user_info");
        return userInfo ? JSON.parse(userInfo) : null;
    } catch (error) {
        console.error("Error parsing stored user info:", error);
        return null;
    }
}
