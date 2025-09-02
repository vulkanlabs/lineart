import { useEffect, useRef, useCallback } from "react";
import { useWorkflowStore } from "../store/workflow-store";
import type { WorkflowApiClient } from "../api/types";

interface UseAutoSaveConfig {
    apiClient: WorkflowApiClient;
    workflow: any;
    getUIMetadata?: () => { [key: string]: any };
    activityDelay?: number; // Default: 15000ms (15s)
    fallbackInterval?: number; // Default: 60000ms (60s)
    maxRetryAttempts?: number; // Default: 3
    retryDelayBase?: number; // Default: 2000ms (2s)
    circuitBreakerThreshold?: number; // Default: 5 consecutive failures
    circuitBreakerCooldown?: number; // Default: 300000ms (5 minutes)
}

interface RetryState {
    attempts: number;
    lastError: Error | null;
}

interface CircuitBreakerState {
    consecutiveFailures: number;
    lastFailureTime: Date | null;
    isOpen: boolean;
}

export function useAutoSave({
    apiClient,
    workflow,
    getUIMetadata = () => ({}),
    activityDelay = 15000,
    fallbackInterval = 60000,
    maxRetryAttempts = 3,
    retryDelayBase = 2000,
    circuitBreakerThreshold = 5,
    circuitBreakerCooldown = 300000,
}: UseAutoSaveConfig) {
    const activityTimerRef = useRef<NodeJS.Timeout | null>(null);
    const fallbackTimerRef = useRef<NodeJS.Timeout | null>(null);
    const retryTimerRef = useRef<NodeJS.Timeout | null>(null);
    const lastSaveAttemptRef = useRef<Date | null>(null);
    const retryStateRef = useRef<RetryState>({ attempts: 0, lastError: null });
    const circuitBreakerRef = useRef<CircuitBreakerState>({ 
        consecutiveFailures: 0, 
        lastFailureTime: null, 
        isOpen: false 
    });

    const { 
        autoSave, 
        markSaving, 
        markSaved, 
        markSaveError,
        getSpec 
    } = useWorkflowStore((state) => ({
        autoSave: state.autoSave,
        markSaving: state.markSaving,
        markSaved: state.markSaved,
        markSaveError: state.markSaveError,
        getSpec: state.getSpec,
    }));

    const isRetryableError = useCallback((error: Error): boolean => {
        // Network errors, timeout errors, and 5xx server errors are retryable
        const retryablePatterns = [
            /network/i,
            /timeout/i,
            /connection/i,
            /502|503|504/,
            /fetch/i,
        ];
        return retryablePatterns.some(pattern => pattern.test(error.message));
    }, []);

    const calculateRetryDelay = useCallback((attempt: number): number => {
        // Exponential backoff with jitter: base * (2^attempt) + random(0-1000ms)
        return retryDelayBase * Math.pow(2, attempt) + Math.random() * 1000;
    }, [retryDelayBase]);

    const checkCircuitBreaker = useCallback((): boolean => {
        const now = new Date();
        
        // If circuit breaker is open, check if cooldown period has passed
        if (circuitBreakerRef.current.isOpen) {
            if (circuitBreakerRef.current.lastFailureTime && 
                (now.getTime() - circuitBreakerRef.current.lastFailureTime.getTime()) > circuitBreakerCooldown) {
                // Reset circuit breaker to half-open state
                circuitBreakerRef.current.isOpen = false;
                circuitBreakerRef.current.consecutiveFailures = 0;
                console.info("Circuit breaker entering half-open state, allowing auto-save attempts");
                return true;
            }
            return false; // Still in open state
        }
        
        return true; // Circuit is closed, allow requests
    }, [circuitBreakerCooldown]);

    const handleCircuitBreakerFailure = useCallback(() => {
        circuitBreakerRef.current.consecutiveFailures += 1;
        circuitBreakerRef.current.lastFailureTime = new Date();
        
        if (circuitBreakerRef.current.consecutiveFailures >= circuitBreakerThreshold) {
            circuitBreakerRef.current.isOpen = true;
            console.warn(`Circuit breaker opened after ${circuitBreakerThreshold} consecutive failures. Auto-save disabled for ${circuitBreakerCooldown / 60000} minutes.`);
        }
    }, [circuitBreakerThreshold, circuitBreakerCooldown]);

    const handleCircuitBreakerSuccess = useCallback(() => {
        // Reset circuit breaker on successful save
        circuitBreakerRef.current.consecutiveFailures = 0;
        circuitBreakerRef.current.isOpen = false;
        circuitBreakerRef.current.lastFailureTime = null;
    }, []);

    const performAutoSave = useCallback(async (isRetry: boolean = false): Promise<void> => {
        if (!autoSave.autoSaveEnabled || autoSave.isSaving) return;

        // Check circuit breaker before attempting save
        if (!checkCircuitBreaker()) {
            console.warn("Auto-save blocked by circuit breaker. Service may be experiencing issues.");
            return;
        }

        try {
            if (!isRetry) {
                markSaving();
                lastSaveAttemptRef.current = new Date();
                // Reset retry state on new save attempt
                retryStateRef.current = { attempts: 0, lastError: null };
            }

            const spec = getSpec();
            const uiMetadata = getUIMetadata();

            await apiClient.saveWorkflowSpec(workflow, spec, uiMetadata, true); // isAutoSave = true
            
            // Success - reset retry state, circuit breaker, and mark as saved
            retryStateRef.current = { attempts: 0, lastError: null };
            handleCircuitBreakerSuccess();
            markSaved();
            
        } catch (error) {
            const currentError = error instanceof Error ? error : new Error("Auto-save failed");
            retryStateRef.current.lastError = currentError;

            // Check if we should retry
            if (retryStateRef.current.attempts < maxRetryAttempts && isRetryableError(currentError)) {
                retryStateRef.current.attempts += 1;
                const delay = calculateRetryDelay(retryStateRef.current.attempts - 1);
                
                console.warn(`Auto-save attempt ${retryStateRef.current.attempts + 1} failed, retrying in ${Math.round(delay)}ms:`, currentError.message);
                
                // Clear any existing retry timer
                if (retryTimerRef.current) clearTimeout(retryTimerRef.current);

                // Schedule retry with exponential backoff
                retryTimerRef.current = setTimeout(() => {
                    markSaving(); // Show saving state during retry
                    performAutoSave(true);
                }, delay);
                
            } else {
                // Max retries reached or non-retryable error
                // Only trigger circuit breaker for retryable errors that exhausted retries
                if (isRetryableError(currentError)) handleCircuitBreakerFailure();
                
                const finalErrorMessage = `Auto-save failed after ${retryStateRef.current.attempts} attempts: ${currentError.message}`;
                markSaveError(finalErrorMessage);
                console.error("Auto-save failed permanently:", {
                    attempts: retryStateRef.current.attempts,
                    maxAttempts: maxRetryAttempts,
                    isRetryable: isRetryableError(currentError),
                    error: currentError,
                    circuitBreakerState: circuitBreakerRef.current
                });
                
                // Reset retry state
                retryStateRef.current = { attempts: 0, lastError: null };
            }
        }
    }, [apiClient, workflow, autoSave.autoSaveEnabled, autoSave.isSaving, markSaving, markSaved, markSaveError, getSpec, getUIMetadata, maxRetryAttempts, isRetryableError, calculateRetryDelay, checkCircuitBreaker, handleCircuitBreakerSuccess, handleCircuitBreakerFailure]);

    const scheduleActivitySave = useCallback(() => {
        // Clear existing activity timer
        if (activityTimerRef.current) clearTimeout(activityTimerRef.current);

        // Schedule save after activity delay (3s after last change)
        activityTimerRef.current = setTimeout(() => {
            if (autoSave.hasUnsavedChanges) performAutoSave();
        }, 3000); // 3 second delay after last activity
    }, [autoSave.hasUnsavedChanges, performAutoSave]);

    const scheduleFallbackSave = useCallback(() => {
        // Clear existing fallback timer
        if (fallbackTimerRef.current) clearInterval(fallbackTimerRef.current);

        // Schedule regular fallback saves
        fallbackTimerRef.current = setInterval(() => {
            if (autoSave.hasUnsavedChanges && autoSave.autoSaveEnabled) performAutoSave();
        }, fallbackInterval);
    }, [autoSave.hasUnsavedChanges, autoSave.autoSaveEnabled, fallbackInterval, performAutoSave]);

    // React to changes in workflow state
    useEffect(() => {
        if (autoSave.hasUnsavedChanges && autoSave.autoSaveEnabled) {
            scheduleActivitySave();
        }
    }, [autoSave.hasUnsavedChanges, autoSave.autoSaveEnabled, scheduleActivitySave]);

    // Set up fallback timer on mount
    useEffect(() => {
        if (autoSave.autoSaveEnabled) scheduleFallbackSave();

        return () => {
            if (fallbackTimerRef.current) clearInterval(fallbackTimerRef.current);
        };
    }, [autoSave.autoSaveEnabled, scheduleFallbackSave]);

    // Cleanup timers on unmount
    useEffect(() => {
        return () => {
            if (activityTimerRef.current) clearTimeout(activityTimerRef.current);
            if (fallbackTimerRef.current) clearInterval(fallbackTimerRef.current);
            if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
        };
    }, []);

    return {
        isAutoSaving: autoSave.isSaving,
        hasUnsavedChanges: autoSave.hasUnsavedChanges,
        lastSaved: autoSave.lastSaved,
        saveError: autoSave.saveError,
        autoSaveEnabled: autoSave.autoSaveEnabled,
        retryAttempts: retryStateRef.current.attempts,
        circuitBreakerOpen: circuitBreakerRef.current.isOpen,
        consecutiveFailures: circuitBreakerRef.current.consecutiveFailures,
        performManualSave: () => performAutoSave(false), // For manual save button
    };
}