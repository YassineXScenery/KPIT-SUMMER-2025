import socket
import threading
import json
import time
from PyQt5.QtCore import QObject, pyqtSignal

class SocketManager(QObject):
    update_received = pyqtSignal(dict)
    peer_discovered = pyqtSignal(str)
    
    def __init__(self, host='0.0.0.0', port=65432, broadcast_port=65433):
        super().__init__()
        self.host = host
        self.port = port
        self.broadcast_port = broadcast_port
        self.running = False
        self.peers = set()
        self.socket = None
        self.broadcast_socket = None
        self.receive_thread = None
        self.discovery_thread = None
        
    def start(self):
        """Start both the main socket and discovery service"""
        if self.running:
            return True
            
        try:
            # Main UDP socket for communication
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            
            # Broadcast socket for peer discovery
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_socket.settimeout(0.2)
            
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            self.discovery_thread.start()
            return True
        except Exception as e:
            print(f"Failed to start socket manager: {e}")
            self.stop()
            return False

    def _receive_loop(self):
        """Thread function to receive messages"""
        while self.running:
            try:
                if not self.socket:
                    time.sleep(0.1)
                    continue
                    
                data, addr = self.socket.recvfrom(1024)
                try:
                    message = json.loads(data.decode())
                    
                    if message.get('type') == 'discovery':
                        # Respond to discovery requests
                        if addr[0] != self._get_local_ip():
                            response = {'type': 'discovery_response', 'host': self._get_local_ip()}
                            self.socket.sendto(json.dumps(response).encode(), addr)
                    else:
                        # Normal message handling
                        self.update_received.emit(message)
                except json.JSONDecodeError:
                    continue
                    
            except ConnectionResetError:
                time.sleep(0.1)
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Socket receive error: {e}")
                time.sleep(1)
                
    def _discovery_loop(self):
        """Thread function for automatic peer discovery"""
        while self.running:
            try:
                if not self.broadcast_socket:
                    time.sleep(5)
                    continue
                    
                # Broadcast discovery request
                message = {'type': 'discovery'}
                self.broadcast_socket.sendto(
                    json.dumps(message).encode(),
                    ('<broadcast>', self.broadcast_port)
                )
                
                # Listen for responses
                start_time = time.time()
                while time.time() - start_time < 1:  # Listen for 1 second
                    try:
                        data, addr = self.broadcast_socket.recvfrom(1024)
                        message = json.loads(data.decode())
                        if message.get('type') == 'discovery_response':
                            peer_ip = message['host']
                            if peer_ip not in self.peers and peer_ip != self._get_local_ip():
                                self.peers.add(peer_ip)
                                self.peer_discovered.emit(peer_ip)
                    except socket.timeout:
                        continue
                        
                time.sleep(5)  # Check for peers every 5 seconds
                
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"Discovery error: {e}")
                time.sleep(5)
                
    def _get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'
            
    def send_update(self, message):
        """Send an update to all known peers"""
        if not self.running:
            if not self.start():
                return False
                
        for peer in list(self.peers):  # Create a copy to avoid modification during iteration
            try:
                if not self.socket:
                    continue
                self.socket.sendto(json.dumps(message).encode(), (peer, self.port))
            except Exception as e:
                print(f"Error sending to {peer}: {e}")
                self.peers.discard(peer)  # Remove bad peers
        return True
                
    def stop(self):
        """Clean up resources"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        if self.broadcast_socket:
            try:
                self.broadcast_socket.close()
            except:
                pass
            self.broadcast_socket = None
            
        if self.receive_thread:
            self.receive_thread.join(timeout=1)
        if self.discovery_thread:
            self.discovery_thread.join(timeout=1)