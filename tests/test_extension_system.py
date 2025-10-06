"""End-to-end integration tests for extension system.

Tests the complete extension loading flow including:
- Configuration parsing
- Model loading
- API routes
- Admin views
- OpenAPI documentation

Note: The _example extension is enabled by default in tests (via conftest.py).
"""

from httpx import AsyncClient

from app.core.config import settings


class TestExtensionSystem:
    """Integration tests for extension system with _example extension enabled."""

    async def test_extension_configuration(self):
        """Test extension configuration parsing."""
        assert "_example" in settings.ENABLED_EXTENSIONS
        assert isinstance(settings.ENABLED_EXTENSIONS, list)

    async def test_extension_api_routes_loaded(self, client: AsyncClient):
        """Test extension API routes are accessible."""
        # Test listing features
        response = await client.get("/api/example/features")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_extension_crud_flow(self, client: AsyncClient):
        """Test complete CRUD flow for extension."""
        # Create
        create_data = {
            "name": "Integration Test Feature",
            "description": "End-to-end test",
            "is_active": True,
        }
        create_response = await client.post("/api/example/features", json=create_data)
        assert create_response.status_code == 201
        feature = create_response.json()
        assert feature["name"] == create_data["name"]
        feature_id = feature["id"]

        # Read
        read_response = await client.get(f"/api/example/features/{feature_id}")
        assert read_response.status_code == 200
        assert read_response.json()["id"] == feature_id

        # Update
        update_data = {"description": "Updated description"}
        update_response = await client.patch(
            f"/api/example/features/{feature_id}", json=update_data
        )
        assert update_response.status_code == 200
        assert update_response.json()["description"] == update_data["description"]

        # List (verify feature exists)
        list_response = await client.get("/api/example/features")
        assert list_response.status_code == 200
        features = list_response.json()
        assert any(f["id"] == feature_id for f in features)

        # Delete
        delete_response = await client.delete(f"/api/example/features/{feature_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_deleted = await client.get(f"/api/example/features/{feature_id}")
        assert get_deleted.status_code == 404

    async def test_openapi_includes_extension(self, client: AsyncClient):
        """Test OpenAPI schema includes extension endpoints and tags."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        # Check tags include extension
        tags = schema.get("tags", [])
        tag_names = [tag["name"] for tag in tags]
        # Tag name is generated from extension name: _example -> " Example"
        assert any("Example" in tag for tag in tag_names)

        # Check extension endpoints are in paths
        paths = schema.get("paths", {})
        assert "/api/example/features" in paths
        assert "/api/example/features/{feature_id}" in paths

    async def test_extension_validation(self, client: AsyncClient):
        """Test extension validation works correctly."""
        # Test invalid data
        invalid_data = {"name": ""}  # Empty name should fail
        response = await client.post("/api/example/features", json=invalid_data)
        assert response.status_code == 422  # Validation error

        # Test valid data
        valid_data = {"name": "Valid Feature", "description": "Test", "is_active": True}
        response = await client.post("/api/example/features", json=valid_data)
        assert response.status_code == 201

    async def test_multiple_extensions_in_config(self):
        """Test configuration supports multiple extensions."""
        # This tests the CSV parsing
        test_cases = [
            ("", []),
            ("ext1", ["ext1"]),
            ("ext1,ext2", ["ext1", "ext2"]),
            ("ext1, ext2, ext3", ["ext1", "ext2", "ext3"]),
            ("  ext1  ,  ext2  ", ["ext1", "ext2"]),  # Whitespace handling
        ]

        from app.core.config import Settings

        for input_val, expected in test_cases:
            config = Settings.model_validate(
                {
                    "POSTGRES_USER": "test",
                    "POSTGRES_PASSWORD": "test",
                    "POSTGRES_DB": "test",
                    "POSTGRES_HOST": "localhost",
                    "POSTGRES_PORT": 5432,
                    "REDIS_HOST": "localhost",
                    "REDIS_PORT": 6379,
                    "CELERY_APP_NAME": "app",
                    "CELERY_TIMEZONE": "UTC",
                    "CELERY_TASK_TRACK_STARTED": True,
                    "CELERY_TASK_TIME_LIMIT": 1800,
                    "CELERY_TASK_SOFT_TIME_LIMIT": 1500,
                    "CELERY_RESULT_EXPIRES": 3600,
                    "CELERY_TASK_ACKS_LATE": True,
                    "CELERY_WORKER_PREFETCH_MULTIPLIER": 4,
                    "CELERY_WORKER_MAX_TASKS_PER_CHILD": 1000,
                    "FLOWER_PORT": 5555,
                    "ENABLED_EXTENSIONS": input_val,
                }
            )
            assert config.ENABLED_EXTENSIONS == expected, (
                f"Failed for input: {input_val}"
            )


class TestExtensionIsolation:
    """Test that core functionality works alongside extensions."""

    async def test_core_endpoints_work_with_extensions(self, client: AsyncClient):
        """Test core functionality works when extensions are enabled."""
        # Core endpoints should still work
        response = await client.get("/api/health")
        assert response.status_code == 200

        response = await client.get("/api/examples")
        assert response.status_code == 200

    async def test_openapi_includes_both_core_and_extensions(self, client: AsyncClient):
        """Test OpenAPI schema includes both core and extension endpoints."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

        tags = schema.get("tags", [])
        tag_names = [tag["name"] for tag in tags]

        # Both core and extension tags should be present
        assert "Health" in tag_names
        assert "Examples" in tag_names
        # Extension tag (formatted with title() from _example)
        assert any("Example" in tag for tag in tag_names)

        paths = schema.get("paths", {})
        # Core paths
        assert "/api/health" in paths
        assert "/api/examples" in paths
        # Extension paths
        assert "/api/example/features" in paths
