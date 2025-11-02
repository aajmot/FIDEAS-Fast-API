-- Add new columns to sales_order_items table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sales_order_items' AND column_name = 'mrp') THEN
        ALTER TABLE sales_order_items ADD COLUMN mrp decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sales_order_items' AND column_name = 'gst_amount') THEN
        ALTER TABLE sales_order_items ADD COLUMN gst_amount decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sales_order_items' AND column_name = 'cgst_amount') THEN
        ALTER TABLE sales_order_items ADD COLUMN cgst_amount decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sales_order_items' AND column_name = 'sgst_amount') THEN
        ALTER TABLE sales_order_items ADD COLUMN sgst_amount decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sales_order_items' AND column_name = 'description') THEN
        ALTER TABLE sales_order_items ADD COLUMN description text;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'sales_order_items' AND column_name = 'product_name') THEN
        ALTER TABLE sales_order_items ADD COLUMN product_name text;
    END IF;


END $$;

-- Add new columns to purchase_order_items table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_order_items' AND column_name = 'mrp') THEN
        ALTER TABLE purchase_order_items ADD COLUMN mrp decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_order_items' AND column_name = 'gst_amount') THEN
        ALTER TABLE purchase_order_items ADD COLUMN gst_amount decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_order_items' AND column_name = 'cgst_amount') THEN
        ALTER TABLE purchase_order_items ADD COLUMN cgst_amount decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_order_items' AND column_name = 'sgst_amount') THEN
        ALTER TABLE purchase_order_items ADD COLUMN sgst_amount decimal(18,2) default null;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_order_items' AND column_name = 'description') THEN
        ALTER TABLE purchase_order_items ADD COLUMN description text;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'purchase_order_items' AND column_name = 'product_name') THEN
        ALTER TABLE purchase_order_items ADD COLUMN product_name text;
    END IF;
END $$;