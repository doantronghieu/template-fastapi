"""Integration tests for Salesforce CRUD service.

Uses Task object for testing - standard, safe, simple fields.
Test records use TEST_CRUD_ prefix for easy identification.
"""

import uuid

import pytest

from app.integrations.salesforce.exceptions import SalesforceRecordNotFound
from app.integrations.salesforce.services.crud_service import CRUDService


def _test_subject() -> str:
    """Generate unique test subject."""
    return f"TEST_CRUD_{uuid.uuid4().hex[:8]}"


class TestCRUDLifecycle:
    """Test full CRUD lifecycle with Task object."""

    def test_create_read_update_delete(self, crud_service: CRUDService):
        """Test complete CRUD cycle."""
        subject = _test_subject()
        task_id = None

        try:
            # Create
            task_id = crud_service.create(
                "Task",
                {"Subject": subject, "Status": "Not Started", "Priority": "Normal"},
            )
            assert task_id is not None
            assert len(task_id) == 18  # Salesforce ID length

            # Read
            task = crud_service.get("Task", task_id)
            assert task["Subject"] == subject
            assert task["Status"] == "Not Started"
            assert task["Priority"] == "Normal"

            # Update
            success = crud_service.update(
                "Task",
                task_id,
                {"Status": "Completed", "Description": "Updated by test"},
            )
            assert success is True

            # Verify update
            updated_task = crud_service.get("Task", task_id)
            assert updated_task["Status"] == "Completed"
            assert updated_task["Description"] == "Updated by test"

            # Delete
            success = crud_service.delete("Task", task_id)
            assert success is True
            task_id = None  # Mark as deleted

        finally:
            # Cleanup: ensure test record is deleted
            if task_id:
                try:
                    crud_service.delete("Task", task_id)
                except Exception:
                    pass


class TestCreate:
    """Test create operations."""

    def test_create_returns_id(self, crud_service: CRUDService):
        """Create should return valid Salesforce ID."""
        subject = _test_subject()
        task_id = None

        try:
            task_id = crud_service.create(
                "Task",
                {"Subject": subject, "Status": "Not Started"},
            )
            assert task_id is not None
            assert isinstance(task_id, str)
            assert len(task_id) == 18
        finally:
            if task_id:
                crud_service.delete("Task", task_id)


class TestRead:
    """Test read operations."""

    def test_get_existing_record(self, crud_service: CRUDService):
        """Get should return record data."""
        subject = _test_subject()
        task_id = crud_service.create(
            "Task",
            {"Subject": subject, "Status": "Not Started"},
        )

        try:
            task = crud_service.get("Task", task_id)
            assert task["Id"] == task_id
            assert task["Subject"] == subject
        finally:
            crud_service.delete("Task", task_id)

    def test_get_nonexistent_record(self, crud_service: CRUDService):
        """Get non-existent record should raise SalesforceRecordNotFound."""
        # Create and delete a record to get a valid-format ID that no longer exists
        subject = _test_subject()
        task_id = crud_service.create(
            "Task",
            {"Subject": subject, "Status": "Not Started"},
        )
        crud_service.delete("Task", task_id)

        with pytest.raises(SalesforceRecordNotFound):
            crud_service.get("Task", task_id)


class TestUpdate:
    """Test update operations."""

    def test_update_single_field(self, crud_service: CRUDService):
        """Update should modify specified field."""
        subject = _test_subject()
        task_id = crud_service.create(
            "Task",
            {"Subject": subject, "Status": "Not Started"},
        )

        try:
            success = crud_service.update("Task", task_id, {"Status": "In Progress"})
            assert success is True

            task = crud_service.get("Task", task_id)
            assert task["Status"] == "In Progress"
        finally:
            crud_service.delete("Task", task_id)

    def test_update_multiple_fields(self, crud_service: CRUDService):
        """Update should modify multiple fields."""
        subject = _test_subject()
        task_id = crud_service.create(
            "Task",
            {"Subject": subject, "Status": "Not Started", "Priority": "Normal"},
        )

        try:
            success = crud_service.update(
                "Task",
                task_id,
                {"Status": "Completed", "Priority": "High", "Description": "Done"},
            )
            assert success is True

            task = crud_service.get("Task", task_id)
            assert task["Status"] == "Completed"
            assert task["Priority"] == "High"
            assert task["Description"] == "Done"
        finally:
            crud_service.delete("Task", task_id)


class TestDelete:
    """Test delete operations."""

    def test_delete_existing_record(self, crud_service: CRUDService):
        """Delete should remove record."""
        subject = _test_subject()
        task_id = crud_service.create(
            "Task",
            {"Subject": subject, "Status": "Not Started"},
        )

        success = crud_service.delete("Task", task_id)
        assert success is True

        # Verify deletion
        with pytest.raises(SalesforceRecordNotFound):
            crud_service.get("Task", task_id)


class TestQuery:
    """Test query operations."""

    def test_query_returns_records(self, crud_service: CRUDService):
        """Query should return list of records."""
        subject = _test_subject()
        task_id = crud_service.create(
            "Task",
            {"Subject": subject, "Status": "Not Started"},
        )

        try:
            records = crud_service.query(
                f"SELECT Id, Subject, Status FROM Task WHERE Subject = '{subject}'"
            )
            assert len(records) == 1
            assert records[0]["Subject"] == subject
        finally:
            crud_service.delete("Task", task_id)

    def test_query_empty_result(self, crud_service: CRUDService):
        """Query with no matches should return empty list."""
        records = crud_service.query(
            "SELECT Id FROM Task WHERE Subject = 'NONEXISTENT_TEST_RECORD_12345'"
        )
        assert records == []
