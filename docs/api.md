# TCF Pricing Tool API Documentation

## Fan Calculation Endpoints

### Calculate Fan Data
**Endpoint:** `/calculate_fan`  
**Method:** POST  
**Description:** Calculates fan weight, fabrication cost, and total cost based on selected options.

**Request Body:**
```json
{
    "Fan_Model": "string",
    "Fan_Size": "string",
    "Class": "string",
    "Arrangement": "integer",
    "vendor": "string",
    "material": "string",
    "vibration_isolators": "string",
    "fabrication_margin": "float",
    "bought_out_margin": "float",
    "accessories": {
        "accessory_name": "boolean"
    },
    "optionalItemPrices": {
        "item_name": "float"
    }
}
```

**Response:**
```json
{
    "success": true,
    "bare_fan_weight": "float",
    "no_of_isolators": "float",
    "shaft_diameter": "float",
    "total_weight": "float",
    "fabrication_cost": "float",
    "total_fabrication_cost": "float",
    "total_bought_out_cost": "float",
    "total_cost": "float"
}
```

### Check Accessory Weight
**Endpoint:** `/check_accessory_weight`  
**Method:** POST  
**Description:** Checks if weight data exists for a specific accessory and fan combination.

**Request Body:**
```json
{
    "accessory": "string",
    "Fan Model": "string",
    "Fan Size": "string",
    "Class": "string",
    "Arrangement": "integer"
}
```

**Response:**
```json
{
    "success": true,
    "weight": "float"
}
```

### Save Accessory Weight
**Endpoint:** `/save_accessory_weight`  
**Method:** POST  
**Description:** Saves or updates weight data for a specific accessory and fan combination.

**Request Body:**
```json
{
    "accessory": "string",
    "Fan Model": "string",
    "Fan Size": "string",
    "Class": "string",
    "Arrangement": "integer",
    "weight": "float"
}
```

**Response:**
```json
{
    "success": true,
    "message": "string"
}
```

## Valid Values

### Accessories
The following accessories are supported:
- Unitary Base Frame
- Isolation Base Frame
- Split Casing
- Inlet Companion Flange
- Outlet Companion Flange
- Inlet Butterfly Damper

### Materials
- ms (Mild Steel)
- ss304 (Stainless Steel 304)
- mixed (Mixed Construction)

### Vibration Isolators
- not_required
- polybond
- dunlop

## Error Handling
All endpoints return appropriate error messages with HTTP status codes:
- 400: Bad Request (invalid input)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Example error response:
```json
{
    "success": false,
    "error": "error message"
}
``` 