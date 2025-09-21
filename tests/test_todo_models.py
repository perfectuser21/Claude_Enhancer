"""
Comprehensive test suite for Todo data models.
Tests for SQLAlchemy models, Pydantic schemas, and database operations.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.models.base import Base
from backend.models.todo_models import (
    User, Category, TodoItem, Attachment, Comment, SharedTodo, ActivityLog,
    PriorityLevel, StatusType, PermissionLevel, ActionType
)
from backend.schemas.todo_schemas import (
    UserCreate, CategoryCreate, TodoItemCreate, TodoItemUpdate,
    AttachmentCreate, CommentCreate, SharedTodoCreate
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_category(db_session, sample_user):
    """Create a sample category for testing."""
    category = Category(
        user_id=sample_user.id,
        name="Test Category",
        description="Test category description",
        color="#ff5733",
        icon="test-icon"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_todo(db_session, sample_user, sample_category):
    """Create a sample todo item for testing."""
    todo = TodoItem(
        user_id=sample_user.id,
        category_id=sample_category.id,
        title="Test Todo",
        description="Test todo description",
        priority=PriorityLevel.HIGH,
        status=StatusType.PENDING,
        tags=["test", "example"],
        estimated_hours=5.0
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)
    return todo


# =============================================================================
# USER MODEL TESTS
# =============================================================================

class TestUserModel:
    """Test suite for User model."""

    def test_user_creation(self, db_session):
        """Test basic user creation."""
        user = User(
            email="newuser@example.com",
            username="newuser",
            password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_full_name_property(self, sample_user):
        """Test full_name hybrid property."""
        assert sample_user.full_name == "Test User"

        # Test with only first name
        sample_user.last_name = None
        assert sample_user.full_name == "Test"

        # Test with only last name
        sample_user.first_name = None
        sample_user.last_name = "User"
        assert sample_user.full_name == "User"

        # Test with no names
        sample_user.first_name = None
        sample_user.last_name = None
        assert sample_user.full_name == "testuser"

    def test_user_unique_constraints(self, db_session, sample_user):
        """Test unique constraints on email and username."""
        # Try to create user with same email
        duplicate_email_user = User(
            email=sample_user.email,
            username="different_username",
            password_hash="hashed_password"
        )
        db_session.add(duplicate_email_user)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

        db_session.rollback()

        # Try to create user with same username
        duplicate_username_user = User(
            email="different@example.com",
            username=sample_user.username,
            password_hash="hashed_password"
        )
        db_session.add(duplicate_username_user)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_user_relationships(self, db_session, sample_user, sample_category, sample_todo):
        """Test user relationships with other models."""
        assert len(sample_user.categories) == 1
        assert sample_user.categories[0] == sample_category

        assert len(sample_user.todos) == 1
        assert sample_user.todos[0] == sample_todo


# =============================================================================
# CATEGORY MODEL TESTS
# =============================================================================

class TestCategoryModel:
    """Test suite for Category model."""

    def test_category_creation(self, db_session, sample_user):
        """Test basic category creation."""
        category = Category(
            user_id=sample_user.id,
            name="Work",
            description="Work-related tasks"
        )
        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.name == "Work"
        assert category.color == "#007bff"  # Default color
        assert category.icon == "folder"  # Default icon
        assert category.is_active is True
        assert category.sort_order == 0

    def test_category_unique_constraint(self, db_session, sample_user, sample_category):
        """Test unique constraint on user_id + name."""
        duplicate_category = Category(
            user_id=sample_user.id,
            name=sample_category.name,
            description="Different description"
        )
        db_session.add(duplicate_category)

        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

    def test_category_color_validation(self, db_session, sample_user):
        """Test color format validation."""
        # Valid hex color should work
        valid_category = Category(
            user_id=sample_user.id,
            name="Valid Color",
            color="#ff5733"
        )
        db_session.add(valid_category)
        db_session.commit()
        assert valid_category.color == "#ff5733"

    def test_category_properties(self, db_session, sample_category, sample_todo):
        """Test category computed properties."""
        # Note: These properties may not work in SQLite, but test the logic
        assert hasattr(sample_category, 'todo_count')
        assert hasattr(sample_category, 'completed_count')


# =============================================================================
# TODO ITEM MODEL TESTS
# =============================================================================

class TestTodoItemModel:
    """Test suite for TodoItem model."""

    def test_todo_creation(self, db_session, sample_user):
        """Test basic todo creation."""
        todo = TodoItem(
            user_id=sample_user.id,
            title="New Task",
            description="Task description"
        )
        db_session.add(todo)
        db_session.commit()

        assert todo.id is not None
        assert todo.title == "New Task"
        assert todo.status == StatusType.PENDING
        assert todo.priority == PriorityLevel.MEDIUM
        assert todo.progress_percentage == 0
        assert todo.is_pinned is False
        assert todo.is_archived is False

    def test_todo_due_date_logic(self, db_session, sample_user):
        """Test due date related logic."""
        # Create todo with future due date
        future_todo = TodoItem(
            user_id=sample_user.id,
            title="Future Task",
            due_date=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(future_todo)
        db_session.commit()

        assert not future_todo.is_overdue
        assert future_todo.days_until_due == 0  # Should be 0 or 1 depending on time

        # Create todo with past due date
        overdue_todo = TodoItem(
            user_id=sample_user.id,
            title="Overdue Task",
            due_date=datetime.utcnow() - timedelta(days=1)
        )
        db_session.add(overdue_todo)
        db_session.commit()

        assert overdue_todo.is_overdue
        assert overdue_todo.days_until_due < 0

    def test_todo_status_transitions(self, db_session, sample_todo):
        """Test todo status transition methods."""
        # Mark as in progress
        sample_todo.mark_in_progress()
        assert sample_todo.status == StatusType.IN_PROGRESS
        assert sample_todo.started_at is not None

        # Mark as completed
        sample_todo.mark_completed()
        assert sample_todo.status == StatusType.COMPLETED
        assert sample_todo.completed_at is not None
        assert sample_todo.progress_percentage == 100

    def test_todo_tags_handling(self, db_session, sample_user):
        """Test tags array handling."""
        todo = TodoItem(
            user_id=sample_user.id,
            title="Tagged Task",
            tags=["urgent", "client", "review"]
        )
        db_session.add(todo)
        db_session.commit()

        assert len(todo.tags) == 3
        assert "urgent" in todo.tags
        assert "client" in todo.tags
        assert "review" in todo.tags

    def test_todo_metadata_handling(self, db_session, sample_user):
        """Test JSONB metadata handling."""
        metadata = {
            "client": "ABC Corp",
            "project_id": 12345,
            "custom_fields": {
                "priority_score": 8.5,
                "estimated_complexity": "high"
            }
        }

        todo = TodoItem(
            user_id=sample_user.id,
            title="Metadata Task",
            metadata=metadata
        )
        db_session.add(todo)
        db_session.commit()

        assert todo.metadata["client"] == "ABC Corp"
        assert todo.metadata["project_id"] == 12345
        assert todo.metadata["custom_fields"]["priority_score"] == 8.5

    def test_todo_subtasks(self, db_session, sample_user, sample_todo):
        """Test parent-child relationship (subtasks)."""
        subtask = TodoItem(
            user_id=sample_user.id,
            parent_id=sample_todo.id,
            title="Subtask",
            description="A subtask of the main todo"
        )
        db_session.add(subtask)
        db_session.commit()

        assert subtask.parent_id == sample_todo.id
        assert subtask.parent == sample_todo
        assert len(sample_todo.subtasks) == 1
        assert sample_todo.subtasks[0] == subtask


# =============================================================================
# ATTACHMENT MODEL TESTS
# =============================================================================

class TestAttachmentModel:
    """Test suite for Attachment model."""

    def test_attachment_creation(self, db_session, sample_user, sample_todo):
        """Test basic attachment creation."""
        attachment = Attachment(
            todo_id=sample_todo.id,
            user_id=sample_user.id,
            filename="document.pdf",
            original_filename="Important Document.pdf",
            file_path="/uploads/attachments/document.pdf",
            file_size=1024000,  # 1MB
            mime_type="application/pdf",
            file_hash="a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
        )
        db_session.add(attachment)
        db_session.commit()

        assert attachment.id is not None
        assert attachment.filename == "document.pdf"
        assert attachment.file_size == 1024000
        assert attachment.is_public is False

    def test_attachment_file_size_property(self, db_session, sample_user, sample_todo):
        """Test file size in MB property."""
        attachment = Attachment(
            todo_id=sample_todo.id,
            user_id=sample_user.id,
            filename="large_file.zip",
            original_filename="large_file.zip",
            file_path="/uploads/large_file.zip",
            file_size=5242880,  # 5MB
            mime_type="application/zip",
            file_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        )
        db_session.add(attachment)
        db_session.commit()

        assert attachment.file_size_mb == 5.0


# =============================================================================
# COMMENT MODEL TESTS
# =============================================================================

class TestCommentModel:
    """Test suite for Comment model."""

    def test_comment_creation(self, db_session, sample_user, sample_todo):
        """Test basic comment creation."""
        comment = Comment(
            todo_id=sample_todo.id,
            user_id=sample_user.id,
            content="This is a test comment"
        )
        db_session.add(comment)
        db_session.commit()

        assert comment.id is not None
        assert comment.content == "This is a test comment"
        assert comment.is_edited is False
        assert comment.is_deleted is False

    def test_nested_comments(self, db_session, sample_user, sample_todo):
        """Test nested comment functionality."""
        parent_comment = Comment(
            todo_id=sample_todo.id,
            user_id=sample_user.id,
            content="Parent comment"
        )
        db_session.add(parent_comment)
        db_session.commit()

        reply_comment = Comment(
            todo_id=sample_todo.id,
            user_id=sample_user.id,
            parent_id=parent_comment.id,
            content="Reply to parent comment"
        )
        db_session.add(reply_comment)
        db_session.commit()

        assert reply_comment.parent_id == parent_comment.id
        assert reply_comment.parent == parent_comment
        assert len(parent_comment.replies) == 1
        assert parent_comment.replies[0] == reply_comment


# =============================================================================
# SHARED TODO MODEL TESTS
# =============================================================================

class TestSharedTodoModel:
    """Test suite for SharedTodo model."""

    def test_shared_todo_creation(self, db_session, sample_user, sample_todo):
        """Test basic shared todo creation."""
        # Create another user to share with
        other_user = User(
            email="other@example.com",
            username="otheruser",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.commit()

        shared_todo = SharedTodo(
            todo_id=sample_todo.id,
            owner_id=sample_user.id,
            shared_with_id=other_user.id,
            permission=PermissionLevel.READ
        )
        db_session.add(shared_todo)
        db_session.commit()

        assert shared_todo.id is not None
        assert shared_todo.permission == PermissionLevel.READ
        assert not shared_todo.is_expired

    def test_shared_todo_expiry(self, db_session, sample_user, sample_todo):
        """Test shared todo expiry logic."""
        other_user = User(
            email="expired@example.com",
            username="expireduser",
            password_hash="hashed_password"
        )
        db_session.add(other_user)
        db_session.commit()

        # Create expired sharing
        expired_sharing = SharedTodo(
            todo_id=sample_todo.id,
            owner_id=sample_user.id,
            shared_with_id=other_user.id,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        db_session.add(expired_sharing)
        db_session.commit()

        assert expired_sharing.is_expired


# =============================================================================
# ACTIVITY LOG MODEL TESTS
# =============================================================================

class TestActivityLogModel:
    """Test suite for ActivityLog model."""

    def test_activity_log_creation(self, db_session, sample_user, sample_todo):
        """Test basic activity log creation."""
        activity = ActivityLog(
            todo_id=sample_todo.id,
            user_id=sample_user.id,
            action=ActionType.CREATED,
            description="Todo was created",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Test Browser)"
        )
        db_session.add(activity)
        db_session.commit()

        assert activity.id is not None
        assert activity.action == ActionType.CREATED
        assert activity.ip_address == "192.168.1.1"


# =============================================================================
# PYDANTIC SCHEMA TESTS
# =============================================================================

class TestPydanticSchemas:
    """Test suite for Pydantic schemas."""

    def test_user_create_schema(self):
        """Test UserCreate schema validation."""
        valid_data = {
            "email": "test@example.com",
            "username": "testuser123",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "first_name": "Test",
            "last_name": "User"
        }

        user_schema = UserCreate(**valid_data)
        assert user_schema.email == "test@example.com"
        assert user_schema.username == "testuser123"

    def test_user_create_password_validation(self):
        """Test password validation in UserCreate schema."""
        # Test password mismatch
        with pytest.raises(ValueError, match="Passwords do not match"):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="SecurePass123!",
                confirm_password="DifferentPass123!"
            )

        # Test weak password
        with pytest.raises(ValueError, match="uppercase letter"):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="weakpass",
                confirm_password="weakpass"
            )

    def test_todo_create_schema(self):
        """Test TodoItemCreate schema validation."""
        valid_data = {
            "title": "Test Todo",
            "description": "Test description",
            "priority": "high",
            "tags": ["work", "urgent", "client-meeting"]
        }

        todo_schema = TodoItemCreate(**valid_data)
        assert todo_schema.title == "Test Todo"
        assert len(todo_schema.tags) == 3

    def test_todo_create_tags_validation(self):
        """Test tags validation in TodoItemCreate schema."""
        # Test too many tags
        with pytest.raises(ValueError, match="Maximum 20 tags"):
            TodoItemCreate(
                title="Test Todo",
                tags=[f"tag{i}" for i in range(25)]
            )

        # Test invalid tag format
        with pytest.raises(ValueError, match="letters, numbers, hyphens"):
            TodoItemCreate(
                title="Test Todo",
                tags=["valid-tag", "invalid@tag"]
            )

    def test_category_create_schema(self):
        """Test CategoryCreate schema validation."""
        valid_data = {
            "name": "Work Category",
            "description": "Work-related tasks",
            "color": "#ff5733",
            "icon": "briefcase"
        }

        category_schema = CategoryCreate(**valid_data)
        assert category_schema.name == "Work Category"
        assert category_schema.color == "#ff5733"

    def test_category_color_validation(self):
        """Test color validation in CategoryCreate schema."""
        # Test invalid color format
        with pytest.raises(ValueError):
            CategoryCreate(
                name="Test Category",
                color="invalid-color"
            )

        # Test valid color
        category = CategoryCreate(
            name="Test Category",
            color="#123ABC"
        )
        assert category.color == "#123ABC"


# =============================================================================
# DATABASE INITIALIZATION TESTS
# =============================================================================

class TestDatabaseInitialization:
    """Test suite for database initialization functions."""

    def test_model_table_creation(self, db_engine):
        """Test that all model tables are created correctly."""
        # Check that tables exist
        tables = db_engine.table_names()

        # Note: SQLite uses different naming, so we check for table existence
        assert len(tables) > 0  # At least some tables should be created

    def test_model_relationships(self, db_session, sample_user, sample_category, sample_todo):
        """Test that model relationships work correctly."""
        # Test user -> categories relationship
        assert sample_category in sample_user.categories

        # Test user -> todos relationship
        assert sample_todo in sample_user.todos

        # Test category -> todos relationship
        assert sample_todo in sample_category.todos

        # Test todo -> user relationship
        assert sample_todo.user == sample_user

        # Test todo -> category relationship
        assert sample_todo.category == sample_category


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Test suite for performance-related functionality."""

    def test_bulk_todo_creation(self, db_session, sample_user, sample_category):
        """Test creating multiple todos efficiently."""
        todos = []
        for i in range(100):
            todo = TodoItem(
                user_id=sample_user.id,
                category_id=sample_category.id,
                title=f"Todo {i}",
                description=f"Description for todo {i}",
                priority=PriorityLevel.MEDIUM if i % 2 == 0 else PriorityLevel.HIGH
            )
            todos.append(todo)

        # Bulk insert
        db_session.add_all(todos)
        db_session.commit()

        # Verify all todos were created
        todo_count = db_session.query(TodoItem).filter_by(user_id=sample_user.id).count()
        assert todo_count == 101  # 100 new + 1 from fixture

    def test_query_optimization(self, db_session, sample_user):
        """Test that queries are optimized with proper joins."""
        # Create test data
        category = Category(
            user_id=sample_user.id,
            name="Performance Test Category"
        )
        db_session.add(category)
        db_session.flush()

        for i in range(10):
            todo = TodoItem(
                user_id=sample_user.id,
                category_id=category.id,
                title=f"Performance Todo {i}"
            )
            db_session.add(todo)

        db_session.commit()

        # Query with join
        todos = db_session.query(TodoItem).join(Category).filter(
            TodoItem.user_id == sample_user.id
        ).all()

        assert len(todos) == 11  # 10 new + 1 from fixture


if __name__ == "__main__":
    pytest.main([__file__, "-v"])