import mysql.connector
from mysql.connector import Error, pooling
from datetime import datetime
import time

# Database Configuration
DB_CONFIG = {
    'host': '10.10.0.47',
    'port': 3306,
    'user': 'user',
    'password': '1234',
    'auth_plugin': 'mysql_native_password',
    'database': 'kpit_summer_2025',
    'pool_name': 'iot_pool',
    'pool_size': 10
}

# Create connection pool with retries
connection_pool = None
max_retries = 3
retry_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        connection_pool = pooling.MySQLConnectionPool(**DB_CONFIG)
        print("✅ Connection pool created successfully!")
        break
    except Error as e:
        print(f"❌ Attempt {attempt+1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
else:
    print("❌ Failed to create connection pool after multiple attempts")

def get_connection():
    """Get a connection from the pool"""
    if not connection_pool:
        return None
    
    try:
        conn = connection_pool.get_connection()
        conn.autocommit = False
        
        # Test the connection is actually working
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchall()
        cursor.close()
        
        return conn
    except Error as e:
        print(f"Error getting connection from pool: {e}")
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
            WHERE signal_name IN ('led', 'button', 'ledL', 'buttonL')
        """)
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None
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
                MAX(CASE WHEN signal_name = 'ledL' THEN value END) as ledL_state,
                MAX(CASE WHEN signal_name = 'buttonL' THEN value END) as buttonL_state,
                MAX(timestamp) as last_change
            FROM (
                SELECT signal_name, value, timestamp
                FROM signals_log
                WHERE signal_name IN ('led', 'button', 'ledL', 'buttonL')
                ORDER BY timestamp DESC
                LIMIT 4
            ) as latest_states
        """)
        row = cursor.fetchone()
        cursor.close()
        return (
            row[0] or 'off',  # CAN led
            row[1] or 'not pressed',  # CAN button
            row[2] or 'off',  # LIN led
            row[3] or 'not pressed',  # LIN button
            row[4]  # timestamp
        )
    except Exception as e:
        print("Error getting states:", e)
        return None, None, None, None, None
    finally:
        if conn and conn.is_connected():
            conn.close()

def update_states(led_state, button_state, protocol='CAN'):
    """Update states in the database"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        if protocol == 'CAN':
            cursor.execute("""
            INSERT INTO signals_log (signal_name, value, source, protocol)
            VALUES (%s, %s, 'GUI', 'CAN'), (%s, %s, 'GUI', 'CAN')
            """, ('led', led_state, 'button', button_state))
        else:  # LIN
            cursor.execute("""
            INSERT INTO signals_log (signal_name, value, source, protocol)
            VALUES (%s, %s, 'GUI', 'LIN'), (%s, %s, 'GUI', 'LIN')
            """, ('ledL', led_state, 'buttonL', button_state))
        
        conn.commit()
        return True
    except Exception as e:
        print("Error updating states:", e)
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    print("\n=== Testing Database Module ===")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Check connection
    print("\n[1] Testing database connection...")
    conn = get_connection()
    if conn:
        print("✅ Connection successful!")
        conn.close()
    else:
        print("❌ Connection failed!")
    
    # Test 2: Get last update time
    print("\n[2] Testing get_last_update_time()...")
    last_update = get_last_update_time()
    print(f"Last update time: {last_update}")
    
    # Test 3: Get current states
    print("\n[3] Testing get_current_states()...")
    can_led, can_button, lin_led, lin_button, timestamp = get_current_states()
    print(f"CAN LED: {can_led}, CAN Button: {can_button}")
    print(f"LIN LED: {lin_led}, LIN Button: {lin_button}")
    print(f"Last Change: {timestamp}")
    
    # Test 4: Update states (toggle)
    print("\n[4] Testing update_states()...")
    new_can_led = 'on' if can_led == 'off' else 'off'
    new_can_button = 'pressed' if can_button == 'not pressed' else 'not pressed'
    success = update_states(new_can_led, new_can_button, 'CAN')
    print(f"CAN Update {'successful' if success else 'failed'}. New states: LED={new_can_led}, Button={new_can_button}")
    
    new_lin_led = 'on' if lin_led == 'off' else 'off'
    new_lin_button = 'pressed' if lin_button == 'not pressed' else 'not pressed'
    success = update_states(new_lin_led, new_lin_button, 'LIN')
    print(f"LIN Update {'successful' if success else 'failed'}. New states: LED={new_lin_led}, Button={new_lin_button}")
    
    # Verify update
    print("\n[5] Verifying update...")
    can_led, can_button, lin_led, lin_button, timestamp = get_current_states()
    print(f"Updated CAN states - LED: {can_led}, Button: {can_button}")
    print(f"Updated LIN states - LED: {lin_led}, Button: {lin_button}")
    print(f"Timestamp: {timestamp}")
    
    print("\n=== Tests complete ===")