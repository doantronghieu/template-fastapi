"""Export OpenAPI schema to openapi.json for client generation."""

import json
from pathlib import Path

from app.main import app

# Export OpenAPI schema
openapi_schema = app.openapi()

# Write to project root
output_path = Path(__file__).parent.parent / "openapi.json"
output_path.write_text(json.dumps(openapi_schema, indent=2))

print(f"✓ OpenAPI schema exported to {output_path}")
