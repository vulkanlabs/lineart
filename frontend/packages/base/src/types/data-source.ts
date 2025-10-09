/**
 * Data Source Type Extensions
 *
 * This file contains temporary type extensions for the DataSource type
 * until the backend implements these fields and regenerates OpenAPI types.
 *
 */

import type { DataSource } from "@vulkanlabs/client-open";

/**
 * Temporary type extension: Status field
 *
 * - Add 'status' field to DataSource model in backend
 * - Regenerate OpenAPI types from backend
 * - Remove this type extension once backend types include status
 *
 * This extension allows type-safe access to dataSource.status
 * without using 'as any' casts throughout the codebase.
 */
declare module "@vulkanlabs/client-open" {
    interface DataSource {
        /**
         * Status of the data source
         *
         * @description
         * - `draft`: Data source is in draft mode. Can be edited freely.
         *            Not available in workflows until published.
         *
         * - `published`: Data source is published and read-only.
         *                Available for use in workflows.
         *                Only timeout, retry policy can be adjusted.
         *
         * @default "draft"
         *
         * Transition: draft → published (one-way, no rollback)
         */
        status?: "draft" | "published";
    }
}

// Export empty object to make this a module
export {};
