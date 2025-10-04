import os
import shutil
import sqlite3
from flask import Blueprint, redirect, session, request, url_for
from flask_basicauth import BasicAuth
import logging
import html

# Simple database admin interface
logger = logging.getLogger(__name__)

# Dictionary to store the database paths - now using unified database
DATABASE_PATHS = {
    'unified': 'data/fan_pricing.db'
}

# Create Blueprint for database admin routes
db_admin_bp = Blueprint('db_admin', __name__)

# Define routes on the blueprint before it gets registered
@db_admin_bp.route('/')
def index():
    """Redirect to unified database view."""
    return redirect('/db-admin/view/unified')

@db_admin_bp.route('/view/<db_name>')
def view_db(db_name):
    """Show database tables list."""
    if db_name not in DATABASE_PATHS:
        return "Database not found", 404
    
    db_path = DATABASE_PATHS[db_name]
    
    # Ensure the unified database exists
    if not os.path.exists(db_path):
        return f"Unified database file not found at {db_path}", 404
    
    # Get list of tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Create HTML for table list
    table_links = ""
    for table in tables:
        table_links += f'<li><a href="/db-admin/view-table/{db_name}/{table}">{table}</a></li>'
    
    # Create HTML content
    db_title = "Unified Database"
    html_content = f"""
    <html>
    <head>
        <title>{db_title} - TCF Database Admin</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }}
            h1 {{
                color: #333;
            }}
            .back-link {{
                margin: 10px 0 20px 0;
            }}
            .back-link a {{
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                text-decoration: none;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <h1>{db_title}</h1>
        <div class="back-link">
            <a href="/">← Back to Main App</a>
        </div>
        
        <div>
            <form method="post" action="/db-admin/execute-sql/{db_name}">
                <h3>Run SQL Query</h3>
                <textarea name="sql_query" style="width: 100%; height: 100px;"></textarea>
                <button type="submit" style="padding: 5px 10px; margin-top: 10px;">Execute</button>
            </form>
        </div>
        
        <h3>Tables</h3>
        <div id="tables">
            <ul>
                {table_links}
            </ul>
        </div>
    </body>
    </html>
    """
    return html_content

@db_admin_bp.route('/view-table/<db_name>/<table_name>')
@db_admin_bp.route('/view-table/<db_name>/<table_name>/<int:page>')
def view_table(db_name, table_name, page=1):
    """View a specific table from the database."""
    if db_name not in DATABASE_PATHS:
        return "Database not found", 404
    
    db_path = DATABASE_PATHS[db_name]
    rows_per_page = 500  # Increased from 100 to 500 rows per page
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Get total count of rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        
        # Calculate total pages
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page
        
        # Ensure page is within valid range
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages
        
        # Calculate offset
        offset = (page - 1) * rows_per_page
        
        # Get the table data with pagination
        cursor.execute(f"SELECT rowid, * FROM {table_name} LIMIT {rows_per_page} OFFSET {offset}")
        rows = cursor.fetchall()
        
        conn.close()
        
        # Build table header HTML
        headers = "<th>Actions</th>"
        for col in columns:
            headers += f"<th>{html.escape(col)}</th>"
            
        # Build table rows HTML
        table_rows = ""
        for row in rows:
            rowid = row[0]
            
            table_rows += "<tr>"
            # Add action buttons
            edit_url = f"/db-admin/edit-record/{db_name}/{table_name}/{rowid}"
            delete_url = f"/db-admin/delete-record/{db_name}/{table_name}/{rowid}"
            
            table_rows += f"""<td>
                <a href='{edit_url}' class='edit-link'>Edit</a> | 
                <a href='{delete_url}' class='delete-link' 
                   onclick='return confirm("Are you sure you want to delete this record?")'>Delete</a>
            </td>"""
            
            # Add data cells
            for i in range(1, len(row)):
                val = row[i] if row[i] is not None else ""
                table_rows += f"<td>{html.escape(str(val))}</td>"
            
            table_rows += "</tr>"
        
        # Build pagination controls
        pagination = ""
        if total_pages > 1:
            pagination = "<div class='pagination'>"
            
            # Previous button
            if page > 1:
                pagination += f"<a href='/db-admin/view-table/{db_name}/{table_name}/{page-1}' class='page-link'>Previous</a>"
            
            # Page numbers
            max_pages_to_show = 7
            start_page = max(1, page - max_pages_to_show // 2)
            end_page = min(total_pages, start_page + max_pages_to_show - 1)
            
            for p in range(start_page, end_page + 1):
                if p == page:
                    pagination += f"<span class='current-page'>{p}</span>"
                else:
                    pagination += f"<a href='/db-admin/view-table/{db_name}/{table_name}/{p}' class='page-link'>{p}</a>"
            
            # Next button
            if page < total_pages:
                pagination += f"<a href='/db-admin/view-table/{db_name}/{table_name}/{page+1}' class='page-link'>Next</a>"
            
            pagination += "</div>"
        
        # Build the complete HTML
        html_content = f"""
        <html>
        <head>
            <title>Table: {table_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .back-link {{
                    margin-bottom: 20px;
                }}
                .action-buttons {{
                    margin: 20px 0;
                }}
                .action-buttons a {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 12px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-right: 10px;
                }}
                .edit-link {{
                    color: blue;
                    text-decoration: underline;
                    cursor: pointer;
                }}
                .delete-link {{
                    color: red;
                    text-decoration: underline;
                    cursor: pointer;
                }}
                .pagination {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .page-link {{
                    display: inline-block;
                    padding: 5px 10px;
                    margin: 0 3px;
                    border: 1px solid #ddd;
                    background-color: #f8f8f8;
                    color: #333;
                    text-decoration: none;
                    border-radius: 3px;
                }}
                .page-link:hover {{
                    background-color: #ddd;
                }}
                .current-page {{
                    display: inline-block;
                    padding: 5px 10px;
                    margin: 0 3px;
                    border: 1px solid #4CAF50;
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 3px;
                }}
            </style>
        </head>
        <body>
            <div class="back-link">
                <a href="/db-admin/view/{db_name}">← Back to {db_name} Database</a>
            </div>
            <h2>Table: {table_name}</h2>
            
            <div class="action-buttons">
                <a href="/db-admin/add-record/{db_name}/{table_name}">Add New Record</a>
            </div>
            
            <table>
                <tr>
                    {headers}
                </tr>
                {table_rows}
            </table>
            
            {pagination}
            
            <p>Showing page {page} of {total_pages} ({total_rows} total records, {rows_per_page} per page)</p>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"Error viewing table: {str(e)}", 500

@db_admin_bp.route('/execute-sql/<db_name>', methods=['POST'])
def execute_sql(db_name):
    """Execute SQL query on the selected database."""
    if db_name not in DATABASE_PATHS:
        return "Database not found", 404
    
    db_path = DATABASE_PATHS[db_name]
    sql_query = request.form.get('sql_query', '')
    
    if not sql_query:
        return "No SQL query provided", 400
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Determine if this is a SELECT query
        is_select = sql_query.strip().upper().startswith("SELECT")
        
        if is_select:
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Generate HTML table headers
            table_headers = "<tr>"
            for col in columns:
                table_headers += f"<th style='padding: 8px;'>{html.escape(col)}</th>"
            table_headers += "</tr>"
            
            # Generate HTML table rows
            table_rows = ""
            for row in rows:
                table_rows += "<tr>"
                for val in row:
                    val_str = str(val) if val is not None else ""
                    table_rows += f"<td style='padding: 8px;'>{html.escape(val_str)}</td>"
                table_rows += "</tr>"
            
            # Full results table
            result_html = f"""
            <h3>Query Results</h3>
            <table border='1' style='border-collapse: collapse; width: 100%;'>
                {table_headers}
                {table_rows}
            </table>
            """
        else:
            cursor.execute(sql_query)
            conn.commit()
            result_html = f"<p>Query executed successfully. {cursor.rowcount} rows affected.</p>"
        
        conn.close()
        
        # Build final HTML
        html_content = f"""
        <html>
        <head>
            <title>SQL Query Results</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                .back-link {{
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="back-link">
                <a href="/db-admin/view/{db_name}">← Back to {db_name} Database</a>
            </div>
            <h2>SQL Query</h2>
            <pre style="background-color: #f5f5f5; padding: 10px;">{html.escape(sql_query)}</pre>
            {result_html}
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        error_html = f"""
        <html>
        <head>
            <title>SQL Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                .error {{
                    color: red;
                    padding: 10px;
                    background-color: #ffeeee;
                }}
                .back-link {{
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="back-link">
                <a href="/db-admin/view/{db_name}">← Back to {db_name} Database</a>
            </div>
            <h2>SQL Error</h2>
            <div class="error">{html.escape(str(e))}</div>
            <h3>Your Query</h3>
            <pre style="background-color: #f5f5f5; padding: 10px;">{html.escape(sql_query)}</pre>
        </body>
        </html>
        """
        return error_html

@db_admin_bp.route('/add-record/<db_name>/<table_name>', methods=['GET', 'POST'])
def add_record(db_name, table_name):
    """Add a new record to the table."""
    if db_name not in DATABASE_PATHS:
        return "Database not found", 404
    
    db_path = DATABASE_PATHS[db_name]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        columns = [row[1] for row in columns_info]
        column_types = {row[1]: row[2] for row in columns_info}
        
        if request.method == 'POST':
            # Extract values from form and convert to appropriate types
            values = []
            for col in columns:
                value = request.form.get(col, '')
                col_type = column_types[col]
                
                # Convert empty string to None
                if not value:
                    values.append(None)
                    continue
                
                # Convert based on column type
                if col_type == 'INTEGER':
                    try:
                        values.append(int(value))
                    except ValueError:
                        return f"Invalid integer value for column {col}: {value}", 400
                elif col_type == 'REAL':
                    try:
                        values.append(float(value))
                    except ValueError:
                        return f"Invalid float value for column {col}: {value}", 400
                else:  # TEXT or other types
                    values.append(value)
            
            # Insert the new record
            placeholders = ', '.join(['?' for _ in columns])
            cols = ', '.join([f'"{col}"' for col in columns])
            cursor.execute(f'INSERT INTO "{table_name}" ({cols}) VALUES ({placeholders})', values)
            conn.commit()
            conn.close()
            
            return redirect(f'/db-admin/view-table/{db_name}/{table_name}')
        
        # Generate form for adding a new record
        form_fields = ''
        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2]
            input_type = 'number' if col_type in ('INTEGER', 'REAL') else 'text'
            step = '0.01' if col_type == 'REAL' else '1'
            form_fields += f"""
            <div class="form-group">
                <label for="{col_name}">{col_name}</label>
                <input type="{input_type}" id="{col_name}" name="{col_name}" class="form-control" step="{step}">
            </div>
            """
        
        conn.close()
        
        html_content = f"""
        <html>
        <head>
            <title>Add Record - {table_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                .back-link {{
                    margin-bottom: 20px;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                .form-control {{
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                    cursor: pointer;
                    border: none;
                }}
            </style>
        </head>
        <body>
            <div class="back-link">
                <a href="/db-admin/view-table/{db_name}/{table_name}">← Back to Table</a>
            </div>
            <h2>Add New Record to {table_name}</h2>
            <form method="post">
                {form_fields}
                <button type="submit" class="btn">Save Record</button>
            </form>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"Error adding record: {str(e)}", 500

@db_admin_bp.route('/edit-record/<db_name>/<table_name>/<int:rowid>', methods=['GET', 'POST'])
def edit_record(db_name, table_name, rowid):
    """Edit an existing record in the table."""
    if db_name not in DATABASE_PATHS:
        return "Database not found", 404
    
    db_path = DATABASE_PATHS[db_name]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        columns = [row[1] for row in columns_info]
        
        if request.method == 'POST':
            # Extract updated values from form
            set_clauses = []
            values = []
            for col in columns:
                set_clauses.append(f'"{col}" = ?')
                values.append(request.form.get(col, ''))
            
            # Update the record
            set_clause = ', '.join(set_clauses)
            values.append(rowid)  # For the WHERE clause
            cursor.execute(f'UPDATE "{table_name}" SET {set_clause} WHERE rowid = ?', values)
            conn.commit()
            conn.close()
            
            return redirect(f'/db-admin/view-table/{db_name}/{table_name}')
        
        # Get the current record data
        cursor.execute(f'SELECT * FROM "{table_name}" WHERE rowid = ?', (rowid,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return f"Record with ID {rowid} not found", 404
        
        # Generate form for editing the record
        form_fields = ''
        for i, col_info in enumerate(columns_info):
            col_name = col_info[1]
            val = row[i] if row[i] is not None else ''
            val_str = str(val)
            form_fields += f"""
            <div class="form-group">
                <label for="{col_name}">{col_name}</label>
                <input type="text" id="{col_name}" name="{col_name}" value="{html.escape(val_str)}" class="form-control">
            </div>
            """
        
        conn.close()
        
        html_content = f"""
        <html>
        <head>
            <title>Edit Record - {table_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }}
                .back-link {{
                    margin-bottom: 20px;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                .form-control {{
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                    cursor: pointer;
                    border: none;
                }}
            </style>
        </head>
        <body>
            <div class="back-link">
                <a href="/db-admin/view-table/{db_name}/{table_name}">← Back to Table</a>
            </div>
            <h2>Edit Record in {table_name}</h2>
            <form method="post">
                {form_fields}
                <button type="submit" class="btn">Save Changes</button>
            </form>
        </body>
        </html>
        """
        return html_content
    except Exception as e:
        return f"Error editing record: {str(e)}", 500

@db_admin_bp.route('/delete-record/<db_name>/<table_name>/<int:rowid>', methods=['GET'])
def delete_record(db_name, table_name, rowid):
    """Delete a record from the table."""
    if db_name not in DATABASE_PATHS:
        return "Database not found", 404
    
    db_path = DATABASE_PATHS[db_name]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete the record
        cursor.execute(f'DELETE FROM "{table_name}" WHERE rowid = ?', (rowid,))
        conn.commit()
        conn.close()
        
        return redirect(f'/db-admin/view-table/{db_name}/{table_name}')
    except Exception as e:
        return f"Error deleting record: {str(e)}", 500

def register_db_admin_routes(app):
    """Register database admin routes."""
    # Setup Basic Authentication - Use environment variables for production
    app.config['BASIC_AUTH_USERNAME'] = os.environ.get('DB_ADMIN_USERNAME', 'admin')
    app.config['BASIC_AUTH_PASSWORD'] = os.environ.get('DB_ADMIN_PASSWORD', 'tcfadmin2024')
    app.config['BASIC_AUTH_FORCE'] = False  # Don't force it globally
    
    # Create basic auth instance
    basic_auth = BasicAuth(app)
    
    # Create a wrapper function to protect all routes in the blueprint
    @db_admin_bp.before_request
    def require_auth():
        if not basic_auth.authenticate():
            return basic_auth.challenge()
    
    # Register the blueprint
    app.register_blueprint(db_admin_bp, url_prefix='/db-admin')
    
    logger.info("Database admin routes registered") 