"""
Intelligence Service
Main orchestration service that ties everything together
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Dict, Any, Optional, List, Tuple
import logging
import json

from intelligence.models import StudentIntelligenceProfile
from intelligence.engines import MasteryEngine, NextBestActionEngine
from knowledge_graph.models import Concept, Topic, Subject
from evidence.models import CompetencyEvidence
from evidence.engines.competency_engine import CompetencyEngine

User = get_user_model()
logger = logging.getLogger(__name__)


class IntelligenceService:
    """
    Central intelligence service that orchestrates all components.
    Implements the closed-loop: OBSERVE → UNDERSTAND → DIAGNOSE → 
    RECOMMEND → TEACH/PRACTICE → ASSESS → VERIFY → UPDATE → RECOMMEND
    """
    
    def __init__(self, user: User):
        """
        Initialize the intelligence service for a user.
        
        Args:
            user: The user instance
        """
        self.user = user
        self.profile = self._get_or_create_profile()
        self.mastery_engine = MasteryEngine(self.profile)
        self.action_engine = NextBestActionEngine(self.profile)
        self.competency_engine = CompetencyEngine(user)
    
    def _get_or_create_profile(self) -> StudentIntelligenceProfile:
        """Get or create the student intelligence profile."""
        profile, created = StudentIntelligenceProfile.objects.get_or_create(
            user=self.user
        )
        if created:
            logger.info(f"Created new intelligence profile for user {self.user.id}")
        return profile
    
    def process_learning_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a learning event through the complete closed-loop.
        
        This is the main entry point for all learning activities.
        
        Args:
            event_data: Dictionary containing event details
                - event_type: 'quiz', 'simulation', 'practical', 'project', etc.
                - event_id: ID of the event
                - concepts: List of concept IDs involved
                - performance_score: Score achieved (0-100)
                - difficulty_level: Difficulty of the activity (1-10)
                - time_spent: Time spent in seconds
                - domain: Domain of the activity
                - metadata: Additional metadata
        
        Returns:
            Dict with processed results including next actions
        """
        logger.info(f"Processing learning event for user {self.user.id}")
        
        # STEP 1: OBSERVE - Collect the event data
        observation = self._observe_event(event_data)
        
        # STEP 2: UNDERSTAND - Update mastery and create evidence
        understanding = self._understand_event(observation)
        
        # STEP 3: DIAGNOSE - Analyze mastery and identify gaps
        diagnosis = self._diagnose_learner()
        
        # STEP 4: RECOMMEND - Generate next best action
        recommendation = self._recommend_action(diagnosis)
        
        # STEP 5: TEACH/PRACTICE - This happens outside this service
        # The recommendation is returned to the client to execute
        
        # STEP 6: ASSESS - This will happen when the next event comes in
        
        # STEP 7: VERIFY - Check if evidence is verified
        verification = self._verify_evidence(observation)
        
        # STEP 8: UPDATE - Profile is already updated in understanding step
        
        # STEP 9: RECOMMEND - Already done in step 4
        
        # Return the complete loop result
        return {
            'loop_id': f"{self.user.id}_{timezone.now().timestamp()}",
            'event': observation,
            'understanding': understanding,
            'diagnosis': diagnosis,
            'recommendation': recommendation,
            'verification': verification,
            'profile_summary': self._get_profile_summary(),
            'timestamp': timezone.now().isoformat(),
        }
    
    def _observe_event(self, event_data: Dict) -> Dict:
        """
        OBSERVE: Collect and structure the event data.
        """
        observation = {
            'event_type': event_data.get('event_type', 'unknown'),
            'event_id': event_data.get('event_id'),
            'concepts': event_data.get('concepts', []),
            'performance_score': event_data.get('performance_score', 0),
            'difficulty_level': event_data.get('difficulty_level', 3),
            'time_spent': event_data.get('time_spent', 0),
            'domain': event_data.get('domain', 'general'),
            'metadata': event_data.get('metadata', {}),
            'observed_at': timezone.now().isoformat(),
        }
        
        # Update profile with activity
        self.profile.total_attempts += 1
        if observation['performance_score'] >= 70:
            self.profile.total_correct += 1
        
        # Update average score
        total_scored = self.profile.average_score * (self.profile.total_attempts - 1)
        self.profile.average_score = (
            total_scored + observation['performance_score']
        ) / self.profile.total_attempts
        
        # Update last activity date
        self.profile.last_activity_date = timezone.now()
        self.profile.save()
        
        logger.debug(f"Observed event: {observation['event_type']} with score {observation['performance_score']}")
        
        return observation
    
    def _understand_event(self, observation: Dict) -> Dict:
        """
        UNDERSTAND: Update mastery and create evidence from the event.
        """
        with transaction.atomic():
            # 1. Update mastery scores
            mastery_updates = self.mastery_engine.update_all_mastery()
            
            # 2. Create competency evidence
            evidence_data = {
                'activity_type': observation['event_type'],
                'activity_id': observation['event_id'],
                'activity_name': observation.get('event_name', 'Learning Activity'),
                'performance_score': observation['performance_score'],
                'difficulty_level': observation['difficulty_level'],
                'completed_at': timezone.now(),
                'concepts': observation['concepts'],
                'domain': observation['domain'],
                'context': observation.get('metadata', {}),
                'tags': observation.get('tags', []),
            }
            
            evidence = self.competency_engine.process_evidence(evidence_data)
            
            # 3. Update engagement score
            self.profile.update_engagement_score(
                activity_type=observation['event_type'],
                performance=observation['performance_score']
            )
            
            understanding = {
                'mastery_updates': mastery_updates,
                'evidence_id': str(evidence.id) if evidence else None,
                'engagement_score': self.profile.engagement_score,
                'total_attempts': self.profile.total_attempts,
            }
            
            logger.info(f"Understood event: {len(mastery_updates.get('concepts_updated', 0))} concepts updated")
            
            return understanding
    
    def _diagnose_learner(self) -> Dict:
        """
        DIAGNOSE: Analyze the learner's current state.
        """
        diagnosis = {
            'mastery_summary': {
                'average_mastery': 0,
                'mastered_concepts': 0,
                'weak_concepts': len(self.profile.weaknesses),
                'growth_rate': self.profile.knowledge_growth_rate,
            },
            'weaknesses': self.profile.weaknesses[:5],
            'strengths': self._identify_strengths(),
            'readiness': self._assess_readiness(),
            'engagement': {
                'score': self.profile.engagement_score,
                'consistency': self.profile.consistency_score,
                'curiosity': self.profile.curiosity_score,
            },
        }
        
        # Calculate summary stats
        if self.profile.concept_mastery:
            masteries = list(self.profile.concept_mastery.values())
            diagnosis['mastery_summary']['average_mastery'] = sum(masteries) / len(masteries)
            diagnosis['mastery_summary']['mastered_concepts'] = len([
                m for m in masteries if m >= 0.7
            ])
        
        # Add career readiness
        diagnosis['career_readiness'] = {
            'level': self.profile.career_readiness_level,
            'recommended_paths': self.profile.recommended_career_paths,
        }
        
        logger.debug(f"Diagnosed learner: {diagnosis['mastery_summary']}")
        
        return diagnosis
    
    def _recommend_action(self, diagnosis: Dict) -> Dict:
        """
        RECOMMEND: Generate the next best action.
        """
        # Get recommendation from action engine
        action = self.action_engine.get_next_action({
            'diagnosis': diagnosis,
            'current_time': timezone.now().isoformat(),
        })
        
        # Enhance with personalization
        action['personalized'] = {
            'based_on_engagement': diagnosis['engagement']['score'],
            'based_on_weaknesses': len(diagnosis['weaknesses']) > 0,
            'recommended_format': self._get_preferred_learning_format(),
        }
        
        # Add context to the action
        if action['target']:
            try:
                concept = Concept.objects.get(id=int(action['target']))
                action['target_name'] = concept.name
                action['topic_name'] = concept.topic.name
                action['difficulty'] = concept.difficulty
            except (Concept.DoesNotExist, ValueError):
                pass
        
        logger.info(f"Recommended action: {action['action']} (priority: {action['priority']})")
        
        return action
    
    def _verify_evidence(self, observation: Dict) -> Dict:
        """
        VERIFY: Check if evidence needs verification.
        """
        # Check if the evidence needs manual verification
        needs_verification = False
        reason = None
        
        # High-stakes activities need verification
        high_stakes_types = ['exam', 'project', 'internship']
        if observation['event_type'] in high_stakes_types:
            needs_verification = True
            reason = 'High-stakes activity requires verification'
        
        # Very high scores might need verification
        if observation['performance_score'] >= 95:
            needs_verification = True
            reason = 'Exceptional performance needs verification'
        
        # Check for suspicious patterns
        if self._detect_anomaly(observation):
            needs_verification = True
            reason = 'Suspicious activity pattern detected'
        
        return {
            'needs_verification': needs_verification,
            'reason': reason,
            'auto_verified': not needs_verification,
            'verification_deadline': (
                timezone.now() + timezone.timedelta(days=7)
            ).isoformat() if needs_verification else None,
        }
    
    def _identify_strengths(self) -> List[Dict]:
        """Identify the learner's strengths."""
        strengths = []
        
        for concept_id, mastery in self.profile.concept_mastery.items():
            if mastery >= 0.8:
                try:
                    concept = Concept.objects.get(id=int(concept_id))
                    strengths.append({
                        'concept_id': concept_id,
                        'concept_name': concept.name,
                        'mastery': mastery,
                        'topic': concept.topic.name,
                    })
                except (Concept.DoesNotExist, ValueError):
                    continue
        
        return sorted(strengths, key=lambda x: x['mastery'], reverse=True)[:5]
    
    def _assess_readiness(self) -> Dict:
        """Assess the learner's readiness for advancement."""
        readiness = {
            'ready_to_advance': False,
            'blocking_concepts': [],
            'recommended_action': None,
        }
        
        # Check if all core concepts are mastered
        core_concepts = []
        for concept_id, mastery in self.profile.concept_mastery.items():
            try:
                concept = Concept.objects.get(id=int(concept_id))
                if concept.is_core and mastery < 0.7:
                    core_concepts.append({
                        'concept_id': concept_id,
                        'concept_name': concept.name,
                        'mastery': mastery,
                    })
            except (Concept.DoesNotExist, ValueError):
                continue
        
        if not core_concepts:
            readiness['ready_to_advance'] = True
        else:
            readiness['blocking_concepts'] = core_concepts[:3]
            readiness['recommended_action'] = 'remediate_core_concepts'
        
        return readiness
    
    def _get_preferred_learning_format(self) -> str:
        """Get the user's preferred learning format."""
        preferences = self.profile.preferred_learning_styles
        
        if not preferences:
            return 'mixed'
        
        # Return most preferred format
        return preferences[0] if preferences else 'mixed'
    
    def _detect_anomaly(self, observation: Dict) -> bool:
        """
        Detect anomalous learning patterns.
        """
        # Check for too fast completion
        if observation['time_spent'] and observation['time_spent'] < 30:  # Less than 30 seconds
            return True
        
        # Check for impossible scores
        if observation['performance_score'] > 100 or observation['performance_score'] < 0:
            return True
        
        # Check for repeated identical patterns
        # This would need historical data comparison
        
        return False
    
    def _get_profile_summary(self) -> Dict:
        """Get a summary of the learner's profile."""
        return {
            'total_attempts': self.profile.total_attempts,
            'total_correct': self.profile.total_correct,
            'average_score': self.profile.average_score,
            'engagement_score': self.profile.engagement_score,
            'mastered_concepts': len([
                m for m in self.profile.concept_mastery.values() if m >= 0.7
            ]),
            'weak_concepts': len(self.profile.weaknesses),
            'career_readiness': self.profile.career_readiness_level,
        }
    
    def get_learning_path(self, subject_id: Optional[str] = None) -> Dict:
        """
        Get personalized learning path for the user.
        
        Args:
            subject_id: Optional subject ID to filter by
        
        Returns:
            Dict with personalized learning path
        """
        from knowledge_graph.services import KnowledgeGraphService
        
        if subject_id:
            path = KnowledgeGraphService.get_learning_path(subject_id, self.user)
            
            # Add personalized progress to each concept
            for topic in path.get('topics', []):
                for concept in topic.get('concepts', []):
                    concept_id = concept.get('id')
                    if concept_id:
                        mastery = self.profile.get_mastery_for_concept(concept_id)
                        concept['mastery'] = mastery
                        concept['mastery_status'] = self._get_mastery_status(mastery)
            
            return path
        
        # Get all subjects
        subjects = Subject.objects.filter(is_active=True)
        paths = []
        
        for subject in subjects:
            subject_path = KnowledgeGraphService.get_learning_path(str(subject.id), self.user)
            paths.append(subject_path)
        
        return {'subjects': paths}
    
    def _get_mastery_status(self, mastery: float) -> str:
        """Get mastery status label."""
        if mastery >= 0.8:
            return 'mastered'
        elif mastery >= 0.6:
            return 'proficient'
        elif mastery >= 0.3:
            return 'developing'
        elif mastery > 0:
            return 'beginner'
        else:
            return 'not_started'
