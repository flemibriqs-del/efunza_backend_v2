"""
Closed Loop Service
Implements the complete closed-loop learning cycle:
OBSERVE → UNDERSTAND → DIAGNOSE → RECOMMEND → TEACH/PRACTICE → 
ASSESS → VERIFY → UPDATE → RECOMMEND NEXT ACTION
"""

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import timedelta

from .intelligence_service import IntelligenceService
from .rag_service import RAGService

logger = logging.getLogger(__name__)


class ClosedLoopService:
    """
    Orchestrates the complete closed-loop learning cycle.
    """
    
    def __init__(self, user):
        """
        Initialize the closed-loop service.
        
        Args:
            user: The user instance
        """
        self.user = user
        self.intelligence_service = IntelligenceService(user)
    
    @transaction.atomic
    def execute_loop(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one complete closed-loop cycle.
        
        This is the main method that should be called for every
        significant learning interaction.
        
        Args:
            event_data: Learning event data
        
        Returns:
            Complete loop results
        """
        logger.info(f"Starting closed-loop for user {self.user.id}")
        
        loop_data = {
            'user_id': str(self.user.id),
            'start_time': timezone.now().isoformat(),
            'steps': {},
            'duration': None,
        }
        
        start = timezone.now()
        
        # STEP 1: OBSERVE
        logger.debug("Closed-loop: OBSERVE")
        loop_data['steps']['observe'] = self._step_observe(event_data)
        
        # STEP 2: UNDERSTAND
        logger.debug("Closed-loop: UNDERSTAND")
        loop_data['steps']['understand'] = self._step_understand(event_data)
        
        # STEP 3: DIAGNOSE
        logger.debug("Closed-loop: DIAGNOSE")
        loop_data['steps']['diagnose'] = self._step_diagnose()
        
        # STEP 4: RECOMMEND
        logger.debug("Closed-loop: RECOMMEND")
        loop_data['steps']['recommend'] = self._step_recommend(loop_data['steps']['diagnose'])
        
        # STEP 5: TEACH/PRACTICE - This is returned to the client
        
        # STEP 6: ASSESS - Will happen in next event
        
        # STEP 7: VERIFY
        logger.debug("Closed-loop: VERIFY")
        loop_data['steps']['verify'] = self._step_verify(event_data)
        
        # STEP 8: UPDATE - Happened in understand step
        
        # STEP 9: RECOMMEND NEXT ACTION - Already in recommend step
        
        # Calculate loop duration
        end = timezone.now()
        loop_data['duration'] = (end - start).total_seconds()
        loop_data['end_time'] = end.isoformat()
        loop_data['status'] = 'success'
        
        # Add the recommendation for the next action
        loop_data['next_action'] = loop_data['steps']['recommend']
        
        # Add summary
        loop_data['summary'] = self._generate_summary(loop_data)
        
        # Cache the loop results for performance
        cache_key = f"loop_{self.user.id}_{int(timezone.now().timestamp())}"
        cache.set(cache_key, loop_data, 3600)
        
        logger.info(f"Closed-loop completed in {loop_data['duration']:.2f} seconds")
        
        return loop_data
    
    def _step_observe(self, event_data: Dict) -> Dict:
        """OBSERVE: Collect and structure event data."""
        return {
            'event_type': event_data.get('event_type', 'unknown'),
            'event_id': event_data.get('event_id'),
            'timestamp': timezone.now().isoformat(),
            'data': event_data,
        }
    
    def _step_understand(self, event_data: Dict) -> Dict:
        """UNDERSTAND: Process event and update understanding."""
        try:
            # Process the learning event
            result = self.intelligence_service.process_learning_event(event_data)
            
            return {
                'mastery_updates': result['understanding']['mastery_updates'],
                'evidence_id': result['understanding']['evidence_id'],
                'engagement_score': result['understanding']['engagement_score'],
                'profile_updated': True,
                'timestamp': timezone.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in understand step: {str(e)}")
            return {
                'error': str(e),
                'profile_updated': False,
            }
    
    def _step_diagnose(self) -> Dict:
        """DIAGNOSE: Analyze learner's state."""
        try:
            # Get diagnosis from intelligence service
            # We'll just use the diagnosis from the latest processing
            diagnosis = {
                'weaknesses': self.intelligence_service.profile.weaknesses,
                'mastery_level': self._calculate_mastery_level(),
                'engagement': self.intelligence_service.profile.engagement_score,
                'growth_rate': self.intelligence_service.profile.knowledge_growth_rate,
                'ready_for_advancement': self._check_advancement_readiness(),
                'career_readiness': self.intelligence_service.profile.career_readiness_level,
                'learning_goals': self.intelligence_service.profile.learning_goals,
            }
            
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error in diagnose step: {str(e)}")
            return {'error': str(e)}
    
    def _step_recommend(self, diagnosis: Dict) -> Dict:
        """RECOMMEND: Generate next action."""
        try:
            # Get recommendation from action engine
            action = self.intelligence_service.action_engine.get_next_action()
            
            # Enhance with personalization
            action['recommendation_context'] = {
                'based_on_weaknesses': len(diagnosis.get('weaknesses', [])) > 0,
                'based_on_mastery': diagnosis.get('mastery_level', 0),
                'based_on_engagement': diagnosis.get('engagement', 0),
            }
            
            # Add learning format recommendation
            action['recommended_format'] = self._get_recommended_format(action)
            
            return action
            
        except Exception as e:
            logger.error(f"Error in recommend step: {str(e)}")
            return {'error': str(e)}
    
    def _step_verify(self, event_data: Dict) -> Dict:
        """VERIFY: Check if evidence needs verification."""
        verification = {
            'needs_verification': False,
            'verification_status': 'auto_verified',
            'timestamp': timezone.now().isoformat(),
        }
        
        # Check if this is a high-stakes activity
        high_stakes = ['exam', 'project', 'internship', 'certification']
        if event_data.get('event_type') in high_stakes:
            verification['needs_verification'] = True
            verification['verification_status'] = 'pending'
            verification['reason'] = 'High-stakes activity requires review'
        
        # Check for exceptional performance
        if event_data.get('performance_score', 0) >= 95:
            verification['needs_verification'] = True
            verification['verification_status'] = 'pending'
            verification['reason'] = 'Exceptional performance needs review'
        
        # Check for suspicious patterns
        if self._detect_suspicious_pattern(event_data):
            verification['needs_verification'] = True
            verification['verification_status'] = 'flagged'
            verification['reason'] = 'Suspicious activity pattern detected'
        
        return verification
    
    def _calculate_mastery_level(self) -> float:
        """Calculate overall mastery level."""
        if not self.intelligence_service.profile.concept_mastery:
            return 0.0
        
        masteries = list(self.intelligence_service.profile.concept_mastery.values())
        return sum(masteries) / len(masteries)
    
    def _check_advancement_readiness(self) -> bool:
        """Check if learner is ready to advance."""
        profile = self.intelligence_service.profile
        
        # Check if majority of concepts are mastered
        if not profile.concept_mastery:
            return False
        
        mastered = len([m for m in profile.concept_mastery.values() if m >= 0.7])
        total = len(profile.concept_mastery)
        
        if total > 0 and mastered / total >= 0.8:
            return True
        
        return False
    
    def _get_recommended_format(self, action: Dict) -> str:
        """
        Get recommended learning format based on action type.
        """
        action_type = action.get('action', 'learn')
        
        format_map = {
            'learn': 'video_and_reading',
            'remediate': 'tutorial_and_practice',
            'practice': 'quizzes_and_exercises',
            'simulate': 'interactive_simulation',
            'build': 'guided_project',
            'challenge': 'advanced_problems',
            'advance': 'progression_assessment',
        }
        
        return format_map.get(action_type, 'mixed')
    
    def _detect_suspicious_pattern(self, event_data: Dict) -> bool:
        """
        Detect suspicious learning patterns.
        """
        # Check for impossible timings
        time_spent = event_data.get('time_spent', 0)
        if time_spent and time_spent < 30 and event_data.get('performance_score', 0) > 90:
            return True
        
        # Check for repeated perfect scores
        # This would need historical data comparison
        
        return False
    
    def _generate_summary(self, loop_data: Dict) -> Dict:
        """
        Generate a human-readable summary of the loop.
        """
        steps = loop_data.get('steps', {})
        recommend = steps.get('recommend', {})
        
        summary = {
            'action_taken': recommend.get('action', 'none'),
            'action_reason': recommend.get('reason', ''),
            'priority': recommend.get('priority', 0),
            'weaknesses_identified': len(steps.get('diagnose', {}).get('weaknesses', [])),
            'verified': steps.get('verify', {}).get('verification_status') == 'auto_verified',
        }
        
        if recommend.get('target'):
            summary['target_concept'] = recommend.get('target')
        
        return summary
    
    def get_loop_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent closed-loop history for the user.
        """
        # Get from cache or database
        # For now, we'll get from cache
        cache_pattern = f"loop_{self.user.id}_*"
        keys = cache.keys(cache_pattern)
        
        loops = []
        for key in sorted(keys, reverse=True)[:limit]:
            data = cache.get(key)
            if data:
                loops.append({
                    'timestamp': data.get('end_time'),
                    'action': data.get('next_action', {}).get('action'),
                    'status': data.get('status'),
                    'duration': data.get('duration'),
                })
        
        return loops
