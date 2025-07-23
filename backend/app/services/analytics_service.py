from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from app.models.database import get_db, UserInteractionDB, JobMetadataDB
from app.models.schemas import UserInteraction

class AnalyticsService:
    def __init__(self):
        pass

    def track_user_interaction(self, db: Session, user_id: str, job_id: str, 
                             action: str, metadata: Optional[Dict[str, Any]] = None):
        """Track user interaction"""
        try:
            interaction = UserInteractionDB(
                user_id=user_id,
                job_id=job_id,
                action=action,
                interaction_metadata=json.dumps(metadata) if metadata else None,
                timestamp=datetime.utcnow()
            )
            db.add(interaction)
            db.commit()
            return True
        except Exception as e:
            print(f"Error tracking user interaction: {e}")
            db.rollback()
            return False

    def get_user_interactions(self, db: Session, user_id: str, 
                            limit: int = 50) -> List[UserInteraction]:
        """Get user interactions"""
        try:
            interactions = db.query(UserInteractionDB).filter(
                UserInteractionDB.user_id == user_id
            ).order_by(UserInteractionDB.timestamp.desc()).limit(limit).all()
            
            result = []
            for interaction in interactions:
                metadata = None
                if interaction.interaction_metadata:
                    try:
                        metadata = json.loads(interaction.interaction_metadata)
                    except:
                        pass
                
                result.append(UserInteraction(
                    id=str(interaction.id),
                    user_id=interaction.user_id,
                    job_id=interaction.job_id,
                    action=interaction.action,
                    metadata=metadata,
                    timestamp=interaction.timestamp
                ))
            
            return result
        except Exception as e:
            print(f"Error getting user interactions: {e}")
            return []

    def get_popular_jobs(self, db: Session, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular jobs based on interactions"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            popular_jobs = db.query(
                UserInteractionDB.job_id,
                db.func.count(UserInteractionDB.id).label('interaction_count')
            ).filter(
                UserInteractionDB.timestamp >= since_date,
                UserInteractionDB.action.in_(['view', 'click'])
            ).group_by(
                UserInteractionDB.job_id
            ).order_by(
                db.func.count(UserInteractionDB.id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'job_id': job.job_id,
                    'interaction_count': job.interaction_count
                }
                for job in popular_jobs
            ]
        except Exception as e:
            print(f"Error getting popular jobs: {e}")
            return []

    def get_search_analytics(self, db: Session, days: int = 7) -> Dict[str, Any]:
        """Get search analytics"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Total searches
            total_searches = db.query(UserInteractionDB).filter(
                UserInteractionDB.action == 'search',
                UserInteractionDB.timestamp >= since_date
            ).count()
            
            # Unique users
            unique_users = db.query(UserInteractionDB.user_id).filter(
                UserInteractionDB.timestamp >= since_date
            ).distinct().count()
            
            # Most active users
            active_users = db.query(
                UserInteractionDB.user_id,
                db.func.count(UserInteractionDB.id).label('activity_count')
            ).filter(
                UserInteractionDB.timestamp >= since_date
            ).group_by(
                UserInteractionDB.user_id
            ).order_by(
                db.func.count(UserInteractionDB.id).desc()
            ).limit(10).all()
            
            return {
                'total_searches': total_searches,
                'unique_users': unique_users,
                'active_users': [
                    {
                        'user_id': user.user_id,
                        'activity_count': user.activity_count
                    }
                    for user in active_users
                ]
            }
        except Exception as e:
            print(f"Error getting search analytics: {e}")
            return {}
