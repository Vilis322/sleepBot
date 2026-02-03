-- This script runs automatically when the PostgreSQL container is first initialized
-- It ensures the database user has all necessary permissions

-- Grant all privileges to sleepbot_user on the database
GRANT ALL PRIVILEGES ON DATABASE sleepbot_db TO sleepbot_user;

-- Connect to the sleepbot_db database
\c sleepbot_db

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO sleepbot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sleepbot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sleepbot_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sleepbot_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sleepbot_user;
