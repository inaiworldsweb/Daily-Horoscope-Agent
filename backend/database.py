"""
Database module for saving chat data to MongoDB and JSON file
"""

import os
import json
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient, ASCENDING, DESCENDING
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("Warning: pymongo/motor not installed. Chat data will not be saved to database.")

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://web_db_user:nency2004@dailyhoroscope.buhj27w.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "daily_horoscope")

class DatabaseManager:
    """Manages MongoDB connections and chat data operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.chats_collection = None
        self.sessions_collection = None
        self.connected = False
        
        # JSON file storage path
        self.json_file_path = os.path.join(os.path.dirname(__file__), 'chat_history.json')
        self.json_lock = threading.Lock()
        
        if MONGODB_AVAILABLE:
            self._connect()
    
    def _save_to_json(self, chat_document: Dict[str, Any]):
        """Save chat data to local JSON file as backup"""
        try:
            # Make document JSON serializable
            json_doc = dict(chat_document)
            if 'timestamp' in json_doc and isinstance(json_doc['timestamp'], datetime):
                json_doc['timestamp'] = json_doc['timestamp'].isoformat()
            if '_id' in json_doc:
                json_doc['_id'] = str(json_doc['_id'])
            
            with self.json_lock:
                # Read existing data
                data = []
                if os.path.exists(self.json_file_path):
                    try:
                        with open(self.json_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        data = []
                
                # Append new message
                data.append(json_doc)
                
                # Write back
                with open(self.json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving to JSON file: {e}")
    
    def get_json_history(self, session_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat history from JSON file"""
        try:
            if not os.path.exists(self.json_file_path):
                return []
            
            with self.json_lock:
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Filter by session if provided
            if session_id:
                data = [d for d in data if d.get('session_id') == session_id]
            
            # Sort by timestamp (newest first) and limit
            data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return data[:limit]
        except Exception as e:
            print(f"⚠️ Error reading JSON file: {e}")
            return []
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[DB_NAME]
            self.chats_collection = self.db['chats']
            self.sessions_collection = self.db['sessions']
            self.connected = True
            print("✅ Connected to MongoDB successfully")
            
            # Create indexes for better query performance
            self._create_indexes()
        except Exception as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            print("Chat data will be stored in memory only.")
            self.connected = False
    
    def _create_indexes(self):
        """Create database indexes for efficient querying"""
        if not self.connected:
            return
        try:
            # Index for session-based queries
            self.chats_collection.create_index([("session_id", ASCENDING)])
            self.chats_collection.create_index([("timestamp", DESCENDING)])
            self.chats_collection.create_index([("session_id", ASCENDING), ("timestamp", DESCENDING)])
            
            # Index for sessions
            self.sessions_collection.create_index([("session_id", ASCENDING)], unique=True)
            self.sessions_collection.create_index([("last_active", DESCENDING)])
            print("✅ Database indexes created")
        except Exception as e:
            print(f"⚠️ Error creating indexes: {e}")
    
    def save_chat_message(self, session_id: str, user_message: str, bot_reply: str,
                          sign: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """
        Save a chat message exchange to MongoDB and JSON file

        Args:
            session_id: Unique session identifier
            user_message: The user's message
            bot_reply: The bot's response
            sign: Zodiac sign if detected
            metadata: Additional metadata about the chat

        Returns:
            bool: True if saved to either storage, False otherwise
        """
        chat_document = {
            "session_id": session_id,
            "user_message": user_message,
            "bot_reply": bot_reply,
            "sign": sign,
            "timestamp": datetime.utcnow(),
            "metadata": metadata or {}
        }

        # Always save to JSON file (works even without MongoDB)
        self._save_to_json(chat_document)

        mongo_saved = False
        if self.connected:
            try:
                result = self.chats_collection.insert_one(chat_document)
                mongo_saved = bool(result.inserted_id)
                # Update session info
                self._update_session(session_id, sign)
            except Exception as e:
                print(f"⚠️ Error saving chat message to MongoDB: {e}")

        return True  # JSON always saves, MongoDB is bonus
    
    def _update_session(self, session_id: str, sign: Optional[str] = None):
        """Update or create session record"""
        if not self.connected:
            return
        
        try:
            update_data = {
                "$set": {
                    "last_active": datetime.utcnow()
                },
                "$setOnInsert": {
                    "session_id": session_id,
                    "created_at": datetime.utcnow()
                }
            }
            
            if sign:
                update_data["$set"]["sign"] = sign
            
            self.sessions_collection.update_one(
                {"session_id": session_id},
                update_data,
                upsert=True
            )
        except Exception as e:
            print(f"⚠️ Error updating session: {e}")
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a specific session
        
        Args:
            session_id: The session ID to query
            limit: Maximum number of messages to return
        
        Returns:
            List of chat documents
        """
        if not self.connected:
            return []
        
        try:
            cursor = self.chats_collection.find(
                {"session_id": session_id}
            ).sort("timestamp", DESCENDING).limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"⚠️ Error retrieving chat history: {e}")
            return []
    
    def get_all_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active sessions
        
        Args:
            limit: Maximum number of sessions to return
        
        Returns:
            List of session documents
        """
        if not self.connected:
            return []
        
        try:
            cursor = self.sessions_collection.find().sort("last_active", DESCENDING).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"⚠️ Error retrieving sessions: {e}")
            return []
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        if not self.connected:
            return {}
        
        try:
            message_count = self.chats_collection.count_documents({"session_id": session_id})
            session = self.sessions_collection.find_one({"session_id": session_id})
            
            return {
                "session_id": session_id,
                "message_count": message_count,
                "session_info": session
            }
        except Exception as e:
            print(f"⚠️ Error getting session stats: {e}")
            return {}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        if not self.connected:
            return {"status": "disconnected"}
        
        try:
            total_chats = self.chats_collection.count_documents({})
            total_sessions = self.sessions_collection.count_documents({})
            
            # Get today's chats
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_chats = self.chats_collection.count_documents({
                "timestamp": {"$gte": today_start}
            })
            
            return {
                "status": "connected",
                "total_chats": total_chats,
                "total_sessions": total_sessions,
                "today_chats": today_chats,
                "database_name": DB_NAME
            }
        except Exception as e:
            print(f"⚠️ Error getting database stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            print("✅ MongoDB connection closed")


# Global database instance
db_manager = DatabaseManager()
