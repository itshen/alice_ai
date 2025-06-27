"""
SQLite数据库管理
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .config import config

class Database:
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.get('database.path', 'chat_history.db')
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    model_provider TEXT,
                    model_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def create_session(self, title: str, model_provider: str = None, model_name: str = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO sessions (id, title, model_provider, model_name)
                VALUES (?, ?, ?, ?)
            ''', (session_id, title, model_provider, model_name))
            conn.commit()
        return session_id
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT s.*, COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取单个会话"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_session(self, session_id: str, **kwargs):
        """更新会话"""
        if not kwargs:
            return
        
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now().isoformat(), session_id]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f'''
                UPDATE sessions 
                SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values)
            conn.commit()
    
    def delete_session(self, session_id: str):
        """删除会话"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            conn.commit()
    
    def add_message(self, session_id: str, role: str, content: str, tool_calls: List[Dict] = None):
        """添加消息"""
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO messages (session_id, role, content, tool_calls)
                VALUES (?, ?, ?, ?)
            ''', (session_id, role, content, tool_calls_json))
            
            # 更新会话的最后更新时间
            conn.execute('''
                UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY created_at ASC
            ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                message = dict(row)
                if message['tool_calls']:
                    message['tool_calls'] = json.loads(message['tool_calls'])
                messages.append(message)
            
            return messages
    
    def clear_messages(self, session_id: str):
        """清空会话消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            conn.commit()

# 全局数据库实例
db = Database() 