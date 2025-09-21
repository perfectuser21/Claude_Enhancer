-- =============================================================================
-- Todo Data Model - PostgreSQL Schema
-- Production-ready todo system with advanced features
-- =============================================================================

-- Create schema for todo system
CREATE SCHEMA IF NOT EXISTS todo;

-- Enable UUID extension for better primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- USERS TABLE (if not exists)
-- =============================================================================
CREATE TABLE IF NOT EXISTS todo.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT username_format CHECK (username ~* '^[A-Za-z0-9_]{3,}$')
);

-- =============================================================================
-- TODO CATEGORIES TABLE
-- =============================================================================
CREATE TABLE todo.categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#007bff', -- Hex color code
    icon VARCHAR(50) DEFAULT 'folder',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_category_per_user UNIQUE (user_id, name),
    CONSTRAINT color_hex_format CHECK (color ~* '^#[0-9A-Fa-f]{6}$')
);

-- =============================================================================
-- TODO ITEMS TABLE
-- =============================================================================
CREATE TYPE todo.priority_level AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE todo.status_type AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'on_hold');

CREATE TABLE todo.items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES todo.categories(id) ON DELETE SET NULL,
    parent_id UUID REFERENCES todo.items(id) ON DELETE CASCADE, -- For subtasks

    -- Core fields
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status todo.status_type DEFAULT 'pending',
    priority todo.priority_level DEFAULT 'medium',

    -- Dates and deadlines
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,

    -- Organization
    sort_order INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,

    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    estimated_hours DECIMAL(5,2) CHECK (estimated_hours >= 0),
    actual_hours DECIMAL(5,2) CHECK (actual_hours >= 0),

    -- Metadata
    tags TEXT[], -- Array of tags
    metadata JSONB DEFAULT '{}', -- Flexible metadata storage

    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT title_not_empty CHECK (LENGTH(TRIM(title)) > 0),
    CONSTRAINT completed_at_logic CHECK (
        (status = 'completed' AND completed_at IS NOT NULL) OR
        (status != 'completed' AND completed_at IS NULL)
    ),
    CONSTRAINT progress_status_logic CHECK (
        (status = 'completed' AND progress_percentage = 100) OR
        (status != 'completed')
    )
);

-- =============================================================================
-- TODO ATTACHMENTS TABLE
-- =============================================================================
CREATE TABLE todo.attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    todo_id UUID NOT NULL REFERENCES todo.items(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,

    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    mime_type VARCHAR(100) NOT NULL,

    -- Security
    file_hash VARCHAR(64) NOT NULL, -- SHA-256 hash
    is_public BOOLEAN DEFAULT FALSE,

    -- Metadata
    description TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT filename_not_empty CHECK (LENGTH(TRIM(filename)) > 0),
    CONSTRAINT file_size_limit CHECK (file_size <= 10485760) -- 10MB limit
);

-- =============================================================================
-- TODO COMMENTS TABLE
-- =============================================================================
CREATE TABLE todo.comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    todo_id UUID NOT NULL REFERENCES todo.items(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES todo.comments(id) ON DELETE CASCADE, -- For nested comments

    content TEXT NOT NULL,
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT content_not_empty CHECK (LENGTH(TRIM(content)) > 0)
);

-- =============================================================================
-- TODO SHARING TABLE
-- =============================================================================
CREATE TYPE todo.permission_level AS ENUM ('read', 'write', 'admin');

CREATE TABLE todo.shared_todos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    todo_id UUID NOT NULL REFERENCES todo.items(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,
    shared_with_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,
    permission todo.permission_level DEFAULT 'read',

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT unique_sharing UNIQUE (todo_id, shared_with_id),
    CONSTRAINT no_self_sharing CHECK (owner_id != shared_with_id)
);

-- =============================================================================
-- TODO HISTORY/AUDIT TABLE
-- =============================================================================
CREATE TYPE todo.action_type AS ENUM ('created', 'updated', 'deleted', 'completed', 'reopened', 'assigned', 'commented');

CREATE TABLE todo.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    todo_id UUID REFERENCES todo.items(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES todo.users(id) ON DELETE CASCADE,
    action todo.action_type NOT NULL,

    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    description TEXT,

    -- IP and user agent for security
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PERFORMANCE INDEXES
-- =============================================================================

-- Users table indexes
CREATE INDEX idx_users_email ON todo.users(email);
CREATE INDEX idx_users_username ON todo.users(username);
CREATE INDEX idx_users_active ON todo.users(is_active) WHERE is_active = TRUE;

-- Categories table indexes
CREATE INDEX idx_categories_user_id ON todo.categories(user_id);
CREATE INDEX idx_categories_active ON todo.categories(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_categories_sort_order ON todo.categories(user_id, sort_order);

-- Todo items table indexes (most critical for performance)
CREATE INDEX idx_todos_user_id ON todo.items(user_id);
CREATE INDEX idx_todos_status ON todo.items(user_id, status);
CREATE INDEX idx_todos_priority ON todo.items(user_id, priority);
CREATE INDEX idx_todos_due_date ON todo.items(user_id, due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_todos_category ON todo.items(category_id) WHERE category_id IS NOT NULL;
CREATE INDEX idx_todos_parent ON todo.items(parent_id) WHERE parent_id IS NOT NULL;
CREATE INDEX idx_todos_archived ON todo.items(user_id, is_archived);
CREATE INDEX idx_todos_pinned ON todo.items(user_id, is_pinned) WHERE is_pinned = TRUE;
CREATE INDEX idx_todos_created_at ON todo.items(user_id, created_at);
CREATE INDEX idx_todos_updated_at ON todo.items(user_id, updated_at);

-- Full-text search index for todo content
CREATE INDEX idx_todos_search ON todo.items USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Tags search index
CREATE INDEX idx_todos_tags ON todo.items USING gin(tags) WHERE tags IS NOT NULL;

-- Attachments indexes
CREATE INDEX idx_attachments_todo_id ON todo.attachments(todo_id);
CREATE INDEX idx_attachments_user_id ON todo.attachments(user_id);
CREATE INDEX idx_attachments_hash ON todo.attachments(file_hash);

-- Comments indexes
CREATE INDEX idx_comments_todo_id ON todo.comments(todo_id);
CREATE INDEX idx_comments_user_id ON todo.comments(user_id);
CREATE INDEX idx_comments_parent ON todo.comments(parent_id) WHERE parent_id IS NOT NULL;

-- Sharing indexes
CREATE INDEX idx_shared_todos_owner ON todo.shared_todos(owner_id);
CREATE INDEX idx_shared_todos_shared_with ON todo.shared_todos(shared_with_id);
CREATE INDEX idx_shared_todos_todo ON todo.shared_todos(todo_id);

-- Activity log indexes
CREATE INDEX idx_activity_log_todo_id ON todo.activity_log(todo_id);
CREATE INDEX idx_activity_log_user_id ON todo.activity_log(user_id);
CREATE INDEX idx_activity_log_created_at ON todo.activity_log(created_at);
CREATE INDEX idx_activity_log_action ON todo.activity_log(action);

-- =============================================================================
-- TRIGGERS FOR AUTO-UPDATE TIMESTAMPS
-- =============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION todo.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON todo.users
    FOR EACH ROW EXECUTE FUNCTION todo.update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON todo.categories
    FOR EACH ROW EXECUTE FUNCTION todo.update_updated_at_column();

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON todo.items
    FOR EACH ROW EXECUTE FUNCTION todo.update_updated_at_column();

CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON todo.comments
    FOR EACH ROW EXECUTE FUNCTION todo.update_updated_at_column();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE todo.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo.items ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo.attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo.shared_todos ENABLE ROW LEVEL SECURITY;
ALTER TABLE todo.activity_log ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_policy ON todo.users FOR ALL USING (id = current_setting('app.current_user_id')::UUID);

-- Categories belong to users
CREATE POLICY categories_policy ON todo.categories FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

-- Todos belong to users or are shared with them
CREATE POLICY todos_owner_policy ON todo.items FOR ALL USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY todos_shared_policy ON todo.items FOR SELECT USING (
    id IN (
        SELECT todo_id FROM todo.shared_todos
        WHERE shared_with_id = current_setting('app.current_user_id')::UUID
    )
);

-- Attachments follow todo permissions
CREATE POLICY attachments_policy ON todo.attachments FOR ALL USING (
    todo_id IN (
        SELECT id FROM todo.items
        WHERE user_id = current_setting('app.current_user_id')::UUID
        OR id IN (
            SELECT todo_id FROM todo.shared_todos
            WHERE shared_with_id = current_setting('app.current_user_id')::UUID
        )
    )
);

-- Comments follow todo permissions
CREATE POLICY comments_policy ON todo.comments FOR ALL USING (
    todo_id IN (
        SELECT id FROM todo.items
        WHERE user_id = current_setting('app.current_user_id')::UUID
        OR id IN (
            SELECT todo_id FROM todo.shared_todos
            WHERE shared_with_id = current_setting('app.current_user_id')::UUID
        )
    )
);

-- Sharing policies
CREATE POLICY shared_todos_owner_policy ON todo.shared_todos FOR ALL USING (owner_id = current_setting('app.current_user_id')::UUID);
CREATE POLICY shared_todos_recipient_policy ON todo.shared_todos FOR SELECT USING (shared_with_id = current_setting('app.current_user_id')::UUID);

-- Activity log follows todo permissions
CREATE POLICY activity_log_policy ON todo.activity_log FOR ALL USING (
    todo_id IN (
        SELECT id FROM todo.items
        WHERE user_id = current_setting('app.current_user_id')::UUID
        OR id IN (
            SELECT todo_id FROM todo.shared_todos
            WHERE shared_with_id = current_setting('app.current_user_id')::UUID
        )
    )
);

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to get user's todo statistics
CREATE OR REPLACE FUNCTION todo.get_user_stats(p_user_id UUID)
RETURNS TABLE (
    total_todos BIGINT,
    completed_todos BIGINT,
    pending_todos BIGINT,
    overdue_todos BIGINT,
    completion_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_todos,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::BIGINT as completed_todos,
        COUNT(CASE WHEN status = 'pending' THEN 1 END)::BIGINT as pending_todos,
        COUNT(CASE WHEN due_date < CURRENT_TIMESTAMP AND status != 'completed' THEN 1 END)::BIGINT as overdue_todos,
        CASE
            WHEN COUNT(*) > 0 THEN
                ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / COUNT(*)::DECIMAL * 100), 2)
            ELSE 0.00
        END as completion_rate
    FROM todo.items
    WHERE user_id = p_user_id AND is_archived = FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to search todos with full-text search
CREATE OR REPLACE FUNCTION todo.search_todos(
    p_user_id UUID,
    p_search_term TEXT,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(255),
    description TEXT,
    status todo.status_type,
    priority todo.priority_level,
    due_date TIMESTAMPTZ,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.title,
        i.description,
        i.status,
        i.priority,
        i.due_date,
        ts_rank(to_tsvector('english', i.title || ' ' || COALESCE(i.description, '')), plainto_tsquery('english', p_search_term)) as rank
    FROM todo.items i
    WHERE i.user_id = p_user_id
        AND i.is_archived = FALSE
        AND to_tsvector('english', i.title || ' ' || COALESCE(i.description, '')) @@ plainto_tsquery('english', p_search_term)
    ORDER BY rank DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- SAMPLE DATA (for development/testing)
-- =============================================================================

-- Insert sample categories (optional, for testing)
/*
INSERT INTO todo.categories (user_id, name, description, color, icon) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Work', 'Work-related tasks', '#dc3545', 'briefcase'),
    ('00000000-0000-0000-0000-000000000001', 'Personal', 'Personal tasks and goals', '#28a745', 'user'),
    ('00000000-0000-0000-0000-000000000001', 'Health', 'Health and fitness tasks', '#17a2b8', 'heart'),
    ('00000000-0000-0000-0000-000000000001', 'Learning', 'Education and skill development', '#ffc107', 'book');
*/

-- =============================================================================
-- PERFORMANCE ANALYSIS QUERIES
-- =============================================================================

-- Query to analyze table sizes
/*
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals
FROM pg_stats
WHERE schemaname = 'todo'
ORDER BY tablename, attname;
*/

-- Query to check index usage
/*
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'todo'
ORDER BY idx_scan DESC;
*/