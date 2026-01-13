-- Patient demographics and statistics
CREATE OR REPLACE FUNCTION get_patient_analytics(p_tenant_id INTEGER)
RETURNS TABLE(
    total_patients INTEGER,
    new_patients_month INTEGER,
    active_patients INTEGER,
    age_group VARCHAR,
    age_count INTEGER,
    gender VARCHAR,
    gender_count INTEGER
) AS $$
DECLARE
    v_month_start DATE := DATE_TRUNC('month', CURRENT_DATE);
BEGIN
    RETURN QUERY
    WITH patient_stats AS (
        SELECT 
            COUNT(*)::INTEGER as total,
            COUNT(CASE WHEN created_at >= v_month_start THEN 1 END)::INTEGER as new_month,
            COUNT(CASE WHEN is_active = TRUE THEN 1 END)::INTEGER as active
        FROM patients 
        WHERE tenant_id = p_tenant_id AND is_deleted = FALSE
    ),
    age_stats AS (
        SELECT 
            CASE 
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) < 18 THEN 'Under 18'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) BETWEEN 18 AND 35 THEN '18-35'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) BETWEEN 36 AND 55 THEN '36-55'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth)) BETWEEN 56 AND 70 THEN '56-70'
                ELSE 'Over 70'
            END as age_group,
            COUNT(*)::INTEGER as count
        FROM patients 
        WHERE tenant_id = p_tenant_id AND is_deleted = FALSE AND date_of_birth IS NOT NULL
        GROUP BY 1
    ),
    gender_stats AS (
        SELECT 
            p.gender,
            COUNT(*)::INTEGER as count
        FROM patients p
        WHERE p.tenant_id = p_tenant_id AND p.is_deleted = FALSE AND p.gender IS NOT NULL
        GROUP BY p.gender
    )
    SELECT ps.total, ps.new_month, ps.active, 
           COALESCE(ag.age_group, 'No Data')::VARCHAR, COALESCE(ag.count, 0), 
           COALESCE(gs.gender, 'No Data')::VARCHAR, COALESCE(gs.count, 0)
    FROM patient_stats ps
    LEFT JOIN age_stats ag ON TRUE
    LEFT JOIN gender_stats gs ON TRUE;
END;
$$ LANGUAGE plpgsql;

-- Appointment analytics
CREATE OR REPLACE FUNCTION get_appointment_analytics(p_tenant_id INTEGER)
RETURNS TABLE(
    total_appointments INTEGER,
    scheduled_appointments INTEGER,
    completed_appointments INTEGER,
    cancelled_appointments INTEGER,
    no_show_appointments INTEGER,
    completion_rate DECIMAL,
    no_show_rate DECIMAL,
    avg_daily_appointments DECIMAL
) AS $$
DECLARE
    v_week_start DATE := CURRENT_DATE - INTERVAL '7 days';
    v_total INTEGER;
    v_completed INTEGER;
    v_no_show INTEGER;
BEGIN
    SELECT 
        COUNT(*)::INTEGER,
        COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END)::INTEGER,
        COUNT(CASE WHEN status = 'NO_SHOW' THEN 1 END)::INTEGER
    INTO v_total, v_completed, v_no_show
    FROM appointments 
    WHERE tenant_id = p_tenant_id AND appointment_date >= v_week_start AND is_deleted = FALSE;
    
    RETURN QUERY
    SELECT 
        v_total,
        COUNT(CASE WHEN status = 'SCHEDULED' THEN 1 END)::INTEGER,
        v_completed,
        COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END)::INTEGER,
        v_no_show,
        CASE WHEN v_total > 0 THEN ROUND((v_completed::DECIMAL / v_total * 100), 2) ELSE 0 END,
        CASE WHEN v_total > 0 THEN ROUND((v_no_show::DECIMAL / v_total * 100), 2) ELSE 0 END,
        ROUND((v_total::DECIMAL / 7), 2)
    FROM appointments 
    WHERE tenant_id = p_tenant_id AND appointment_date >= v_week_start AND is_deleted = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Clinical operations analytics
CREATE OR REPLACE FUNCTION get_clinical_operations(p_tenant_id INTEGER)
RETURNS TABLE(
    medical_records_generated INTEGER,
    prescriptions_issued INTEGER,
    test_orders_created INTEGER,
    sample_collections INTEGER,
    test_results_completed INTEGER,
    avg_turnaround_hours DECIMAL
) AS $$
DECLARE
    v_month_start DATE := DATE_TRUNC('month', CURRENT_DATE);
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM medical_records 
         WHERE tenant_id = p_tenant_id AND created_at >= v_month_start AND is_deleted = FALSE),
        (SELECT COUNT(*)::INTEGER FROM prescriptions 
         WHERE tenant_id = p_tenant_id AND created_at >= v_month_start AND is_deleted = FALSE),
        (SELECT COUNT(*)::INTEGER FROM test_orders 
         WHERE tenant_id = p_tenant_id AND created_at >= v_month_start AND is_deleted = FALSE),
        (SELECT COUNT(*)::INTEGER FROM sample_collections 
         WHERE tenant_id = p_tenant_id AND created_at >= v_month_start AND is_deleted = FALSE),
        0::INTEGER, -- test_results table doesn't exist yet
        0::DECIMAL; -- avg_turnaround_hours calculation disabled until test_results exists
END;
$$ LANGUAGE plpgsql;

-- Doctor performance analytics
CREATE OR REPLACE FUNCTION get_doctor_performance(p_tenant_id INTEGER)
RETURNS TABLE(
    doctor_name VARCHAR,
    specialization VARCHAR,
    total_appointments INTEGER,
    completed_appointments INTEGER,
    avg_consultation_fee DECIMAL,
    patient_satisfaction DECIMAL
) AS $$
DECLARE
    v_month_start DATE := DATE_TRUNC('month', CURRENT_DATE);
BEGIN
    RETURN QUERY
    SELECT 
        (d.first_name || ' ' || d.last_name)::VARCHAR,
        d.specialization::VARCHAR,
        COUNT(a.id)::INTEGER,
        COUNT(CASE WHEN a.status = 'COMPLETED' THEN 1 END)::INTEGER,
        d.consultation_fee,
        0.0::DECIMAL -- Placeholder for satisfaction score
    FROM doctors d
    LEFT JOIN appointments a ON d.id = a.doctor_id 
        AND a.appointment_date >= v_month_start 
        AND a.is_deleted = FALSE
    WHERE d.tenant_id = p_tenant_id AND d.is_active = TRUE
    GROUP BY d.id, d.first_name, d.last_name, d.specialization, d.consultation_fee
    ORDER BY COUNT(a.id) DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- Test analytics
CREATE OR REPLACE FUNCTION get_test_analytics(p_tenant_id INTEGER)
RETURNS TABLE(
    test_name VARCHAR,
    category_name VARCHAR,
    total_orders INTEGER,
    total_revenue DECIMAL,
    avg_turnaround_days DECIMAL
) AS $$
DECLARE
    v_month_start DATE := DATE_TRUNC('month', CURRENT_DATE);
BEGIN
    -- Return empty result since tests and test_categories tables don't exist yet
    RETURN QUERY
    SELECT 
        'No Data'::VARCHAR as test_name,
        'No Data'::VARCHAR as category_name,
        0::INTEGER as total_orders,
        0::DECIMAL as total_revenue,
        0::DECIMAL as avg_turnaround_days
    WHERE FALSE; -- This ensures no rows are returned
END;
$$ LANGUAGE plpgsql;