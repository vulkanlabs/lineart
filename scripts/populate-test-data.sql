-- Populate test data for DataSource metrics for the last 7 days
DO $$
DECLARE
    v_policy_version_id UUID := '8b4825a0-9324-4b8f-85dc-471da7873281';
    v_data_source_id UUID := 'a6348020-1d3f-4d98-9c7f-06e90ef45402';
    v_run_id UUID;
    v_data_object_id UUID;
    v_run_count INT;
    v_data_object_count INT;
    v_inserted_count INT;
    v_now TIMESTAMP;
BEGIN
    -- Check if policy version exists
    SELECT COUNT(*) INTO v_run_count FROM run WHERE policy_version_id = v_policy_version_id;
    IF v_run_count = 0 THEN
        RAISE EXCEPTION 'No runs found for policy_version_id %', v_policy_version_id;
    END IF;
    
    -- Check if data source exists and has data objects
    SELECT COUNT(*) INTO v_data_object_count FROM data_object WHERE data_source_id = v_data_source_id;
    IF v_data_object_count = 0 THEN
        RAISE EXCEPTION 'No data objects found for data_source_id %', v_data_source_id;
    END IF;
    
    -- Get sample IDs to verify they exist
    SELECT run_id INTO v_run_id FROM run WHERE policy_version_id = v_policy_version_id LIMIT 1;
    SELECT data_object_id INTO v_data_object_id FROM data_object WHERE data_source_id = v_data_source_id LIMIT 1;
    
    RAISE NOTICE 'Found run_id: %, data_object_id: %', v_run_id, v_data_object_id;

    -- Store current timestamp for consistent data generation
    SELECT now() INTO v_now;
    
    -- Create a temporary table to store test data
    CREATE TEMPORARY TABLE temp_test_data AS
    WITH date_series AS (
        -- Generate a series of dates for the last 7 days
        SELECT 
            generate_series(
                date_trunc('day', v_now) - interval '6 days', 
                date_trunc('day', v_now),
                interval '1 day'
            )::date as metric_date
    )
    SELECT 
        metric_date,
        -- Random number of requests between 50 and 500
        floor(random() * 450 + 50)::int as request_count,
        -- Random response time between 50ms and 500ms (in seconds for StepMetadata)
        (random() * 0.450 + 0.050)::float as avg_response_time_sec,
        -- Random error rate between 0% and 15%
        (random() * 0.15)::float as error_rate,
        -- Random cache hit ratio between 30% and 95%
        (random() * 0.65 + 0.30)::float as cache_hit_ratio
    FROM date_series;

    -- Insert data into run_data_request to simulate data source usage with both SOURCE and CACHE origins
    INSERT INTO run_data_request (
        run_data_request_id,
        run_id,
        data_object_id,
        data_source_id,
        data_origin,
        created_at
    )
    SELECT 
        gen_random_uuid(),
        v_run_id,
        v_data_object_id,
        v_data_source_id,
        -- Use REQUEST for some percentage and CACHE for the rest based on cache_hit_ratio
        CASE 
            WHEN random() <= t.cache_hit_ratio THEN 'CACHE'::DataObjectOrigin
            ELSE 'REQUEST'::DataObjectOrigin 
        END,
        -- Distribute requests throughout the day
        t.metric_date + (random() * interval '1 day')
    FROM temp_test_data t, 
        -- For each day, generate multiple records based on the request count
        generate_series(1, (SELECT max(request_count) FROM temp_test_data))
    WHERE generate_series <= t.request_count;
    
    -- Insert data into StepMetadata for response time and error rate metrics
    INSERT INTO step_metadata (
        step_metadata_id,
        run_id,
        step_name,
        node_type,
        start_time,
        end_time,
        error,
        created_at
    )
    SELECT 
        gen_random_uuid(),
        v_run_id,
        'data_input_node',
        'DATA_INPUT', -- Match the NodeType.DATA_INPUT.value
        -- Convert timestamps to epoch seconds (double precision)
        EXTRACT(EPOCH FROM t.metric_date + (random() * interval '1 day')), 
        EXTRACT(EPOCH FROM t.metric_date + (random() * interval '1 day')) + t.avg_response_time_sec,
        -- Add errors based on error_rate probability
        CASE 
            WHEN random() <= t.error_rate THEN '{"error": "API timeout"}'::jsonb
            ELSE NULL 
        END,
        t.metric_date + (random() * interval '1 day')
    FROM temp_test_data t, 
        -- Generate same number of step metadata records as requests
        generate_series(1, (SELECT max(request_count) FROM temp_test_data))
    WHERE generate_series <= t.request_count;
    
    -- Get count of inserted records
    SELECT SUM(request_count) INTO v_inserted_count FROM temp_test_data;
    
    -- Output success message with count
    RAISE NOTICE 'Successfully inserted % records', v_inserted_count;
    
    -- Clean up temporary table
    DROP TABLE temp_test_data;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error: % %', SQLERRM, SQLSTATE;
END $$;