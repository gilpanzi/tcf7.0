# TCF Pricing Tool - Deployment Guide

## 🚀 Safe Database Deployment

This guide ensures your database admin interface works without committing production data to git.

### ✅ What's Protected in Git:
- **Production Data**: All `.db` files are excluded from git
- **Sensitive Info**: Database backups and data directories are excluded
- **Directory Structure**: Maintained with `.gitkeep` files

### 📁 Database Structure:
```
data/
├── fan_pricing.db          # Main production database (excluded)
└── central_database/
    └── all_projects.db     # Central database (excluded)

central_database/
├── all_projects.db         # Legacy central database (excluded)
└── project_*.db           # Individual project files (excluded)

database/
├── fan_weights.db          # Secondary database (excluded)
└── create_tables.sql       # Schema file (included in git)
```

### 🔧 Deployment Process:

1. **Fresh Deployment:**
   - App automatically creates databases using `schema.sql`
   - Database initialization runs on startup
   - Admin interface will work with empty databases initially

2. **Existing Deployment:**
   - Database admin interface automatically copies data to correct locations
   - Production data remains safe and accessible

### 🛡️ Security Features:
- ✅ Production data never committed to git
- ✅ Database schema and structure preserved
- ✅ Directory structure maintained
- ✅ Admin interface works immediately after deployment

### 📊 Admin Interface Access:
- **URL**: `/db-admin/`
- **Main Database**: View all application tables and data
- **Central Database**: View project and fan data
- **Features**: Browse, edit, add records, run SQL queries

### 🔄 Database Initialization:
The app automatically handles:
- Creating required tables
- Setting up database schema
- Copying databases to admin-accessible locations
- Maintaining data integrity

No manual database setup required! 