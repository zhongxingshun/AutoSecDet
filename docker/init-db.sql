-- Initialize database with extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create default admin user (password: admin123)
-- Password hash generated with bcrypt, cost factor 12
-- Note: Change this password immediately after first login
INSERT INTO users (username, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'admin',
    '$2b$12$uKAGODfqLPE54lUBlQhEA.39yar2Xl0ZA0WahovDOqTlbVUijXUmy',
    'admin',
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (username) DO NOTHING;

-- Create default categories
INSERT INTO categories (name, description, sort_order, created_at, updated_at)
VALUES 
    ('身份认证', '登录、认证相关安全检测', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('访问控制', '权限、授权相关安全检测', 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('数据安全', '数据加密、传输安全检测', 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('网络安全', '端口、服务、协议安全检测', 4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('系统安全', '操作系统、配置安全检测', 5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (name) DO NOTHING;
