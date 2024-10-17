import os
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any, Optional

MAX_CONTEXT_SIZE = 20000

async def initialize_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                role TEXT,
                content TEXT,
                timestamp DATETIME
            )
        ''')
        await db.commit()

async def get_guild_history(guild_id: str) -> List[Dict[str, Any]]:
    db_path = f'memories/{guild_id}_histories.sqlite'
    if not os.path.exists(db_path):
        await initialize_db(db_path)
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('SELECT message_id, role, content, timestamp FROM messages ORDER BY timestamp') as cursor:
            return [{"message_id": row[0], "content": {"role": row[1], "parts": [row[2]]}, "timestamp": row[3]} for row in await cursor.fetchall()]

async def update_guild_history(guild_id: str, message: Dict[str, Any], message_id: str, timestamp: Optional[datetime] = None) -> None:
    db_path = f'memories/{guild_id}_histories.sqlite'
    if not os.path.exists(db_path):
        await initialize_db(db_path)
    async with aiosqlite.connect(db_path) as db:
        # Check if the message already exists
        async with db.execute('SELECT id, timestamp FROM messages WHERE message_id = ?', (message_id,)) as cursor:
            existing_message = await cursor.fetchone()
        
        if existing_message:
            # If the message exists, update its content but keep the original timestamp
            await db.execute('''
                UPDATE messages
                SET role = ?, content = ?
                WHERE message_id = ?
            ''', (message['role'], message['parts'][0], message_id))
        else:
            # If the message doesn't exist, insert it as a new entry
            if timestamp is None:
                timestamp = datetime.now()
            await db.execute('''
                INSERT INTO messages (message_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (message_id, message['role'], message['parts'][0], timestamp))
        
        await db.commit()

    # Check and maintain the context size limit
    await maintain_context_size_limit(guild_id)

async def edit_guild_history(guild_id: str, message: Dict[str, Any], message_id: str) -> None:
    await update_guild_history(guild_id, message, message_id)

async def remove_message_from_history(guild_id: str, message_id: str) -> None:
    db_path = f'memories/{guild_id}_histories.sqlite'
    if os.path.exists(db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute('DELETE FROM messages WHERE message_id = ?', (message_id,))
            await db.commit()

async def clear_guild_history(guild_id: str) -> None:

    db_path = f'memories/{guild_id}_histories.sqlite'
    if os.path.exists(db_path):
        async with aiosqlite.connect(db_path) as db:
            await db.execute('DELETE FROM messages')
            await db.commit()

async def maintain_context_size_limit(guild_id: str) -> None:
    db_path = f'memories/{guild_id}_histories.sqlite'
    async with aiosqlite.connect(db_path) as db:
        # Get the current number of rows
        async with db.execute('SELECT COUNT(*) FROM messages') as cursor:
            count = (await cursor.fetchone())[0]
        
        if count > MAX_CONTEXT_SIZE:
            # Calculate how many rows to delete
            rows_to_delete = count - MAX_CONTEXT_SIZE
            
            # Delete the oldest rows
            await db.execute('''
                DELETE FROM messages
                WHERE id IN (
                    SELECT id FROM messages
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
            ''', (rows_to_delete,))
            
            await db.commit()

async def sync_bot_user_messages(guild_id: str, channel_id: int, bot: Any) -> None:
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"Couldn't find channel with id {channel_id}")
        return

    db_path = f'memories/{guild_id}_histories.sqlite'
    if not os.path.exists(db_path):
        await initialize_db(db_path)

    async with aiosqlite.connect(db_path) as db:
        # Check if the database is empty (indicating a recent clear)
        async with db.execute('SELECT COUNT(*) FROM messages') as cursor:
            count = (await cursor.fetchone())[0]
        
        if count == 0:
            # If the database is empty, we don't want to repopulate it with old messages
            return

        # Get the timestamp of the most recent message in the database
        async with db.execute('SELECT MAX(timestamp) FROM messages') as cursor:
            last_timestamp = await cursor.fetchone()
        
        last_timestamp = last_timestamp[0] if last_timestamp[0] else "1970-01-01T00:00:00"
        last_timestamp = datetime.fromisoformat(last_timestamp)

        # Fetch messages from Discord that are newer than the most recent message in the database
        messages = [
            message async for message in channel.history(limit=100, after=last_timestamp)
            if message.author == bot.user or (message.mentions and bot.user in message.mentions)
        ]
        messages.reverse()  # Process in chronological order

        for message in messages:
            # Check if the message exists in the database
            async with db.execute('SELECT id FROM messages WHERE message_id = ?', (str(message.id),)) as cursor:
                existing_message = await cursor.fetchone()

            if existing_message:
                # Update existing message
                await db.execute('''
                    UPDATE messages
                    SET content = ?, timestamp = ?
                    WHERE message_id = ?
                ''', (message.content, message.created_at, str(message.id)))
            else:
                # Insert new message
                await db.execute('''
                    INSERT INTO messages (message_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (str(message.id), 'user' if not message.author.bot else 'assistant', message.content, message.created_at))

        await db.commit()

    # Maintain context size limit after syncing
    await maintain_context_size_limit(guild_id)

# Ensure the memories folder exists
if not os.path.exists('memories'):
    os.makedirs('memories')