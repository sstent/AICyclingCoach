# Export/Import API Specification

## Export Endpoint
`GET /api/export`

### Parameters (query string)
- `types` (required): Comma-separated list of data types to export
  - Valid values: `routes`, `rules`, `plans`, `all`
- `format` (required): Export format 
  - `json`: Single JSON file
  - `zip`: ZIP archive with separate files
  - `gpx`: Only GPX files (routes only)

### Response
- `200 OK` with file download
- `400 Bad Request` for invalid parameters
- `500 Internal Server Error` for export failures

### Example
```http
GET /api/export?types=routes,plans&format=zip
```

---

## Import Validation
`POST /api/import/validate`

### Request
- Multipart form with `file` field containing import data

### Response
```json
{
  "valid": true,
  "conflicts": [
    {
      "type": "route",
      "id": 123,
      "name": "Mountain Loop",
      "existing_version": 2,
      "import_version": 3,
      "resolution_options": ["overwrite", "rename", "skip"]
    }
  ],
  "summary": {
    "routes": 15,
    "rules": 3,
    "plans": 2
  }
}
```

---

## Import Execution
`POST /api/import`

### Request
- Multipart form with:
  - `file`: Import data file
  - `conflict_resolution`: Global strategy (overwrite, skip, rename)
  - `resolutions`: JSON array of specific resolutions (optional)
    ```json
    [{"type": "route", "id": 123, "action": "overwrite"}]
    ```

### Response
```json
{
  "imported": {
    "routes": 12,
    "rules": 3,
    "plans": 2
  },
  "skipped": {
    "routes": 3,
    "rules": 0,
    "plans": 0
  },
  "errors": []
}
```

### Status Codes
- `200 OK`: Import completed
- `202 Accepted`: Import in progress (async)
- `400 Bad Request`: Invalid input
- `409 Conflict`: Unresolved conflicts

---