"""
Competency Engine
Core logic for mapping activities → evidence → competencies → proficiency levels
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import List, Dict, Any, Optional, Tuple
import logging
import json

from evidence.models import CompetencyFramework, Competency, CompetencyEvidence, CompetencyAssessment
from evidence.services import EvidenceService

User = get_user_model()
logger = logging.getLogger(__name__)


class CompetencyEngine:
    """
    Engine for managing competency evidence and assessments.
    """
    
    # Proficiency level thresholds
    LEVEL_THRESHOLDS = {
        'beginner': 0.0,
        'developing': 0.3,
        'proficient': 0.6,
        'advanced': 0.8,
        'expert': 0.9,
    }
    
    def __init__(self, user: User):
        self.user = user
    
    def process_evidence(self, activity_data: Dict) -> CompetencyEvidence:
        """
        Process a learning activity and create structured evidence.
        
        Args:
            activity_data: Dict containing activity details and results
        
        Returns:
            CompetencyEvidence instance
        """
        with transaction.atomic():
            # Extract data
            activity_type = activity_data.get('activity_type', 'quiz')
            activity_id = activity_data.get('activity_id')
            activity_name = activity_data.get('activity_name', 'Learning Activity')
            
            # Get performance data
            performance_score = activity_data.get('performance_score', 0)
            difficulty = activity_data.get('difficulty_level', 3)
            time_spent = activity_data.get('time_spent')
            
            # Map to competencies
            competencies = self._map_to_competencies(activity_data)
            skills = self._map_to_skills(activity_data)
            
            # Create evidence
            evidence = CompetencyEvidence.objects.create(
                user=self.user,
                activity_type=activity_type,
                activity_id=activity_id,
                activity_name=activity_name,
                performance_score=performance_score,
                difficulty_level=difficulty,
                time_spent=time_spent,
                competencies_demonstrated=competencies,
                skills_demonstrated=skills,
                evidence_data=activity_data.get('evidence_data', {}),
                context_data=activity_data.get('context', {}),
                domain=activity_data.get('domain', 'general'),
                tags=activity_data.get('tags', []),
                status='submitted',
                completed_at=activity_data.get('completed_at', timezone.now()),
            )
            
            # Calculate quality score
            evidence.quality_score = self._calculate_quality_score(evidence)
            evidence.save()
            
            # Update competency assessments
            self._update_competency_assessments(evidence)
            
            # Create audit trail
            evidence.transactions.create(
                user=self.user,
                action='created',
                changes={'activity_data': activity_data}
            )
            
            logger.info(f"Created competency evidence for user {self.user.id}")
            return evidence
    
    def _map_to_competencies(self, activity_data: Dict) -> List[Dict]:
        """
        Map activity data to competencies.
        This would use AI or predefined rules.
        """
        competencies = []
        
        # Get the domain
        domain = activity_data.get('domain', 'general')
        
        # Get concepts attempted
        concepts = activity_data.get('concepts', [])
        
        # For each concept, map to competencies
        for concept in concepts:
            # This is a simplified mapping - in production, you'd use
            # AI or a mapping table to map concepts to competencies
            competency_data = {
                'competency_id': str(concept.get('id')),
                'level': self._determine_proficiency_level(activity_data, concept),
                'confidence': self._calculate_confidence(activity_data, concept),
            }
            competencies.append(competency_data)
        
        return competencies
    
    def _map_to_skills(self, activity_data: Dict) -> List[Dict]:
        """
        Map activity data to skills demonstrated.
        """
        skills = []
        performance_score = activity_data.get('performance_score', 0)
        
        # Extract skills from activity data
        skill_ids = activity_data.get('skill_ids', [])
        
        for skill_id in skill_ids:
            skill_data = {
                'skill_id': skill_id,
                'proficiency': performance_score / 100.0,  # Normalize
                'confidence': 0.7,  # Initial confidence
            }
            skills.append(skill_data)
        
        return skills
    
    def _determine_proficiency_level(self, activity_data: Dict, concept: Dict) -> str:
        """
        Determine proficiency level based on performance and difficulty.
        """
        performance = activity_data.get('performance_score', 0)
        difficulty = activity_data.get('difficulty_level', 3)
        
        # Adjust for difficulty (harder tasks require lower scores for same level)
        difficulty_factor = difficulty / 5.0
        adjusted_score = performance * difficulty_factor
        
        if adjusted_score >= 85:
            return 'expert'
        elif adjusted_score >= 70:
            return 'advanced'
        elif adjusted_score >= 55:
            return 'proficient'
        elif adjusted_score >= 35:
            return 'developing'
        else:
            return 'beginner'
    
    def _calculate_confidence(self, activity_data: Dict, concept: Dict) -> float:
        """
        Calculate confidence in the competency assessment.
        """
        # Base confidence from performance
        performance = activity_data.get('performance_score', 0)
        base_confidence = performance / 100.0
        
        # Adjust based on evidence strength
        evidence_strength = self._calculate_evidence_strength(activity_data)
        confidence = base_confidence * evidence_strength
        
        return min(confidence, 1.0)
    
    def _calculate_evidence_strength(self, activity_data: Dict) -> float:
        """
        Calculate evidence strength based on activity type and quality.
        """
        activity_type = activity_data.get('activity_type', 'quiz')
        strengths = {
            'exam': 1.0,
            'project': 0.95,
            'simulation': 0.9,
            'practical': 0.9,
            'portfolio': 0.95,
            'internship': 0.95,
            'quiz': 0.7,
            'discussion': 0.6,
            'peer_review': 0.65,
            'self_assessment': 0.5,
        }
        return strengths.get(activity_type, 0.7)
    
    def _calculate_quality_score(self, evidence: CompetencyEvidence) -> Optional[float]:
        """
        Calculate the quality score for evidence.
        """
        score = 0.0
        max_score = 100.0
        
        # Activity quality
        activity_weights = {
            'exam': 15,
            'project': 20,
            'simulation': 15,
            'practical': 15,
            'portfolio': 20,
            'internship': 20,
            'quiz': 10,
            'discussion': 5,
            'peer_review': 5,
            'self_assessment': 3,
        }
        score += activity_weights.get(evidence.activity_type, 5)
        
        # Performance quality
        if evidence.performance_score >= 80:
            score += 30
        elif evidence.performance_score >= 60:
            score += 20
        elif evidence.performance_score >= 40:
            score += 10
        
        # Evidence completeness
        if evidence.evidence_data:
            score += 10
        
        # Domain relevance
        if evidence.domain:
            score += 5
        
        # TODO: Add more sophisticated quality scoring
        # - AI evaluation of evidence content
        # - Peer feedback
        # - Instructor verification
        
        return score
    
    def _update_competency_assessments(self, evidence: CompetencyEvidence):
        """
        Update or create competency assessments based on new evidence.
        """
        for comp_data in evidence.competencies_demonstrated:
            competency_id = comp_data.get('competency_id')
            level = comp_data.get('level', 'beginner')
            confidence = comp_data.get('confidence', 0.5)
            
            if not competency_id:
                continue
            
            # Get or create assessment
            assessment, created = CompetencyAssessment.objects.get_or_create(
                user=self.user,
                competency_id=competency_id,
                defaults={
                    'level_achieved': level,
                    'confidence_score': confidence,
                    'assessed_at': timezone.now(),
                    'assessment_method': 'ai_engine',
                }
            )
            
            # If existing assessment, update if new evidence is better
            if not created:
                # Check if new evidence is better
                level_weight = list(Competency.LEVEL_CHOICES).index(level)
                current_level = assessment.level_achieved
                current_weight = list(Competency.LEVEL_CHOICES).index(current_level)
                
                # Update only if new level is higher or confidence is much higher
                if (level_weight > current_weight or 
                    (level_weight == current_weight and confidence > assessment.confidence_score * 1.2)):
                    assessment.level_achieved = level
                    assessment.confidence_score = confidence
                    assessment.assessed_at = timezone.now()
                    assessment.assessment_method = 'ai_engine'
                
                # Add evidence to assessment
                if evidence not in assessment.evidence_used.all():
                    assessment.evidence_used.add(evidence)
                    assessment.evidence_count = assessment.evidence_used.count()
                
                assessment.save()
    
    def get_competency_profile(self) -> Dict[str, Any]:
        """
        Get the complete competency profile for the user.
        """
        assessments = CompetencyAssessment.objects.filter(
            user=self.user
        ).select_related('competency', 'competency__framework')
        
        profile = {
            'user_id': str(self.user.id),
            'assessments': [],
            'summary': {
                'total_competencies': assessments.count(),
                'by_level': {},
                'by_framework': {},
            }
        }
        
        for assessment in assessments:
            # Add to assessments list
            assessment_data = {
                'competency_id': str(assessment.competency.id),
                'competency_name': assessment.competency.name,
                'competency_code': assessment.competency.code,
                'framework': assessment.competency.framework.name,
                'level_achieved': assessment.level_achieved,
                'confidence': assessment.confidence_score,
                'evidence_count': assessment.evidence_count,
                'assessed_at': assessment.assessed_at,
            }
            profile['assessments'].append(assessment_data)
            
            # Update summary
            level = assessment.level_achieved
            profile['summary']['by_level'][level] = profile['summary']['by_level'].get(level, 0) + 1
            
            framework = assessment.competency.framework.name
            profile['summary']['by_framework'][framework] = profile['summary']['by_framework'].get(framework, 0) + 1
        
        return profile
    
    def verify_evidence(self, evidence_id: str, verifier: User, notes: str = '') -> CompetencyEvidence:
        """
        Verify evidence manually.
        """
        evidence = CompetencyEvidence.objects.get(id=evidence_id, user=self.user)
        
        evidence.status = 'verified'
        evidence.verified_at = timezone.now()
        evidence.verified_by = verifier
        evidence.verification_notes = notes
        evidence.save()
        
        # Update confidence for related assessments
        for comp_data in evidence.competencies_demonstrated:
            competency_id = comp_data.get('competency_id')
            if competency_id:
                assessment = CompetencyAssessment.objects.filter(
                    user=self.user,
                    competency_id=competency_id
                ).first()
                if assessment:
                    assessment.confidence_score = min(assessment.confidence_score + 0.1, 1.0)
                    assessment.save()
        
        # Create audit trail
        evidence.transactions.create(
            user=verifier,
            action='verified',
            changes={'notes': notes}
        )
        
        return evidence
    
    def get_evidence_recommendations(self) -> List[Dict]:
        """
        Recommend evidence to collect for missing competencies.
        """
        recommendations = []
        
        # Get all competencies
        all_competencies = Competency.objects.filter(is_active=True)
        
        # Get assessed competencies
        assessed_ids = CompetencyAssessment.objects.filter(
            user=self.user
        ).values_list('competency_id', flat=True)
        
        # Find missing competencies
        missing = all_competencies.exclude(id__in=assessed_ids)
        
        for competency in missing[:10]:  # Top 10 recommendations
            recommendations.append({
                'competency_id': str(competency.id),
                'competency_name': competency.name,
                'framework': competency.framework.name,
                'required_level': competency.level,
                'evidence_types': competency.evidence_types,
                'assessment_criteria': competency.assessment_criteria,
                'priority': 'high' if competency.prerequisites.exists() else 'medium',
            })
        
        return recommendations
