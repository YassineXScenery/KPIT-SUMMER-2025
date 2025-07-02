import mysql.connector
from mysql.connector import Error

# Database Configuration
DB_CONFIG = {
    'host': '10.20.0.2',
    'port': 3306,
    'user': 'user',
    'password': '1234',
    'database': 'iot_system'
}

def get_connection():
    """Create and return a new database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def get_last_update_time():
    """Get the most recent timestamp from the database"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(timestamp) 
            FROM signals_log 
            WHERE signal_name IN ('led', 'button')
        """)
        return cursor.fetchone()[0]
    except Exception as e:
        print("Error getting last update time:", e)
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_current_states():
    """Get current states in a single optimized query"""
    conn = get_connection()
    if not conn:
        return None, None, None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                MAX(CASE WHEN signal_name = 'led' THEN value END) as led_state,
                MAX(CASE WHEN signal_name = 'button' THEN value END) as button_state,
                MAX(timestamp) as last_change
            FROM (
                SELECT signal_name, value, timestamp
                FROM signals_log
                WHERE signal_name IN ('led', 'button')
                ORDER BY timestamp DESC
                LIMIT 2
            ) as latest_states
        """)
        row = cursor.fetchone()
        return row[0] or 'off', row[1] or 'not pressed', row[2]
    except Exception as e:
        print("Error getting states:", e)
        return None, None, None
    finally:
        if conn and conn.is_connected():
            conn.close()

def update_states(led_state, button_state):
    """Update states in the database"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signals_log (signal_name, value, source)
            VALUES (%s, %s, 'GUI'), (%s, %s, 'GUI')
            ON DUPLICATE KEY UPDATE 
                value = VALUES(value),
                timestamp = CURRENT_TIMESTAMP
        """, ('led', led_state, 'button', button_state))
        conn.commit()
        return True
    except Exception as e:
        print("Error updating states:", e)
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()