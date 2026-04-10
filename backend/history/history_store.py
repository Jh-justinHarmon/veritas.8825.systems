"""
History storage for Veritas synthesis sessions.

Stores synthesis requests/responses with trace data for later retrieval.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class HistoryStore:
    """Manages synthesis history storage and retrieval."""
    
    def __init__(self, history_file: Path = None):
        """
        Initialize history store.
        
        Args:
            history_file: Path to history JSON file (default: history/synthesis_history.json)
        """
        if history_file is None:
            history_file = Path(__file__).parent.parent.parent / "history" / "synthesis_history.json"
        
        self.history_file = history_file
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize file if it doesn't exist
        if not self.history_file.exists():
            self._save_history([])
    
    def _load_history(self) -> List[Dict]:
        """Load history from file."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_history(self, history: List[Dict]):
        """Save history to file."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def save_synthesis(
        self,
        question: str,
        answer: Dict,
        trace: Dict
    ) -> str:
        """
        Save a synthesis session to history.
        
        Args:
            question: User's question
            answer: Synthesis answer (ideas + sources)
            trace: Trace data (retrieved chunks, scores, metadata)
            
        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        
        # Create history entry
        entry = {
            "id": session_id,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "trace": trace
        }
        
        # Load existing history
        history = self._load_history()
        
        # Add new entry at the beginning (most recent first)
        history.insert(0, entry)
        
        # Limit to 100 most recent entries
        history = history[:100]
        
        # Save updated history
        self._save_history(history)
        
        return session_id
    
    def get_all_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get all history entries (paginated).
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            List of history entries (preview format)
        """
        history = self._load_history()
        
        # Paginate
        paginated = history[offset:offset + limit]
        
        # Return preview format (exclude full answer/trace)
        return [
            {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "question": entry["question"],
                "preview": entry["answer"]["ideas"][0]["title"] if entry["answer"].get("ideas") else "",
                "idea_count": len(entry["answer"].get("ideas", [])),
                "source_count": len(entry["answer"].get("sources", {}))
            }
            for entry in paginated
        ]
    
    def get_history_by_id(self, session_id: str) -> Optional[Dict]:
        """
        Get a specific history entry by ID.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Full history entry or None if not found
        """
        history = self._load_history()
        
        for entry in history:
            if entry["id"] == session_id:
                return entry
        
        return None
    
    def delete_history(self, session_id: str) -> bool:
        """
        Delete a history entry.
        
        Args:
            session_id: Session UUID
            
        Returns:
            True if deleted, False if not found
        """
        history = self._load_history()
        
        # Filter out the entry
        updated_history = [e for e in history if e["id"] != session_id]
        
        # Check if anything was removed
        if len(updated_history) < len(history):
            self._save_history(updated_history)
            return True
        
        return False
    
    def clear_all_history(self):
        """Clear all history entries."""
        self._save_history([])
