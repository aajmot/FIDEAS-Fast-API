-- Migration: Remove Account Currency Management menu from menu_master
-- Date: 2025-10-27

DO $$
DECLARE
    d_menu_id INTEGER;
BEGIN
    SELECT t.id INTO d_menu_id FROM menu_master t WHERE t.menu_code = 'CURRENCY_MANAGEMENT';
    IF d_menu_id IS NOT NULL THEN
        DELETE FROM role_menu_mapping t where t.menu_id=d_menu_id;
        DELETE FROM menu_master t WHERE t.id = d_menu_id;
    END IF;
END $$;
