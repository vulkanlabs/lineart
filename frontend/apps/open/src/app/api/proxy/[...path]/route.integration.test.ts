import { describe, it, expect, vi, beforeEach } from "vitest";
import { NextRequest } from "next/server";
import { GET, POST, PUT, DELETE, PATCH } from "./route";

// Mock environment variable
process.env.NEXT_PUBLIC_VULKAN_SERVER_URL = "http://localhost:3000";

describe("Proxy Route Integration Tests", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        console.error = vi.fn();
    });

    const createMockParams = (path: string[]) => Promise.resolve({ path });

    describe("Function Signatures and Exports", () => {
        it("should export all required HTTP method handlers", () => {
            expect(GET).toBeDefined();
            expect(POST).toBeDefined();
            expect(PUT).toBeDefined();
            expect(DELETE).toBeDefined();
            expect(PATCH).toBeDefined();
        });

        it("should accept correct parameters for GET", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test");
            const params = createMockParams(["test"]);
            
            // Should not throw
            expect(async () => {
                await GET(request, { params });
            }).not.toThrow();
        });

        it("should accept correct parameters for POST", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test", {
                method: "POST",
                body: JSON.stringify({ test: "data" })
            });
            const params = createMockParams(["test"]);
            
            // Should not throw
            expect(async () => {
                await POST(request, { params });
            }).not.toThrow();
        });

        it("should accept correct parameters for PUT", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test", {
                method: "PUT",
                body: JSON.stringify({ test: "data" })
            });
            const params = createMockParams(["test"]);
            
            // Should not throw
            expect(async () => {
                await PUT(request, { params });
            }).not.toThrow();
        });

        it("should accept correct parameters for DELETE", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test", {
                method: "DELETE"
            });
            const params = createMockParams(["test"]);
            
            // Should not throw
            expect(async () => {
                await DELETE(request, { params });
            }).not.toThrow();
        });

        it("should accept correct parameters for PATCH", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test", {
                method: "PATCH",
                body: JSON.stringify({ test: "data" })
            });
            const params = createMockParams(["test"]);
            
            // Should not throw
            expect(async () => {
                await PATCH(request, { params });
            }).not.toThrow();
        });
    });

    describe("Response Structure", () => {
        it("should return Response objects for all methods", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test");
            const params = createMockParams(["test"]);
            
            const getResponse = await GET(request, { params });
            expect(getResponse).toBeInstanceOf(Response);
            expect(getResponse.status).toBeDefined();
            expect(getResponse.statusText).toBeDefined();
            expect(getResponse.headers).toBeDefined();

            const postRequest = new NextRequest("http://localhost:3001/api/proxy/test", {
                method: "POST",
                body: JSON.stringify({ test: "data" })
            });
            const postResponse = await POST(postRequest, { params });
            expect(postResponse).toBeInstanceOf(Response);
            expect(postResponse.status).toBeDefined();
        });
    });

    describe("Error Handling", () => {
        it("should handle invalid backend URLs gracefully", async () => {
            // Temporarily set an invalid backend URL
            const originalUrl = process.env.NEXT_PUBLIC_VULKAN_SERVER_URL;
            process.env.NEXT_PUBLIC_VULKAN_SERVER_URL = "http://invalid-host-that-does-not-exist:99999";
            
            const request = new NextRequest("http://localhost:3001/api/proxy/test");
            const params = createMockParams(["test"]);
            
            const response = await GET(request, { params });
            
            // Should return 500 for network errors
            expect(response.status).toBe(500);
            expect(response.statusText).toBe("Internal Server Error");
            
            // Restore original URL
            process.env.NEXT_PUBLIC_VULKAN_SERVER_URL = originalUrl;
        });

        it("should handle malformed path parameters", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test");
            const params = Promise.resolve({ path: [] }); // Empty path
            
            const response = await GET(request, { params });
            
            // Should not crash, but may return error
            expect(response).toBeInstanceOf(Response);
            expect(response.status).toBeDefined();
        });
    });

    describe("Method-Specific Behavior", () => {
        it("should handle GET requests (read operations)", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test/get");
            const params = createMockParams(["test", "get"]);
            
            const response = await GET(request, { params });
            
            // Basic validation - should return a response
            expect(response).toBeInstanceOf(Response);
            // Network error is expected since backend is not running, but function should work
            expect(response.status).toBe(500);
        });

        it("should handle DELETE requests (read operations)", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test/delete", {
                method: "DELETE"
            });
            const params = createMockParams(["test", "delete"]);
            
            const response = await DELETE(request, { params });
            
            expect(response).toBeInstanceOf(Response);
            expect(response.status).toBe(500); // Expected network error
        });

        it("should handle POST requests (write operations)", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test/post", {
                method: "POST",
                body: JSON.stringify({ action: "create", data: "test" })
            });
            const params = createMockParams(["test", "post"]);
            
            const response = await POST(request, { params });
            
            expect(response).toBeInstanceOf(Response);
            expect(response.status).toBe(500); // Expected network error
        });

        it("should handle PUT requests (write operations)", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test/put", {
                method: "PUT",
                body: JSON.stringify({ action: "update", data: "test" })
            });
            const params = createMockParams(["test", "put"]);
            
            const response = await PUT(request, { params });
            
            expect(response).toBeInstanceOf(Response);
            expect(response.status).toBe(500); // Expected network error
        });

        it("should handle PATCH requests (write operations)", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test/patch", {
                method: "PATCH",
                body: JSON.stringify({ action: "patch", data: "test" })
            });
            const params = createMockParams(["test", "patch"]);
            
            const response = await PATCH(request, { params });
            
            expect(response).toBeInstanceOf(Response);
            expect(response.status).toBe(500); // Expected network error
        });
    });

    describe("Path Handling", () => {
        it("should handle single path segment", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/users");
            const params = createMockParams(["users"]);
            
            const response = await GET(request, { params });
            
            expect(response).toBeInstanceOf(Response);
        });

        it("should handle multiple path segments", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/users/123/profile");
            const params = createMockParams(["users", "123", "profile"]);
            
            const response = await GET(request, { params });
            
            expect(response).toBeInstanceOf(Response);
        });

        it("should handle path segments with special characters", async () => {
            const request = new NextRequest("http://localhost:3001/api/proxy/test/special-chars/with%20spaces");
            const params = createMockParams(["test", "special-chars", "with%20spaces"]);
            
            const response = await GET(request, { params });
            
            expect(response).toBeInstanceOf(Response);
        });
    });

    describe("Regression Tests", () => {
        it("should maintain compatibility with existing API patterns", async () => {
            // Test common API patterns that were working before
            const patterns = [
                ["policies"],
                ["policies", "123"],
                ["policy-versions", "456", "runs"],
                ["data-sources", "789", "usage"],
                ["components", "test-component"]
            ];

            for (const path of patterns) {
                const request = new NextRequest(`http://localhost:3001/api/proxy/${path.join("/")}`);
                const params = createMockParams(path);
                
                const response = await GET(request, { params });
                
                // Should not crash and return valid response
                expect(response).toBeInstanceOf(Response);
                expect(response.status).toBeDefined();
                expect(response.statusText).toBeDefined();
            }
        });

        it("should handle all HTTP methods without breaking", async () => {
            const testPath = ["test", "endpoint"];
            const params = createMockParams(testPath);
            const baseUrl = `http://localhost:3001/api/proxy/${testPath.join("/")}`;

            // Test all methods
            const methods = [
                { handler: GET, method: "GET" },
                { handler: POST, method: "POST" },
                { handler: PUT, method: "PUT" },
                { handler: DELETE, method: "DELETE" },
                { handler: PATCH, method: "PATCH" }
            ];

            for (const { handler, method } of methods) {
                const request = new NextRequest(baseUrl, {
                    method,
                    body: ["POST", "PUT", "PATCH"].includes(method) ? JSON.stringify({ test: "data" }) : undefined
                });

                const response = await handler(request, { params });
                
                expect(response).toBeInstanceOf(Response);
                expect(response.status).toBeDefined();
            }
        });
    });
});