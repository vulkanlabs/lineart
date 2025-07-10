export type Dict = {
    [key: string]: any;
};

export type RequestOptions = {
    url: string;
    method: string;
    headers?: Dict;
    params?: Dict;
    body_schema?: Dict;
    timeout?: number;
};

export type CachingTTL = {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
};

export type CachingOptions = {
    enabled: boolean;
    ttl: CachingTTL | number | null;
};

export type RetryPolicy = {
    max_retries: number;
    backoff_factor: number | null;
    status_forcelist: number[] | null;
};

export type DataSource = {
    name: string;
    keys: string[];
    request: RequestOptions;
    caching: CachingOptions;
    retry?: RetryPolicy | null;
    description?: string | null;
    metadata?: Dict | null;
    data_source_id: string;
    project_id: string;
    created_at: string;
    last_updated_at: string;
};
