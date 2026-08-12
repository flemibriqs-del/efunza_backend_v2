"""
Next-Best-Action Engine
Decides whether the learner should:
- Learn
- Remediate
- Practice
- Reassess
- Simulate
- Build
- Challenge
- Advance
"""

from django.utils import timezone
from typing import Dict, Any, Optional, List
import random
import logging

from .base_engine import BaseEngine
from intelligence.models import StudentIntelligenceProfile
from knowledge_graph.models import Concept, Topic

logger = logging.getLogger(__name__)


class NextBestActionEngine(BaseEngine):
    """
    Engine for determining the next best learning action.
    """
    
    # Action types
    ACTION_LEARN = 'learn'
    ACTION_REMEDIATE = 'remediate'
    ACTION_PRACTICE = 'practice'
    ACTION_REASSESS = 'reassess'
    ACTION_SIMULATE = 'simulate'
    ACTION_BUILD = 'build'
    ACTION_CHALLENGE = 'challenge'
    ACTION_ADVANCE = 'advance'
    
    # Action priorities
    PRIORITY_CRITICAL = 10
    PRIORITY_HIGH = 8
    PRIORITY_MEDIUM = 6
    PRIORITY_LOW = 4
    
    def __init__(self, profile: StudentIntelligenceProfile):
        """
        Initialize with a student profile.
        
        Args:
            profile: StudentIntelligenceProfile instance
        """
        self.profile = profile
        self.user = profile.user
        self.mastery_engine = MasteryEngine(profile)
    
    def get_next_action(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Determine the optimal next action for the learner.
        
        Args:
            context: Optional context data (current concept, assessment, etc.)
        
        Returns:
            Dict with action details
        """
        if context is None:
            context = {}
        
        logger.info(f"Determining next action for user {self.user.id}")
        
        # Priority 1: Check for critical weaknesses
        critical_action = self._check_critical_weaknesses()
        if critical_action:
            return critical_action
        
        # Priority 2: Check for reassessment needs
        if self._needs_reassessment():
            return self._action_reassess()
        
        # Priority 3: Check for advancement opportunities
        if self._is_ready_for_advancement():
            return self._action_advance()
        
        # Priority 4: Check for skill gap simulation
        skill_gap = self._check_skill_gaps()
        if skill_gap:
            return self._action_simulate(skill_gap)
        
        # Priority 5: Find next concept to learn
        next_concept = self._find_next_learning_concept()
        if next_concept:
            return self._action_learn(next_concept)
        
        # Priority 6: Practice existing knowledge
        practice_concept = self._find_practice_concept()
        if practice_concept:
            return self._action_practice(practice_concept)
        
        # Default: Challenge with new content
        return self._action_challenge()
    
    def _check_critical_weaknesses(self) -> Optional[Dict]:
        """
        Check for critical weaknesses that need immediate attention.
        """
        if not self.profile.weaknesses:
            return None
        
        # Get the highest priority weakness
        top_weakness = self.profile.weaknesses[0]
        if top_weakness['priority'] >= 8:  # High priority
            concept_id = top_weakness['concept_id']
            gap_score = top_weakness['gap_score']
            
            # Check if we've recently attempted this
            attempts = self.mastery_engine._get_concept_attempts(concept_id)
            
            if not attempts:
                # Never attempted - need to learn
                return self._action_learn(concept_id, priority=self.PRIORITY_CRITICAL)
            elif attempts and len(attempts) >= 2:
                # Attempted but still struggling - need remediation
                return self._action_remediate(
                    concept_id, 
                    gap_score=gap_score,
                    priority=self.PRIORITY_CRITICAL
                )
            else:
                # Need more practice
                return self._action_practice(
                    concept_id,
                    priority=self.PRIORITY_HIGH
                )
        
        return None
    
    def _check_skill_gaps(self) -> Optional[str]:
        """
        Check for skill gaps that need simulation/practical work.
        """
        try:
            from evidence.models import CompetencyEvidence
            
            # Get evidence stats
            evidence_count = CompetencyEvidence.objects.filter(
                user=self.user,
                activity_type__in=['simulation', 'practical', 'project']
            ).count()
            
            # If no practical evidence, recommend simulation
            if evidence_count == 0 and self.profile.weaknesses:
                return self.profile.weaknesses[0]['concept_id']
            
            return None
            
        except (ImportError, AttributeError):
            # Evidence app not installed
            return None
    
    def _needs_reassessment(self) -> bool:
        """
        Check if reassessment is needed (stale data).
        """
        if not self.profile.last_activity_date:
            return False
        
        days_since = (timezone.now() - self.profile.last_activity_date).days
        
        # Reassess if:
        # 1. More than 7 days since last activity
        # 2. Very few attempts relative to concept count
        if days_since > 7:
            return True
        
        concept_count = len(self.profile.concept_mastery)
        if concept_count > 0:
            attempts_per_concept = self.profile.total_attempts / concept_count
            if attempts_per_concept < 2:
                return True
        
        return False
    
    def _is_ready_for_advancement(self) -> bool:
        """
        Check if learner is ready to advance to next level.
        """
        if not self.profile.topic_mastery:
            return False
        
        # Check if all core topics have high mastery
        mastered_topics = 0
        total_core_topics = 0
        
        for topic_id, mastery in self.profile.topic_mastery.items():
            try:
                topic = Topic.objects.get(id=int(topic_id))
                if topic.is_core:
                    total_core_topics += 1
                    if mastery >= 0.8:
                        mastered_topics += 1
            except (ImportError, AttributeError, ValueError):
                continue
        
        # Ready to advance if 80% of core topics are mastered
        if total_core_topics > 0:
            return mastered_topics / total_core_topics >= 0.8
        
        return False
    
    def _find_next_learning_concept(self) -> Optional[str]:
        """
        Find the next concept to learn.
        """
        try:
            # Get all concepts with low mastery
            low_mastery_concepts = []
            for concept_id, mastery in self.profile.concept_mastery.items():
                if mastery < 0.3:  # Low or no mastery
                    low_mastery_concepts.append(concept_id)
            
            if not low_mastery_concepts:
                return None
            
            # Check prerequisites for each concept
            concepts = Concept.objects.filter(
                id__in=[int(cid) for cid in low_mastery_concepts if cid.isdigit()]
            )
            
            for concept in concepts:
                concept_id = str(concept.id)
                
                # Check if prerequisites are met
                prerequisites_met = True
                for prereq in concept.prerequisites.all():
                    prereq_mastery = self.profile.get_mastery_for_concept(str(prereq.id))
                    if prereq_mastery < 0.6:
                        prerequisites_met = False
                        break
                
                if prerequisites_met:
                    return concept_id
            
            # If no concept meets all prerequisites, find one with most prerequisites met
            best_concept = None
            best_ratio = 0
            
            for concept in concepts:
                concept_id = str(concept.id)
                prerequisites = concept.prerequisites.all()
                
                if prerequisites:
                    met_count = 0
                    for prereq in prerequisites:
                        if self.profile.get_mastery_for_concept(str(prereq.id)) >= 0.6:
                            met_count += 1
                    
                    ratio = met_count / len(prerequisites)
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_concept = concept_id
                else:
                    # No prerequisites - good candidate
                    return concept_id
            
            return best_concept
            
        except (ImportError, AttributeError, ValueError):
            # Fallback: use first weakness
            if self.profile.weaknesses:
                return self.profile.weaknesses[0]['concept_id']
            return None
    
    def _find_practice_concept(self) -> Optional[str]:
        """
        Find a concept suitable for practice (medium mastery).
        """
        for concept_id, mastery in self.profile.concept_mastery.items():
            if 0.4 <= mastery <= 0.7:
                return concept_id
        
        # If none found, use a weak concept
        if self.profile.weaknesses:
            return self.profile.weaknesses[0]['concept_id']
        
        return None
    
    def _action_learn(self, concept_id: str, priority: int = PRIORITY_MEDIUM) -> Dict:
        """Recommend learning a new concept."""
        concept_name = self._get_concept_name(concept_id)
        
        return {
            'action': self.ACTION_LEARN,
            'target': concept_id,
            'target_name': concept_name,
            'reason': f"Learn '{concept_name}' to build foundational knowledge",
            'priority': priority,
            'estimated_time': self._get_estimated_time(concept_id),
            'urgency': 'high' if priority >= 8 else 'medium',
            'action_details': {
                'type': 'content_viewing',
                'recommended_format': 'video_and_reading',
                'prerequisites': self._get_prerequisites(concept_id),
            }
        }
    
    def _action_remediate(self, concept_id: str, gap_score: float = 0, priority: int = PRIORITY_HIGH) -> Dict:
        """Recommend remediation for a weak concept."""
        concept_name = self._get_concept_name(concept_id)
        
        return {
            'action': self.ACTION_REMEDIATE,
            'target': concept_id,
            'target_name': concept_name,
            'reason': f"Remediate '{concept_name}' (mastery gap: {gap_score:.2f})",
            'priority': priority,
            'estimated_time': self._get_estimated_time(concept_id) * 1.5,
            'urgency': 'critical' if priority >= 9 else 'high',
            'action_details': {
                'type': 'focused_study',
                'recommended_format': 'tutorial_and_practice',
                'weakness_analysis': self._get_weakness_analysis(concept_id),
            }
        }
    
    def _action_practice(self, concept_id: str, priority: int = PRIORITY_MEDIUM) -> Dict:
        """Recommend practice to reinforce knowledge."""
        concept_name = self._get_concept_name(concept_id)
        
        return {
            'action': self.ACTION_PRACTICE,
            'target': concept_id,
            'target_name': concept_name,
            'reason': f"Practice '{concept_name}' to strengthen understanding",
            'priority': priority,
            'estimated_time': self._get_estimated_time(concept_id) * 0.7,
            'urgency': 'medium',
            'action_details': {
                'type': 'exercises',
                'recommended_format': 'quizzes_and_problems',
                'difficulty': 'current_level',
            }
        }
    
    def _action_reassess(self) -> Dict:
        """Recommend reassessment to update mastery data."""
        return {
            'action': self.ACTION_REASSESS,
            'target': None,
            'target_name': None,
            'reason': "Reassess to verify current mastery level",
            'priority': self.PRIORITY_LOW,
            'estimated_time': 10,
            'urgency': 'low',
            'action_details': {
                'type': 'assessment',
                'recommended_format': 'adaptive_quiz',
                'coverage': 'comprehensive',
            }
        }
    
    def _action_simulate(self, concept_id: str) -> Dict:
        """Recommend simulation to build practical skills."""
        concept_name = self._get_concept_name(concept_id)
        
        return {
            'action': self.ACTION_SIMULATE,
            'target': concept_id,
            'target_name': concept_name,
            'reason': f"Apply '{concept_name}' through hands-on simulation",
            'priority': self.PRIORITY_HIGH,
            'estimated_time': 20,
            'urgency': 'high',
            'action_details': {
                'type': 'simulation',
                'recommended_format': 'interactive_scenario',
                'focus': 'practical_application',
            }
        }
    
    def _action_build(self, concept_id: Optional[str] = None) -> Dict:
        """Recommend building a project."""
        return {
            'action': self.ACTION_BUILD,
            'target': concept_id,
            'target_name': self._get_concept_name(concept_id) if concept_id else None,
            'reason': "Build a project to demonstrate practical competency",
            'priority': self.PRIORITY_MEDIUM,
            'estimated_time': 60,
            'urgency': 'medium',
            'action_details': {
                'type': 'project',
                'recommended_format': 'guided_project',
                'deliverable': 'portfolio_item',
            }
        }
    
    def _action_challenge(self) -> Dict:
        """Recommend a challenge to push beyond current level."""
        return {
            'action': self.ACTION_CHALLENGE,
            'target': None,
            'target_name': None,
            'reason': "Challenge yourself with advanced content",
            'priority': self.PRIORITY_LOW,
            'estimated_time': 15,
            'urgency': 'low',
            'action_details': {
                'type': 'challenge',
                'recommended_format': 'advanced_problems',
                'difficulty': 'above_current_level',
            }
        }
    
    def _action_advance(self) -> Dict:
        """Recommend advancing to the next level."""
        return {
            'action': self.ACTION_ADVANCE,
            'target': None,
            'target_name': None,
            'reason': "You're ready to advance to the next level!",
            'priority': self.PRIORITY_HIGH,
            'estimated_time': 20,
            'urgency': 'high',
            'action_details': {
                'type': 'level_up',
                'recommended_format': 'progression_assessment',
                'next_level': self._get_next_level(),
            }
        }
    
    def _get_concept_name(self, concept_id: Optional[str]) -> str:
        """Get concept name from ID."""
        if not concept_id:
            return "new concept"
        
        try:
            concept = Concept.objects.get(id=int(concept_id))
            return concept.name
        except (Concept.DoesNotExist, ValueError):
            return f"concept {concept_id}"
    
    def _get_estimated_time(self, concept_id: Optional[str]) -> int:
        """Get estimated time for concept in minutes."""
        if not concept_id:
            return 15
        
        try:
            concept = Concept.objects.get(id=int(concept_id))
            return concept.difficulty * 3  # 3 minutes per difficulty level
        except (Concept.DoesNotExist, ValueError):
            return 15
    
    def _get_prerequisites(self, concept_id: str) -> List[str]:
        """Get prerequisites for a concept."""
        try:
            concept = Concept.objects.get(id=int(concept_id))
            return [str(p.id) for p in concept.prerequisites.all()]
        except (Concept.DoesNotExist, ValueError):
            return []
    
    def _get_weakness_analysis(self, concept_id: str) -> Dict:
        """Get weakness analysis for a concept."""
        for weakness in self.profile.weaknesses:
            if weakness['concept_id'] == concept_id:
                return {
                    'gap_score': weakness['gap_score'],
                    'attempt_count': weakness.get('attempt_count', 0),
                    'last_attempt': weakness.get('last_attempt'),
                }
        return {}
    
    def _get_next_level(self) -> str:
        """Get the next level for advancement."""
        current_level = self.profile.career_readiness_level
        levels = ['beginner', 'intermediate', 'advanced', 'expert']
        
        try:
            current_index = levels.index(current_level)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
        except ValueError:
            pass
        
        return 'intermediate'
