"""
Evidence Services
Helper functions for evidence management
"""

from django.db import transaction
from django.utils import timezone
from typing import Dict, Any, Optional, List
import logging

from evidence.models import CompetencyEvidence, CompetencyAssessment, EvidenceTransaction

logger = logging.getLogger(__name__)


class EvidenceService:
    """
    Service for managing evidence operations.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def create_evidence_from_attempt(self, attempt, user, performance_score: float) -> CompetencyEvidence:
        """
        Create evidence from a learning attempt.
        
        Args:
            attempt: The learning attempt object
            user: The user who made the attempt
            performance_score: Score achieved
        
        Returns:
            CompetencyEvidence instance
        """
        evidence_data = {
            'activity_type': 'quiz' if hasattr(attempt, 'quiz') else 'practical',
            'activity_id': str(attempt.id),
            'activity_name': getattr(attempt, 'name', 'Learning Attempt'),
            'performance_score': performance_score,
            'difficulty_level': getattr(attempt, 'difficulty_level', 3),
            'completed_at': getattr(attempt, 'completed_at', timezone.now()),
            'concepts': getattr(attempt, 'concepts', []),
            'domain': getattr(attempt, 'domain', 'general'),
        }
        
        engine = CompetencyEngine(user)
        return engine.process_evidence(evidence_data)
    
    def create_evidence_from_simulation(self, simulation_data: Dict, user) -> CompetencyEvidence:
        """
        Create evidence from simulation debrief.
        
        Args:
            simulation_data: Dict with simulation results
            user: The user who completed the simulation
        
        Returns:
            CompetencyEvidence instance
        """
        evidence_data = {
            'activity_type': 'simulation',
            'activity_id': simulation_data.get('simulation_id'),
            'activity_name': simulation_data.get('simulation_name', 'Simulation'),
            'performance_score': simulation_data.get('performance_score', 0),
            'difficulty_level': simulation_data.get('difficulty_level', 3),
            'time_spent': simulation_data.get('time_spent'),
            'completed_at': simulation_data.get('completed_at', timezone.now()),
            'concepts': simulation_data.get('concepts_tested', []),
            'domain': simulation_data.get('domain', 'general'),
            'evidence_data': {
                'decision_points': simulation_data.get('decisions', []),
                'path_taken': simulation_data.get('path', []),
                'outcomes': simulation_data.get('outcomes', {}),
            },
            'tags': ['simulation', 'practical', 'decision-making'],
        }
        
        engine = CompetencyEngine(user)
        return engine.process_evidence(evidence_data)
    
    def create_evidence_from_project(self, project_data: Dict, user) -> CompetencyEvidence:
        """
        Create evidence from project submission.
        
        Args:
            project_data: Dict with project details
            user: The user who submitted the project
        
        Returns:
            CompetencyEvidence instance
        """
        evidence_data = {
            'activity_type': 'project',
            'activity_id': project_data.get('project_id'),
            'activity_name': project_data.get('project_name', 'Project'),
            'performance_score': project_data.get('score', 0),
            'difficulty_level': project_data.get('difficulty_level', 4),
            'completed_at': project_data.get('submitted_at', timezone.now()),
            'concepts': project_data.get('concepts_covered', []),
            'domain': project_data.get('domain', 'general'),
            'evidence_data': {
                'project_type': project_data.get('project_type'),
                'submission_url': project_data.get('submission_url'),
                'feedback': project_data.get('feedback', ''),
                'peer_reviews': project_data.get('peer_reviews', []),
            },
            'tags': ['project', 'practical', 'portfolio'],
        }
        
        engine = CompetencyEngine(user)
        return engine.process_evidence(evidence_data)
    
    def get_evidence_by_domain(self, user, domain: str) -> List[CompetencyEvidence]:
        """
        Get all evidence for a user in a specific domain.
        """
        return CompetencyEvidence.objects.filter(
            user=user,
            domain=domain
        ).order_by('-completed_at')
    
    def get_latest_evidence(self, user, limit: int = 10) -> List[CompetencyEvidence]:
        """
        Get the latest evidence for a user.
        """
        return CompetencyEvidence.objects.filter(
            user=user
        ).order_by('-completed_at')[:limit]
    
    def get_evidence_stats(self, user) -> Dict:
        """
        Get statistics about a user's evidence.
        """
        evidence = CompetencyEvidence.objects.filter(user=user)
        
        return {
            'total_evidence': evidence.count(),
            'verified': evidence.filter(status='verified').count(),
            'pending': evidence.filter(status='submitted').count(),
            'by_type': evidence.values('activity_type').annotate(count=models.Count('id')),
            'by_domain': evidence.values('domain').annotate(count=models.Count('id')),
            'avg_performance': evidence.aggregate(avg=models.Avg('performance_score'))['avg__avg'],
            'quality_score_avg': evidence.aggregate(avg=models.Avg('quality_score'))['avg__avg'],
        }
    
    def archive_old_evidence(self, days: int = 365):
        """
        Archive evidence older than specified days.
        """
        cutoff = timezone.now() - timedelta(days=days)
        old_evidence = CompetencyEvidence.objects.filter(
            completed_at__lt=cutoff,
            status='verified'
        )
        
        for evidence in old_evidence:
            evidence.status = 'archived'
            evidence.save()
        
        return old_evidence.count()
