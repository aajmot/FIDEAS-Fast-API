-- Add updated_at and updated_by columns to stock_transfers table
ALTER TABLE stock_transfers 
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_by VARCHAR(100);

-- Create trigger to automatically update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_stock_transfers_updated_at 
    BEFORE UPDATE ON stock_transfers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();