/**
 * API response helper
 *
 * Ensures all API routes return the same structure:
 * Success: { success: true, data: T, error: null }
 * Error: { success: false, data: null, error: string }
 */

/**
 * Use this for API route handlers 
 */
export const apiResult = {
    success: <T>(data: T) => Response.json({
        success: true,
        data,
        error: null,
    }),
    error: (message: string, status = 500) => Response.json({
        success: false,
        data: null,
        error: message,
    }, { status }),
};


export interface ApiResult<T> {
    success: boolean;
    data: T | null;
    error: string | null;
}