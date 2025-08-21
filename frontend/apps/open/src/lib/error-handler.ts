/**
 * Enhanced error handler for user-friendly error messages
 */
export function createUserFriendlyError(
    operation: string,
    resourceType: string,
    error: unknown
): Error {
    const errorMessage = error instanceof Error ? error.message : String(error);
    
    // Common error patterns and their user-friendly messages
    const errorPatterns = [
        {
            pattern: /network|fetch|connection/i,
            message: `Unable to ${operation} ${resourceType} due to network issues. ` +
                     `Please check your connection and try again.`
        },
        {
            pattern: /unauthorized|403|forbidden/i,
            message: `You don't have permission to ${operation} this ${resourceType}.`
        },
        {
            pattern: /not found|404/i,
            message: `The ${resourceType} you're trying to ${operation} was not found. ` +
                     `It may have been deleted by someone else.`
        },
        {
            pattern: /validation|invalid|bad request|400/i,
            message: `Invalid data provided for ${operation} ${resourceType}. Please check your input and try again.`
        },
        {
            pattern: /conflict|409/i,
            message: `Cannot ${operation} ${resourceType} due to a conflict. It may be in use or have dependencies.`
        },
        {
            pattern: /server|500|502|503/i,
            message: `Server error occurred while trying to ${operation} ${resourceType}. Please try again later.`
        }
    ];

    for (const { pattern, message } of errorPatterns) {
        if (pattern.test(errorMessage)) {
            return new Error(message);
        }
    }

    // If no specific pattern matches, return a generic but informative message
    return new Error(`Failed to ${operation} ${resourceType}. ${errorMessage}`);
}

export function handleActionError(
    operation: string,
    resourceType: string,
    error: unknown
): never {
    const userFriendlyError = createUserFriendlyError(operation, resourceType, error);
    console.error(`Error ${operation} ${resourceType}:`, error);
    throw userFriendlyError;
}