-- Migration: Add Admin -> Settings -> Currency menu to menu_master
-- Date: 2025-10-27

DO $$
DECLARE
    admin_id INTEGER;
    settings_id INTEGER;
    currency_exists INTEGER;
BEGIN
    -- Ensure top-level Admin menu exists
    SELECT id INTO admin_id FROM menu_master WHERE menu_code = 'ADMIN';
    IF admin_id IS NULL THEN
        INSERT INTO menu_master(menu_name, menu_code, module_code, icon, route, sort_order, is_admin_only, is_active, created_at)
        VALUES('Admin', 'ADMIN', 'ADMIN', 'fa fa-cogs', '/admin', 1, TRUE, TRUE, NOW())
        RETURNING id INTO admin_id;
    END IF;

    -- Ensure Settings submenu under Admin exists
    SELECT id INTO settings_id FROM menu_master WHERE menu_code = 'ADMIN_SETTINGS';
    IF settings_id IS NULL THEN
        INSERT INTO menu_master(menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order, is_admin_only, is_active, created_at)
        VALUES('Settings', 'ADMIN_SETTINGS', 'ADMIN', admin_id, 'fa fa-sliders', '/admin/settings', 2, TRUE, TRUE, NOW())
        RETURNING id INTO settings_id;
    END IF;

    -- Insert Currency menu under Settings if not already present
    SELECT id INTO currency_exists FROM menu_master WHERE menu_code = 'ADMIN_SETTINGS_CURRENCY';
    IF currency_exists IS NULL THEN
        INSERT INTO menu_master(menu_name, menu_code, module_code, parent_menu_id, icon, route, sort_order, is_admin_only, is_active, created_at)
        VALUES('Currency', 'ADMIN_SETTINGS_CURRENCY', 'ADMIN', settings_id, 'fa fa-money', '/admin/settings/currency', 3, TRUE, TRUE, NOW());
    END IF;
END $$;
