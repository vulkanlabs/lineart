import { NextRequest } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;

/**
 * Proxy GET requests to backend - handles read operations
 * @param {NextRequest} request - Incoming HTTP request with headers, query params
 * @param {Object} params - Route parameters containing path segments
 * @returns {Promise<Response>} Proxied response from backend
 *
 * Forwards GET requests to backend, useful for API calls that need CORS handling
 */
export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> },
) {
    const { path } = await params;
    return handleProxyRequest(request, path, request.method);
}

/**
 * Proxy POST requests to backend - handles create operations
 * @param {NextRequest} request - HTTP request with JSON body
 * @param {Object} params - Route parameters with path segments
 * @returns {Promise<Response>} Backend response
 *
 * Creating new resources, submitting forms, API calls that need auth injection
 */
export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> },
) {
    const { path } = await params;
    return handleWriteRequest(request, path);
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> },
) {
    const { path } = await params;
    return handleWriteRequest(request, path);
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> },
) {
    const { path } = await params;
    return handleProxyRequest(request, path, request.method);
}

export async function PATCH(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> },
) {
    const { path } = await params;
    return handleWriteRequest(request, path);
}

/**
 * Handle write operations (POST, PUT, PATCH) to backend
 * @param {NextRequest} request - The incoming request with body/headers
 * @param {string[]} pathSegments - URL path parts to construct backend URL
 * @returns {Promise<Response>} Response from backend or error response
 *
 * Forwards request body, adds auth headers, handles JSON content-type
 * Returns 500 on failure with error details
 */
async function handleWriteRequest(request: NextRequest, pathSegments: string[]) {
    try {
        const path = pathSegments.join("/");
        const url = new URL(path, BACKEND_URL);

        request.nextUrl.searchParams.forEach((value, key) => {
            url.searchParams.append(key, value);
        });

        const headers = new Headers();
        headers.set("Content-Type", "application/json");

        const forwardHeaders = ["accept", "accept-language", "user-agent", "authorization"];
        forwardHeaders.forEach((header) => {
            const value = request.headers.get(header);
            if (value) headers.set(header, value);
        });

        const options: RequestInit = {
            method: request.method,
            headers,
        };

        try {
            const body = await request.json();
            options.body = JSON.stringify(body);
        } catch {
            // If not JSON, try to get raw body
            const body = await request.text();
            if (body) options.body = body;
        }

        const response = await fetch(url.toString(), options);
        const responseBody = await response.text();

        return new Response(responseBody, {
            status: response.status,
            statusText: response.statusText,
            headers: {
                "Content-Type": response.headers.get("Content-Type") || "application/json",
            },
        });
    } catch (error) {
        console.error("Proxy error:", error);
        return new Response(null, {
            status: 500,
            statusText: "Internal Server Error",
        });
    }
}

async function handleProxyRequest(request: NextRequest, pathSegments: string[], method: string) {
    try {
        const path = pathSegments.join("/");
        const url = new URL(path, BACKEND_URL);

        request.nextUrl.searchParams.forEach((value, key) => {
            url.searchParams.append(key, value);
        });

        const headers = new Headers();
        headers.set("Content-Type", "application/json");

        const forwardHeaders = ["accept", "accept-language", "user-agent", "authorization"];
        forwardHeaders.forEach((header) => {
            const value = request.headers.get(header);
            if (value) headers.set(header, value);
        });

        const response = await fetch(url.toString(), {
            method,
            headers,
        });
        const responseBody = await response.text();

        return new Response(responseBody, {
            status: response.status,
            statusText: response.statusText,
            headers: {
                "Content-Type": response.headers.get("Content-Type") || "application/json",
            },
        });
    } catch (error) {
        console.error("Proxy error:", error);
        return new Response(null, {
            status: 500,
            statusText: "Internal Server Error",
        });
    }
}
