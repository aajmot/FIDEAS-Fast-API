DROP TABLE IF EXISTS public.menu_master;
-- 1. Create the table
CREATE TABLE IF NOT EXISTS public.menu_master (
    id              SERIAL PRIMARY KEY,
    -- Core Identity
    menu_name       VARCHAR(100) NOT NULL,
    menu_code       VARCHAR(50) NOT NULL UNIQUE,
    module_code     VARCHAR(50) NOT NULL,
    
    -- Hierarchy & Navigation
    parent_menu_id  INTEGER REFERENCES public.menu_master(id) ON DELETE SET NULL,
    icon            VARCHAR(100),
    route           VARCHAR(200),
    sort_order      INTEGER DEFAULT 0,
    
    -- Permissions & State
    is_admin_only   BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    is_deleted      BOOLEAN DEFAULT FALSE,
    
    -- Audit Trail
    created_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(100) DEFAULT 'system',
    updated_at      TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by      VARCHAR(100) DEFAULT 'system'
);

-- 2. Create index for faster parent/child lookups (Recursive Queries)
CREATE INDEX IF NOT EXISTS idx_menu_parent_id ON public.menu_master(parent_menu_id);
CREATE INDEX IF NOT EXISTS idx_menu_module_code ON public.menu_master(module_code);

-- 3. Automatic Update Trigger for 'updated_at'
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_menu_master_modtime
    BEFORE UPDATE ON public.menu_master
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();


-- ================
-- WITH RECURSIVE menu_tree AS (
--     -- Root items (Parent is NULL)
--     SELECT id, menu_name, menu_code, parent_menu_id, 1 as level
--     FROM menu_master
--     WHERE parent_menu_id IS NULL AND is_active = TRUE
    
--     UNION ALL
    
--     -- Child items
--     SELECT m.id, m.menu_name, m.menu_code, m.parent_menu_id, mt.level + 1
--     FROM menu_master m
--     INNER JOIN menu_tree mt ON m.parent_menu_id = mt.id
--     WHERE m.is_active = TRUE
-- )
-- SELECT * FROM menu_tree ORDER BY level, id;