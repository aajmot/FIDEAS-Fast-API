DELETE FROM public.tenant_settings CASCADE;

-- Insert default settings for tenant 1
INSERT INTO public.tenant_settings (
    tenant_id, 
    enable_inventory, 
    enable_gst, 
    enable_bank_entry, 
    base_currency, 
    payment_modes, 
    default_payment_mode,
    created_at, 
    created_by, 
    updated_at, 
    updated_by
) VALUES (
    1, 
    TRUE, 
    TRUE, 
    TRUE, 
    'INR', 
    ARRAY['CASH','UPI'], 
    'CASH',
    CURRENT_TIMESTAMP, 
    'system', 
    CURRENT_TIMESTAMP, 
    'system'
);

-- Insert default settings for tenant 2
INSERT INTO public.tenant_settings (
    tenant_id, 
    enable_inventory, 
    enable_gst, 
    enable_bank_entry, 
    base_currency, 
    payment_modes, 
    default_payment_mode,
    created_at, 
    created_by, 
    updated_at, 
    updated_by
) VALUES (
    2, 
    TRUE, 
    TRUE, 
    TRUE, 
    'INR', 
    ARRAY['CASH','UPI'], 
    'CASH',
    CURRENT_TIMESTAMP, 
    'system', 
    CURRENT_TIMESTAMP, 
    'system'
);