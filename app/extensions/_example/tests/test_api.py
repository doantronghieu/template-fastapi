"""Tests for _example extension API endpoints."""


async def test_list_features(client):
    """Test listing example features."""
    response = await client.get("/api/example/features")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_create_feature(client):
    """Test creating example feature."""
    data = {
        "name": "Test Feature",
        "description": "Test description",
        "is_active": True,
    }
    response = await client.post("/api/example/features", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == data["name"]
    assert result["description"] == data["description"]
    assert "id" in result


async def test_get_feature(client):
    """Test getting single feature."""
    # Create feature first
    create_data = {"name": "Get Test", "description": "Test"}
    create_response = await client.post("/api/example/features", json=create_data)
    feature_id = create_response.json()["id"]

    # Get feature
    response = await client.get(f"/api/example/features/{feature_id}")
    assert response.status_code == 200
    assert response.json()["id"] == feature_id


async def test_get_nonexistent_feature(client):
    """Test getting nonexistent feature returns 404."""
    response = await client.get("/api/example/features/99999")
    assert response.status_code == 404


async def test_update_feature(client):
    """Test updating feature."""
    # Create feature first
    create_data = {"name": "Update Test", "description": "Original"}
    create_response = await client.post("/api/example/features", json=create_data)
    feature_id = create_response.json()["id"]

    # Update feature
    update_data = {"description": "Updated description"}
    response = await client.patch(
        f"/api/example/features/{feature_id}", json=update_data
    )
    assert response.status_code == 200
    result = response.json()
    assert result["description"] == update_data["description"]
    assert result["name"] == create_data["name"]  # Unchanged


async def test_delete_feature(client):
    """Test deleting feature."""
    # Create feature first
    create_data = {"name": "Delete Test", "description": "To be deleted"}
    create_response = await client.post("/api/example/features", json=create_data)
    feature_id = create_response.json()["id"]

    # Delete feature
    response = await client.delete(f"/api/example/features/{feature_id}")
    assert response.status_code == 204

    # Verify deletion
    get_response = await client.get(f"/api/example/features/{feature_id}")
    assert get_response.status_code == 404
