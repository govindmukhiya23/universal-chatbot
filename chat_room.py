import time
import random
import logging

logger = logging.getLogger(__name__)

class ChatRoomManager:
    def __init__(self, translate_service):
        self.rooms = {}  # {room_pin: {users: {user_id: {name, language, joined_at}}, messages: [], created_at, last_activity}}
        self.user_rooms = {}  # {user_id: room_pin}
        self.translate_service = translate_service
        
    def generate_room_pin(self):
        """Generate a unique 6-digit room PIN"""
        while True:
            pin = str(random.randint(100000, 999999))
            if pin not in self.rooms:
                return pin
    
    def create_room(self, user_id, user_name, user_language):
        """Create a new chat room"""
        # Generate unique PIN
        room_pin = self.generate_room_pin()
        
        # Create room
        self.rooms[room_pin] = {
            'users': {
                user_id: {
                    'name': user_name,
                    'language': user_language,
                    'joined_at': time.time(),
                    'is_creator': True
                }
            },
            'messages': [],
            'created_at': time.time(),
            'last_activity': time.time()
        }
        
        # Map user to room
        self.user_rooms[user_id] = room_pin
        
        logger.info(f"Room {room_pin} created by {user_name}")
        return room_pin
    
    def join_room(self, room_pin, user_id, user_name, user_language):
        """Join an existing chat room"""
        if not room_pin or room_pin not in self.rooms:
            return False, "Room not found or expired"
        
        # Add user to room
        self.rooms[room_pin]['users'][user_id] = {
            'name': user_name,
            'language': user_language,
            'joined_at': time.time(),
            'is_creator': False
        }
        
        # Update room activity
        self.rooms[room_pin]['last_activity'] = time.time()
        
        # Map user to room
        self.user_rooms[user_id] = room_pin
        
        logger.info(f"User {user_name} joined room {room_pin}")
        return True, None
    
    def leave_room(self, user_id):
        """Leave current room"""
        if user_id not in self.user_rooms:
            return False, "Not in any room"
        
        room_pin = self.user_rooms[user_id]
        
        if room_pin in self.rooms and user_id in self.rooms[room_pin]['users']:
            # Remove user from room
            user_name = self.rooms[room_pin]['users'][user_id]['name']
            self.rooms[room_pin]['users'].pop(user_id)
            self.rooms[room_pin]['last_activity'] = time.time()
            
            # Remove user from mapping
            self.user_rooms.pop(user_id)
            
            # If room is empty, remove it
            if not self.rooms[room_pin]['users']:
                self.rooms.pop(room_pin)
                logger.info(f"Empty room {room_pin} removed")
            
            logger.info(f"User {user_name} left room {room_pin}")
            return True, None
            
        return False, "Room or user not found"
    
    def cleanup_expired_rooms(self):
        """Remove rooms that have been inactive for more than 1 hour"""
        current_time = time.time()
        expired_rooms = []
        
        for pin, room in self.rooms.items():
            if current_time - room['last_activity'] > 3600:  # 1 hour
                expired_rooms.append(pin)
        
        for pin in expired_rooms:
            # Remove users from user_rooms mapping
            for user_id in self.rooms[pin]['users']:
                self.user_rooms.pop(user_id, None)
            # Remove room
            self.rooms.pop(pin)
            logger.info(f"Expired room {pin} removed")
    
    def get_room_info(self, room_pin):
        """Get information about a room"""
        if room_pin not in self.rooms:
            return None
        
        room = self.rooms[room_pin]
        return {
            'room_pin': room_pin,
            'users': list(room['users'].values()),
            'message_count': len(room['messages']),
            'created_at': room['created_at'],
            'last_activity': room['last_activity']
        }
    
    def broadcast_message(self, socketio, user_id, message):
        """Broadcast a message to all users in a room with translations"""
        if user_id not in self.user_rooms:
            return False, "Not in any room"
        
        room_pin = self.user_rooms[user_id]
        
        if room_pin not in self.rooms:
            return False, "Room not found"
        
        room = self.rooms[room_pin]
        sender = room['users'][user_id]
        sender_language = sender['language']
        
        # Create message object with translations
        message_obj = {
            'sender_id': user_id,
            'sender_name': sender['name'],
            'original_text': message,
            'sender_language': sender_language,
            'timestamp': time.time(),
            'translations': {}
        }
        
        # Translate for each language in the room
        unique_languages = {user['language'] for user in room['users'].values()}
        
        for lang in unique_languages:
            if lang == sender_language:
                message_obj['translations'][lang] = message
            else:
                try:
                    translated = self.translate_service.translate_text(message, sender_language, lang)
                    message_obj['translations'][lang] = translated or message
                except Exception as e:
                    logger.error(f"Translation error ({sender_language}->{lang}): {e}")
                    message_obj['translations'][lang] = message
        
        # Add message to room history
        room['messages'].append(message_obj)
        room['last_activity'] = time.time()
        
        # Keep only last 100 messages
        if len(room['messages']) > 100:
            room['messages'] = room['messages'][-100:]
        
        # Broadcast to all users in the room
        socketio.emit('room_message', message_obj, room=room_pin)
        return True, None
