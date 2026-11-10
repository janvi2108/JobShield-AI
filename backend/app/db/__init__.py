"""JobShield AI — Database Package.

Exposes models, session factory, schema initializers, and high-level CRUD.
"""
from .database import (
    init_db,
    save_analysis,
    get_recent_analyses,
    get_analysis_by_id,
    get_analyses_list,
    delete_analysis,
    get_analysis_stats,
    save_extraction,
    get_recent_extractions,
    get_session,
    _get_db_path,
    get_connection,
)
from .models import (
    Base,
    JobAnalysis,
    FraudPrediction,
    ExtractedDetails,
    EvidenceFinding,
    AIExplanation,
)

__all__ = [
    "init_db",
    "save_analysis",
    "get_recent_analyses",
    "get_analysis_by_id",
    "get_analyses_list",
    "delete_analysis",
    "get_analysis_stats",
    "save_extraction",
    "get_recent_extractions",
    "get_session",
    "_get_db_path",
    "get_connection",
    "Base",
    "JobAnalysis",
    "FraudPrediction",
    "ExtractedDetails",
    "EvidenceFinding",
    "AIExplanation",
]
