import { AuthApi } from "@vulkanlabs/client-open";
import { createApiConfig } from "@vulkanlabs/base";
import { useState, useEffect } from "react";

// Configure API clients with shared configuration
const apiConfig = createApiConfig({
    baseUrl: process.env.NEXT_PUBLIC_VULKAN_SERVER_URL!,
    headers: {
        "Content-Type": "application/json",
    },
});
const authApi = new AuthApi(apiConfig);

/**
 * Initiates the Google OAuth2 flow.
 * In a real implementation, this would redirect the user to Google's consent screen.
 */
export async function initiateServiceAuth(serviceName: string, projectId: string | null) {
    const headers = {
        "ngrok-skip-browser-warning": "true",
    };
    try {
        const response = await authApi.startAuth(
            {
                serviceName: serviceName,
                projectId: projectId,
            },
            {
                headers: headers,
            },
        );
        if (response.authorization_url) {
            // Open the authorization URL in a new tab
            window.open(response.authorization_url, "_blank", "noopener,noreferrer");
        } else {
            console.error("Authorization URL not found in response:", response);
            throw new Error("Authorization URL not found in response");
        }
    } catch (error) {
        console.error("Error initiating Google OAuth:", error);
        throw new Error("Error initiating Google OAuth");
    }
}

/**
 * A hook to manage Google authentication state.
 */
export function useServiceAuth(serviceName: string, projectId: string | null) {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState<{ email: string } | null>(null);
    const headers = {
        "ngrok-skip-browser-warning": "true",
    };

    const getUserInfo = async () => {
        const userInfo = await authApi.getUserInfo(
            {
                serviceName: serviceName,
                projectId: projectId,
            },
            {
                headers: headers,
            },
        );
        if (!userInfo.email) {
            throw new Error("User info not found");
        }

        return userInfo;
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
        authApi
            .disconnect({
                serviceName: serviceName,
                projectId: projectId,
            })
            .then(() => {
                setIsAuthenticated(false);
                setUser(null);
            })
            .catch((error) => {
                console.error("Error disconnecting from Google:", error);
            });
    };

    return { isAuthenticated, user, disconnect };
}
