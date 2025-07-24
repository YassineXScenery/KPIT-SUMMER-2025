import xml.etree.ElementTree as ET

class CANLINChecker:
    @staticmethod
    def get_expected_can_message(message_name):
        tree = ET.parse('hazard_test_robot/resources/can_messages.xml')
        for msg in tree.findall('message'):
            if msg.get('name') == message_name:
                return {
                    'id': int(msg.get('id'), 16),
                    'data': [int(byte.text) for byte in msg.findall('Byte/Value')]
                }
        raise ValueError(f"CAN message {message_name} not found")
    
    @staticmethod
    def get_expected_lin_message(message_name):
        tree = ET.parse('hazard_test_robot/resources/lin_messages.xml')
        for msg in tree.findall('message'):
            if msg.get('name') == message_name:
                return {
                    'id': int(msg.get('id'), 16),
                    'data': [int(byte.text) for byte in msg.findall('Byte/Value')]
                }
        raise ValueError(f"LIN message {message_name} not found")
    
    @staticmethod
    def receive_can_message(msg_id):
        # Mock implementation - replace with actual CAN bus reading
        return {'id': msg_id, 'data': [0x00, 0x01]}
    
    @staticmethod
    def receive_lin_message(msg_id):
        # Mock implementation - replace with actual LIN bus reading
        return {'id': msg_id, 'data': [0x00]}