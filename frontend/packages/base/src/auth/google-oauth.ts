/**
 * Initiates the Google OAuth2 flow.
 * In a real implementation, this would redirect the user to Google's consent screen.
 */
export async function initiateGoogleOAuth() {
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
            throw new Error("Authorization URL not found in response");
        }
    } catch (error) {
        console.error("Error initiating Google OAuth:", error);
        throw new Error("Error initiating Google OAuth");
    }
}

import { useState, useEffect } from "react";

/**
 * A hook to manage Google authentication state.
 */
export function useGoogleAuth() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<{ email: string } | null>(null);

    const baseUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
    const getUserInfo = async () => {
        const userInfo = await fetch(`${baseUrl}/auth/google/user_info`, {
            headers: { "ngrok-skip-browser-warning": "true" },
        });
        const userInfoData = await userInfo.json();
        if (!userInfoData || !userInfoData.email) {
            throw new Error("User info not found");
        }
        console.log("User info:", userInfoData);

        return userInfoData;
    };

    useEffect(() => {
        getUserInfo()
            .then((userInfoData) => {
                setUser({ email: userInfoData.email });
                setIsAuthenticated(true);
            })
            .catch((error) => {
                console.warn("Failed to fetch user info:", error);
            });
    }, []);

    const disconnect = () => {
        fetch(`${baseUrl}/auth/google/disconnect`, {
            method: "POST",
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            })
            .catch((error) => {
                console.error("Error disconnecting from Google:", error);
            });
        setIsAuthenticated(false);
        setUser(null);
    };

    return { isAuthenticated, user, disconnect };
}
