-- Projects table for storing project details
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enquiry_number TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    total_fans INTEGER NOT NULL,
    sales_engineer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fans table for storing individual fan data for each project
CREATE TABLE IF NOT EXISTS fans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    fan_number INTEGER NOT NULL,
    specifications TEXT,  -- JSON structure with fan specifications
    weights TEXT,         -- JSON structure with weight details
    costs TEXT,           -- JSON structure with cost details
    motor TEXT,           -- JSON structure with motor details
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_fans_project_id ON fans(project_id);
CREATE INDEX IF NOT EXISTS idx_projects_enquiry_number ON projects(enquiry_number);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default users with password 'tcfsales'
INSERT OR IGNORE INTO users (username, password, full_name, is_admin) VALUES
    ('abdul', 'tcfsales', 'Abdul Basidh', 1),
    ('pradeep', 'tcfsales', 'Pradeep', 0),
    ('satish', 'tcfsales', 'Satish', 0),
    ('franklin', 'tcfsales', 'Franklin', 0),
    ('muthu', 'tcfsales', 'Muthu', 0),
    ('raghul', 'tcfsales', 'Raghul', 0); 