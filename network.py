import socket
import mysql.connector
from PyQt5.QtCore import QThread, pyqtSignal

class DatabaseWatcher(QThread):
    update_received = pyqtSignal(str, str)  # signal_name, value
    
    def __init__(self, db_config):
        super().__init__()
        self.db_config = db_config
        self.running = True

    def run(self):
        while self.running:
            try:
                conn = mysql.connector.connect(**self.db_config)
                cursor = conn.cursor(dictionary=True)
                
                # Check for unprocessed changes
                cursor.execute("""
                    SELECT signal_name, new_value 
                    FROM signal_changes 
                    WHERE processed = FALSE
                    ORDER BY change_time DESC
                    LIMIT 2
                """)
                
                for row in cursor.fetchall():
                    self.update_received.emit(row['signal_name'], row['new_value'])
                    # Mark as processed
                    cursor.execute("""
                        UPDATE signal_changes 
                        SET processed = TRUE 
                        WHERE signal_name = %s AND new_value = %s
                    """, (row['signal_name'], row['new_value']))
                    conn.commit()
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Database watch error: {e}")
            finally:
                self.msleep(100)  # 100ms delay between checks

    def stop(self):
        self.running = False

def send_udp_message(signal_name, value):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(f"{signal_name}:{value}".encode(), ('10.20.0.33', 40000))
        sock.close()
    except Exception as e:
        print(f"UDP error: {e}")