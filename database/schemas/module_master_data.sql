TRUNCATE TABLE module_master;   

insert into module_master (module_name, module_code, description, is_mandatory)
 values
('ADMIN', 'ADMIN', 'Module for managing administration tasks', true),
('INVENTORY', 'INVENTORY', 'Module for managing inventory processes', false),
('ACCOUNTING', 'ACCOUNTING', 'Module for managing accounts and finances', false),
('CLINIC', 'CLINIC', 'Module for managing clinic operations', false),
('DIAGNOSTIC', 'DIAGNOSTIC', 'Module for managing diagnostics services', false),
('PHARMACY', 'PHARMACY', 'Module for managing pharmacy operations', false),
('DASHBOARD', 'DASHBOARD', 'Module for dashboard and reporting functionalities', false)
;

