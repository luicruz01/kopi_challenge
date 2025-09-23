"""Storage implementations for conversation history."""
import json
import time
from abc import ABC, abstractmethod

from .models import Turn


class ConversationStore(ABC):
    """Abstract base class for conversation storage."""

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> list[Turn] | None:
        """Get conversation history by ID."""
        pass

    @abstractmethod
    async def save_conversation(self, conversation_id: str, turns: list[Turn]) -> None:
        """Save conversation history with 24h TTL."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if storage is healthy."""
        pass


class InMemoryStore(ConversationStore):
    """In-memory storage implementation with TTL."""

    def __init__(self):
        self._conversations = {}  # {conversation_id: {"turns": [...], "expires_at": timestamp, "next_seq": int}}

    def _cleanup_expired(self):
        """Remove expired conversations."""
        now = time.time()
        expired_keys = [
            key for key, data in self._conversations.items() if data["expires_at"] < now
        ]
        for key in expired_keys:
            del self._conversations[key]

    def _trim_turns(self, turns: list[Turn]) -> list[Turn]:
        """Keep only the last 5 turns per role (max 10 total), ordered chronologically."""
        if len(turns) <= 10:
            return turns

        # Ensure all turns have sequence numbers (fallback safety)
        turns_with_seq = []
        for i, turn in enumerate(turns):
            if turn.sequence is None:
                turn.sequence = i + 1
            turns_with_seq.append(turn)

        # Group by role and keep last 5 of each based on sequence
        user_turns = sorted(
            [t for t in turns_with_seq if t.role == "user"], key=lambda x: x.sequence
        )[-5:]
        bot_turns = sorted(
            [t for t in turns_with_seq if t.role == "bot"], key=lambda x: x.sequence
        )[-5:]

        # Merge and sort by sequence for chronological order
        all_turns = user_turns + bot_turns
        all_turns.sort(key=lambda t: t.sequence)

        return all_turns

    async def get_conversation(self, conversation_id: str) -> list[Turn] | None:
        """Get conversation history by ID."""
        self._cleanup_expired()

        if conversation_id not in self._conversations:
            return None

        data = self._conversations[conversation_id]
        if data["expires_at"] < time.time():
            del self._conversations[conversation_id]
            return None

        return data["turns"]

    async def save_conversation(self, conversation_id: str, turns: list[Turn]) -> None:
        """Save conversation history with 24h TTL."""
        self._cleanup_expired()

        # Assign sequence numbers to turns that don't have them
        if conversation_id in self._conversations:
            next_seq = self._conversations[conversation_id].get("next_seq", 1)
        else:
            next_seq = 1

        for turn in turns:
            if turn.sequence is None:
                turn.sequence = next_seq
                next_seq += 1

        trimmed_turns = self._trim_turns(turns)
        expires_at = time.time() + (24 * 60 * 60)  # 24 hours

        self._conversations[conversation_id] = {
            "turns": trimmed_turns,
            "expires_at": expires_at,
            "next_seq": next_seq,
        }

    async def health_check(self) -> bool:
        """Check if storage is healthy."""
        return True


class RedisStore(ConversationStore):
    """Redis storage implementation with TTL."""

    def __init__(self, redis_url: str):
        import redis.asyncio as redis

        self.redis = redis.from_url(redis_url)

    def _trim_turns(self, turns: list[Turn]) -> list[Turn]:
        """Keep only the last 5 turns per role (max 10 total), ordered chronologically."""
        if len(turns) <= 10:
            return turns

        # Ensure all turns have sequence numbers (fallback safety)
        turns_with_seq = []
        for i, turn in enumerate(turns):
            if turn.sequence is None:
                turn.sequence = i + 1
            turns_with_seq.append(turn)

        # Group by role and keep last 5 of each based on sequence
        user_turns = sorted(
            [t for t in turns_with_seq if t.role == "user"], key=lambda x: x.sequence
        )[-5:]
        bot_turns = sorted(
            [t for t in turns_with_seq if t.role == "bot"], key=lambda x: x.sequence
        )[-5:]

        # Merge and sort by sequence for chronological order
        all_turns = user_turns + bot_turns
        all_turns.sort(key=lambda t: t.sequence)

        return all_turns

    async def get_conversation(self, conversation_id: str) -> list[Turn] | None:
        """Get conversation history by ID."""
        key = f"conv:{conversation_id}"
        data = await self.redis.get(key)

        if not data:
            return None

        try:
            conv_data = json.loads(data)
            turns_data = conv_data.get("turns", [])
            return [Turn(**turn) for turn in turns_data]
        except (json.JSONDecodeError, TypeError):
            # Invalid data, remove it
            await self.redis.delete(key)
            return None

    async def save_conversation(self, conversation_id: str, turns: list[Turn]) -> None:
        """Save conversation history with 24h TTL."""
        key = f"conv:{conversation_id}"

        # Get current sequence number
        existing_data = await self.redis.get(key)
        next_seq = 1
        if existing_data:
            try:
                conv_data = json.loads(existing_data)
                next_seq = conv_data.get("next_seq", 1)
            except (json.JSONDecodeError, TypeError):
                next_seq = 1

        # Assign sequence numbers to turns that don't have them
        for turn in turns:
            if turn.sequence is None:
                turn.sequence = next_seq
                next_seq += 1

        trimmed_turns = self._trim_turns(turns)

        # Store both turns and next sequence number
        conv_data = {"turns": [turn.model_dump() for turn in trimmed_turns], "next_seq": next_seq}
        data = json.dumps(conv_data)

        # Save with 24h TTL
        await self.redis.setex(key, 24 * 60 * 60, data)

    async def health_check(self) -> bool:
        """Check if storage is healthy."""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


def create_store(redis_url: str | None = None) -> ConversationStore:
    """Factory function to create appropriate storage implementation."""
    if redis_url:
        return RedisStore(redis_url)
    else:
        return InMemoryStore()
