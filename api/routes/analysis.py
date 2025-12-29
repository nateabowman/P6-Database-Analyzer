"""Analysis API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from api.auth import get_current_user, require_permission
from utils.rbac import Permission
from utils.logging_config import get_logger
from database.db_factory import DatabaseFactory
from analyzers.schema_health import SchemaHealthScanner
from analyzers.index_fragmentation import IndexFragmentationChecker
from analyzers.table_analyzer import TableAnalyzer
from analyzers.corruption_detector import CorruptionDetector

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/schema")
async def run_schema_analysis(
    connection_config: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.RUN_ANALYSIS.value))
):
    """Run schema health analysis."""
    try:
        # Create connector
        db_type = connection_config.get("db_type")
        connector = DatabaseFactory.create_connector(db_type, **connection_config)
        connector.connect()
        
        # Run analysis
        scanner = SchemaHealthScanner(connector)
        results = scanner.scan_schema_health()
        
        connector.disconnect()
        
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Schema analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/index-fragmentation")
async def run_index_analysis(
    connection_config: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.RUN_ANALYSIS.value))
):
    """Run index fragmentation analysis."""
    try:
        db_type = connection_config.get("db_type")
        connector = DatabaseFactory.create_connector(db_type, **connection_config)
        connector.connect()
        
        checker = IndexFragmentationChecker(connector)
        results = checker.check_fragmentation()
        
        connector.disconnect()
        
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Index analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/tables")
async def run_table_analysis(
    connection_config: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.RUN_ANALYSIS.value))
):
    """Run table analysis."""
    try:
        db_type = connection_config.get("db_type")
        connector = DatabaseFactory.create_connector(db_type, **connection_config)
        connector.connect()
        
        analyzer = TableAnalyzer(connector)
        results = analyzer.analyze_tables()
        
        connector.disconnect()
        
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Table analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/corruption")
async def run_corruption_analysis(
    connection_config: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.RUN_ANALYSIS.value))
):
    """Run corruption detection analysis."""
    try:
        db_type = connection_config.get("db_type")
        connector = DatabaseFactory.create_connector(db_type, **connection_config)
        connector.connect()
        
        detector = CorruptionDetector(connector)
        results = detector.detect_issues()
        
        connector.disconnect()
        
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Corruption analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/full")
async def run_full_analysis(
    connection_config: Dict[str, Any],
    current_user: dict = Depends(require_permission(Permission.RUN_ANALYSIS.value))
):
    """Run full analysis suite."""
    try:
        db_type = connection_config.get("db_type")
        connector = DatabaseFactory.create_connector(db_type, **connection_config)
        connector.connect()
        
        results = {}
        
        # Run all analyses
        scanner = SchemaHealthScanner(connector)
        results['schema_health'] = scanner.scan_schema_health()
        
        checker = IndexFragmentationChecker(connector)
        results['index_fragmentation'] = checker.check_fragmentation()
        
        analyzer = TableAnalyzer(connector)
        results['table_analysis'] = analyzer.analyze_tables()
        
        detector = CorruptionDetector(connector)
        results['corruption'] = detector.detect_issues()
        
        connector.disconnect()
        
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Full analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

