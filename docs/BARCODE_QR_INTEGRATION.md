# Barcode & QR Code Integration

## Overview
Barcode and QR code generation utility integrated into FIDEAS FastAPI application. Generates base64-encoded images that can be directly used in UI/reports.

## Installation
```bash
pip install -r requirements.txt
```

Dependencies added:
- `python-barcode>=0.15.1` - For barcode generation
- `qrcode[pil]>=7.4.2` - For QR code generation

## Usage

### 1. Direct Utility Usage

```python
from core.shared.utils.barcode_utils import BarcodeGenerator

# Generate barcode (Code128 - alphanumeric)
barcode_base64 = BarcodeGenerator.generate_barcode("ORD-2024-001")

# Generate QR code
qr_base64 = BarcodeGenerator.generate_qr_code("https://example.com/order/123")

# Generate product barcode
product_barcode = BarcodeGenerator.generate_product_barcode("PROD-12345")

# Generate order QR with URL
order_qr = BarcodeGenerator.generate_order_qr("ORD-001", 123, "https://app.example.com")
```

### 2. API Integration

#### Test Orders
```bash
# Get test order with barcode/QR
GET /api/v1/testorders/123?include_barcode=true

Response:
{
  "success": true,
  "data": {
    "id": 123,
    "test_order_number": "TO-2024-001",
    "patient_name": "John Doe",
    ...
    "barcode": "data:image/png;base64,iVBORw0KG...",
    "qr_code": "data:image/png;base64,iVBORw0KG..."
  }
}
```

#### Test Invoices
```bash
# Get test invoice with barcode/QR
GET /api/v1/testinvoices/456?include_barcode=true

Response:
{
  "success": true,
  "data": {
    "id": 456,
    "invoice_number": "INV-2024-001",
    "final_amount": 1500.00,
    ...
    "barcode": "data:image/png;base64,iVBORw0KG...",
    "qr_code": "data:image/png;base64,iVBORw0KG..."
  }
}
```

#### Products
```bash
# Get product with barcode/QR
GET /api/v1/products/789?include_barcode=true

Response:
{
  "success": true,
  "data": {
    "id": 789,
    "product_code": "PROD-001",
    "product_name": "Medicine XYZ",
    ...
    "barcode": "data:image/png;base64,iVBORw0KG...",
    "qr_code": "data:image/png;base64,iVBORw0KG..."
  }
}
```

### 3. Frontend Usage

```html
<!-- Direct image display -->
<img src="{{ barcode }}" alt="Barcode" />

<!-- In reports -->
<div class="barcode-container">
  <img src="{{ qr_code }}" style="width: 100px; height: 100px;" />
</div>
```

```javascript
// React/Vue example
<img src={data.barcode} alt="Order Barcode" />
<img src={data.qr_code} alt="Order QR Code" />
```

### 4. Report Generation (ReportLab)

```python
from reportlab.lib.utils import ImageReader
import io
import base64

# Extract base64 data
barcode_data = barcode_base64.split(',')[1]
img_bytes = base64.b64decode(barcode_data)
img_buffer = io.BytesIO(img_bytes)

# Use in ReportLab
from reportlab.platypus import Image
barcode_img = Image(img_buffer, width=200, height=50)
```

### 5. Batch Generation for Reports

```python
from core.shared.utils.barcode_utils import BarcodeGenerator

def generate_product_labels(products):
    """Generate barcodes for multiple products"""
    for product in products:
        try:
            product['barcode'] = BarcodeGenerator.generate_barcode(product['product_code'])
            product['qr_code'] = BarcodeGenerator.generate_qr_code(
                f"PRODUCT:{product['product_code']}|NAME:{product['product_name']}"
            )
        except Exception as e:
            product['barcode'] = None
            product['qr_code'] = None
    return products
```

## Barcode Types

### Code128 (Default - Recommended)
- **Use for**: Order numbers, invoice numbers, product codes
- **Supports**: Alphanumeric characters
- **Example**: `TO-2024-001`, `INV-2024-456`

### Code39
- **Use for**: Legacy systems
- **Supports**: Alphanumeric (limited)
- **Example**: `PROD123`

### EAN-13
- **Use for**: Retail products (13 digits)
- **Supports**: Numeric only
- **Example**: `1234567890123`

### EAN-8
- **Use for**: Small products (8 digits)
- **Supports**: Numeric only
- **Example**: `12345678`

## QR Code Options

### Error Correction Levels
- **L**: 7% error correction (default for small data)
- **M**: 15% error correction (recommended)
- **Q**: 25% error correction
- **H**: 30% error correction (use for critical data)

### Data Formats
```python
# URL
qr = BarcodeGenerator.generate_qr_code("https://example.com/order/123")

# Structured data
qr = BarcodeGenerator.generate_qr_code("ORDER:TO-001|PATIENT:John|AMOUNT:1500")

# JSON (for complex data)
import json
data = {"order_id": 123, "patient": "John", "amount": 1500}
qr = BarcodeGenerator.generate_qr_code(json.dumps(data))
```

## Integration Points

### Current Integrations
✅ Test Orders (`/api/v1/testorders/{id}?include_barcode=true`)
✅ Test Invoices (`/api/v1/testinvoices/{id}?include_barcode=true`)
✅ Products (`/api/v1/products/{id}?include_barcode=true`)

### Future Integrations
- Sales Orders
- Sales Invoices
- Purchase Orders
- Purchase Invoices
- Warehouse locations
- Patient records
- Sample collection labels

## Performance Considerations

1. **Lazy Loading**: Barcodes generated only when `include_barcode=true`
2. **No Storage**: Generated on-demand, not stored in database
3. **Caching**: Consider caching for frequently accessed items
4. **Batch Processing**: For reports, generate in bulk

## Error Handling

```python
try:
    barcode = BarcodeGenerator.generate_barcode(code)
except ValueError as e:
    # Invalid data for barcode type
    logger.error(f"Barcode generation failed: {e}")
    barcode = None
```

All service methods handle errors gracefully and return `None` for barcode/qr_code fields on failure.

## Examples

### Test Order QR Data
```
TEST_ORDER:TO-2024-001|ID:123|PATIENT:John Doe
```

### Test Invoice QR Data
```
INVOICE:INV-2024-001|AMOUNT:1500.00|PATIENT:John Doe
```

### Product QR Data
```
PRODUCT:PROD-001|NAME:Medicine XYZ
```

## Troubleshooting

### Issue: Barcode generation fails
- Check if data contains invalid characters for barcode type
- Use Code128 for alphanumeric data
- Use EAN-13/EAN-8 only for numeric data

### Issue: QR code too large
- Reduce data size
- Use URL shortener for long URLs
- Lower error correction level

### Issue: Image not displaying in frontend
- Verify base64 string includes `data:image/png;base64,` prefix
- Check browser console for errors
- Ensure proper HTML escaping
