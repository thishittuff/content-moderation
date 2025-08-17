-- PostgreSQL initialization script for Content Moderation Service

-- Create database if it doesn't exist
-- (This will be handled by Docker environment variables)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE content_type AS ENUM ('text', 'image');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE moderation_status AS ENUM ('pending', 'processing', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE content_classification AS ENUM ('safe', 'toxic', 'spam', 'harassment', 'inappropriate');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_channel AS ENUM ('email', 'slack');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create tables
CREATE TABLE IF NOT EXISTS moderation_requests (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255) NOT NULL,
    content_type content_type NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    status moderation_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_results (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES moderation_requests(id) ON DELETE CASCADE,
    classification content_classification NOT NULL,
    confidence FLOAT NOT NULL,
    reasoning TEXT,
    llm_response TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES moderation_requests(id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    status VARCHAR(50) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_moderation_requests_email_status ON moderation_requests(email_id, status);
CREATE INDEX IF NOT EXISTS idx_moderation_requests_content_hash ON moderation_requests(content_hash);
CREATE INDEX IF NOT EXISTS idx_moderation_requests_created_at ON moderation_requests(created_at);

CREATE INDEX IF NOT EXISTS idx_moderation_results_request_id ON moderation_results(request_id);
CREATE INDEX IF NOT EXISTS idx_moderation_results_classification ON moderation_results(classification);
CREATE INDEX IF NOT EXISTS idx_moderation_results_created_at ON moderation_results(created_at);

CREATE INDEX IF NOT EXISTS idx_notification_logs_request_channel ON notification_logs(request_id, channel);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at ON notification_logs(sent_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_moderation_requests_updated_at ON moderation_requests;
CREATE TRIGGER update_moderation_requests_updated_at
    BEFORE UPDATE ON moderation_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
INSERT INTO moderation_requests (email_id, content_type, content_hash, status) VALUES
    ('test@example.com', 'text', 'sample_hash_1', 'completed'),
    ('user@example.com', 'image', 'sample_hash_2', 'pending')
ON CONFLICT (content_hash) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO user;

-- Create a view for analytics
CREATE OR REPLACE VIEW user_analytics_summary AS
SELECT 
    mr.email_id,
    COUNT(mr.id) as total_requests,
    COUNT(CASE WHEN mres.classification = 'safe' THEN 1 END) as safe_content,
    COUNT(CASE WHEN mres.classification != 'safe' THEN 1 END) as inappropriate_content,
    COUNT(CASE WHEN mr.status = 'pending' THEN 1 END) as pending_requests,
    MAX(mr.created_at) as last_request_at
FROM moderation_requests mr
LEFT JOIN moderation_results mres ON mr.id = mres.request_id
GROUP BY mr.email_id;

-- Grant permissions on view
GRANT SELECT ON user_analytics_summary TO user;
