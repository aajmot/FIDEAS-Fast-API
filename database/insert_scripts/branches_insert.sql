-- Sample MAIN_BRANCH insert statement
INSERT INTO public.branches (
    tenant_id,
    branch_code,
    branch_name,
    branch_type,
    phone,
    email,
    contact_person,
    address_line1,
    address_line2,
    city,
    state,
    pincode,
    country,
    gstin,
    pan,
    tan,
    is_default,
    status,
    remarks,
    created_by,
    updated_by
) VALUES (
    1,                          -- tenant_id (adjust as needed)
    'MAIN_BRANCH',              -- branch_code
    'Main Branch Office',       -- branch_name
    'HEAD_OFFICE',              -- branch_type
    '+91-9876543210',           -- phone
    'main@company.com',         -- email
    'Branch Manager',           -- contact_person
    '123 Business Park',        -- address_line1
    'Sector 5',                 -- address_line2
    'Mumbai',                   -- city
    'Maharashtra',              -- state
    '400001',                   -- pincode
    'India',                    -- country
    '27AABCU9603R1ZM',          -- gstin (sample format)
    'AABCU9603R',               -- pan (sample format)
    'MUMU12345A',               -- tan (sample format)
    TRUE,                       -- is_default
    'ACTIVE',                   -- status
    'Main branch office',       -- remarks
    'system',                   -- created_by
    'system'                    -- updated_by
);


INSERT INTO public.branches (tenant_id, branch_code, branch_name, branch_type, is_default, status)
VALUES (1, 'MAIN_BRANCH', 'Main Branch Office', 'HEAD_OFFICE', TRUE, 'ACTIVE');
