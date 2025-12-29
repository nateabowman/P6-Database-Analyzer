"""Repository for data access layer."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from storage.database import SessionLocal, get_db
from storage.models import AnalysisResult, ConnectionProfile
from utils.logging_config import get_logger

logger = get_logger(__name__)


class Repository:
    """Data access repository."""
    
    def get_analysis_history(
        self,
        analysis_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get analysis history.
        
        Args:
            analysis_type: Filter by analysis type
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results
        
        Returns:
            List of analysis results
        """
        db = SessionLocal()
        try:
            query = db.query(AnalysisResult)
            
            if analysis_type:
                query = query.filter(AnalysisResult.analysis_type == analysis_type)
            
            if start_date:
                query = query.filter(AnalysisResult.created_at >= start_date)
            
            if end_date:
                query = query.filter(AnalysisResult.created_at <= end_date)
            
            results = query.order_by(AnalysisResult.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': r.id,
                    'analysis_type': r.analysis_type,
                    'database_name': r.database_name,
                    'status': r.status,
                    'results': r.results,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                }
                for r in results
            ]
        finally:
            db.close()
    
    def save_analysis_result(
        self,
        analysis_type: str,
        database_name: str,
        database_type: str,
        status: str,
        results: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save analysis result.
        
        Args:
            analysis_type: Type of analysis
            database_name: Database name
            database_type: Database type
            status: Analysis status
            results: Analysis results
            metadata: Additional metadata
        
        Returns:
            Saved result ID
        """
        db = SessionLocal()
        try:
            result = AnalysisResult(
                analysis_type=analysis_type,
                database_name=database_name,
                database_type=database_type,
                status=status,
                results=results,
                metadata=metadata or {}
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            return result.id
        finally:
            db.close()


# Global repository instance
_repository: Optional[Repository] = None


def get_repository() -> Repository:
    """Get the global repository instance."""
    global _repository
    if _repository is None:
        _repository = Repository()
    return _repository

