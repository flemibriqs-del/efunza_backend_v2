"""
Mastery Engine
Calculates concept/topic mastery from:
- Assessment history
- Difficulty levels
- Consistency of performance
- Recency of activity
- Practical evidence
- Competency evidence
"""

from django.db import models
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import logging
import math
from datetime import timedelta

from .base_engine import BaseEngine
from intelligence.models import StudentIntelligenceProfile
from evidence.models import CompetencyEvidence
from knowledge_graph.models import Concept, Topic, Subject

User = get_user_model()
logger = logging.getLogger(__name__)


class MasteryEngine(BaseEngine):
    """
    Engine for calculating and updating mastery scores.
    """
    
    # Configuration constants
    MIN_ATTEMPTS_FOR_MASTERY = 3
    MASTERY_THRESHOLD = 0.7
    DECAY_HALF_LIFE = 30  # days
    EVIDENCE_BOOST_MAX = 0.15
    CONSISTENCY_THRESHOLD = 0.7
    
    def __init__(self, profile: StudentIntelligenceProfile):
        """
        Initialize the Mastery Engine with a student profile.
        
        Args:
            profile: StudentIntelligenceProfile instance
        """
        self.profile = profile
        self.user = profile.user
        self._cache_key = f"mastery_{profile.id}"
    
    def calculate_concept_mastery(
        self, 
        concept_id: str, 
        force_refresh: bool = False
    ) -> float:
        """
        Calculate mastery for a specific concept.
        
        Args:
            concept_id: UUID of the concept
            force_refresh: Force recalculation instead of using cache
        
        Returns:
            Mastery score between 0 and 1
        """
        # Check cache
        cache_key = f"concept_mastery_{concept_id}_{self.profile.id}"
        if not force_refresh:
            cached = self.get_cached(cache_key)
            if cached is not None:
                return cached
        
        # Get all attempts for this concept
        attempts = self._get_concept_attempts(concept_id)
        
        if not attempts:
            return 0.0
        
        # Calculate individual components
        base_score = self._calculate_base_score(attempts)
        difficulty_adjusted = self._adjust_for_difficulty(base_score, attempts)
        recency_adjusted = self._apply_recency_decay(difficulty_adjusted, attempts)
        consistency_boost = self._calculate_consistency_boost(attempts)
        
        # Get evidence boost
        evidence_boost = self._get_evidence_boost(concept_id)
        
        # Combine all factors
        mastery = recency_adjusted + consistency_boost + evidence_boost
        
        # Apply final normalization
        mastery = self.normalize_score(mastery, 0.0, 1.0)
        
        # Cache the result
        self.set_cached(cache_key, mastery, timeout=3600)
        
        return mastery
    
    def calculate_topic_mastery(self, topic_id: str) -> float:
        """
        Calculate mastery for a topic (aggregate of concepts).
        
        Args:
            topic_id: UUID of the topic
        
        Returns:
            Mastery score between 0 and 1
        """
        # Get all concepts in this topic
        try:
            topic = Topic.objects.get(id=topic_id)
            concepts = topic.concepts.filter(is_active=True)
            
            if not concepts:
                return 0.0
            
            # Calculate mastery for each concept
            concept_masteries = []
            weights = []
            
            for concept in concepts:
                mastery = self.calculate_concept_mastery(str(concept.id))
                if mastery > 0:
                    # Weight core concepts more heavily
                    weight = 1.5 if concept.is_core else 1.0
                    concept_masteries.append(mastery)
                    weights.append(weight)
            
            if not concept_masteries:
                return 0.0
            
            # Calculate weighted average
            topic_mastery = self.weighted_average(concept_masteries, weights)
            
            return self.normalize_score(topic_mastery)
            
        except Topic.DoesNotExist:
            return 0.0
    
    def calculate_subject_mastery(self, subject_id: str) -> float:
        """
        Calculate mastery for a subject (aggregate of topics).
        
        Args:
            subject_id: UUID of the subject
        
        Returns:
            Mastery score between 0 and 1
        """
        try:
            subject = Subject.objects.get(id=subject_id)
            topics = subject.topics.filter(is_active=True)
            
            if not topics:
                return 0.0
            
            # Calculate mastery for each topic
            topic_masteries = []
            weights = []
            
            for topic in topics:
                mastery = self.calculate_topic_mastery(str(topic.id))
                if mastery > 0:
                    # Weight by difficulty
                    weight = 1 + (topic.difficulty_level - 1) * 0.1
                    topic_masteries.append(mastery)
                    weights.append(weight)
            
            if not topic_masteries:
                return 0.0
            
            subject_mastery = self.weighted_average(topic_masteries, weights)
            
            return self.normalize_score(subject_mastery)
            
        except Subject.DoesNotExist:
            return 0.0
    
    def update_all_mastery(self) -> Dict[str, Any]:
        """
        Update all mastery scores in the profile.
        
        Returns:
            Dict with updated mastery data
        """
        logger.info(f"Updating all mastery for user {self.user.id}")
        
        # Get all concepts the user has interacted with
        concept_ids = self._get_interacted_concepts()
        
        # Calculate mastery for each concept
        concept_mastery_updates = {}
        for concept_id in concept_ids:
            mastery = self.calculate_concept_mastery(concept_id, force_refresh=True)
            concept_mastery_updates[concept_id] = mastery
        
        # Update profile
        self.profile.concept_mastery = concept_mastery_updates
        
        # Update topic mastery (aggregate of concepts in topic)
        self._update_topic_mastery()
        
        # Update subject mastery (aggregate of topics in subject)
        self._update_subject_mastery()
        
        # Update weaknesses
        self._update_weaknesses()
        
        # Update growth rate
        self._update_growth_rate()
        
        # Save the profile
        self.profile.save()
        
        # Invalidate cache
        self.invalidate_cache()
        
        result = {
            'concepts_updated': len(concept_mastery_updates),
            'topics_updated': len(self.profile.topic_mastery),
            'subjects_updated': len(self.profile.subject_mastery),
            'weaknesses_found': len(self.profile.weaknesses),
            'timestamp': timezone.now().isoformat(),
        }
        
        logger.info(f"Mastery update complete: {result}")
        
        return result
    
    def get_mastery_status(self, concept_id: str) -> Dict[str, Any]:
        """
        Get detailed mastery status for a concept.
        
        Args:
            concept_id: UUID of the concept
        
        Returns:
            Dict with detailed mastery information
        """
        mastery = self.calculate_concept_mastery(concept_id)
        attempts = self._get_concept_attempts(concept_id)
        
        # Determine status
        if mastery >= self.MASTERY_THRESHOLD:
            status = 'mastered'
        elif mastery >= self.MASTERY_THRESHOLD * 0.6:
            status = 'proficient'
        elif mastery >= self.MASTERY_THRESHOLD * 0.3:
            status = 'developing'
        elif mastery > 0:
            status = 'beginner'
        else:
            status = 'not_started'
        
        return {
            'concept_id': concept_id,
            'mastery': mastery,
            'status': status,
            'attempt_count': len(attempts),
            'average_score': self._calculate_base_score(attempts) * 100,
            'consistency': self._calculate_consistency_boost(attempts),
            'last_attempt': attempts[0].get('created_at') if attempts else None,
            'needs_remediation': mastery < self.MASTERY_THRESHOLD * 0.5,
            'threshold': self.MASTERY_THRESHOLD,
        }
    
    def _get_concept_attempts(self, concept_id: str) -> List[Dict]:
        """
        Get all attempts for a concept.
        """
        # This should be implemented based on your learning models
        # For now, we'll try to get from ItemAttempt or similar
        try:
            from learning.models import ItemAttempt
            attempts = ItemAttempt.objects.filter(
                user=self.user,
                concept_id=concept_id
            ).order_by('-created_at').values(
                'id', 'score', 'created_at', 'question_difficulty'
            )
            return list(attempts)
        except (ImportError, AttributeError):
            # Fallback: try to get from the profile's historical data
            return self.profile.concept_mastery_history.get(concept_id, {}).get('attempts', [])
    
    def _get_interacted_concepts(self) -> List[str]:
        """
        Get all concepts the user has interacted with.
        """
        try:
            from learning.models import ItemAttempt
            concept_ids = ItemAttempt.objects.filter(
                user=self.user
            ).values_list('concept_id', flat=True).distinct()
            return [str(cid) for cid in concept_ids if cid]
        except (ImportError, AttributeError):
            # Fallback: use profile data
            return list(self.profile.concept_mastery.keys())
    
    def _calculate_base_score(self, attempts: List[Dict]) -> float:
        """
        Calculate base score from attempt performance.
        """
        if not attempts:
            return 0.0
        
        scores = [a.get('score', 0) for a in attempts]
        avg_score = sum(scores) / len(scores)
        return avg_score / 100.0  # Normalize to 0-1
    
    def _adjust_for_difficulty(self, base_score: float, attempts: List[Dict]) -> float:
        """
        Adjust base score for difficulty of attempted items.
        Higher difficulty items contribute more to mastery.
        """
        if not attempts:
            return base_score
        
        # Calculate average difficulty
        difficulties = [a.get('question_difficulty', 3) for a in attempts]
        avg_difficulty = sum(difficulties) / len(difficulties)
        
        # Normalize difficulty factor (1-10 scale)
        difficulty_factor = 1 + (avg_difficulty - 5) / 10
        
        # Apply adjustment
        adjusted = base_score * difficulty_factor
        
        return self.normalize_score(adjusted)
    
    def _apply_recency_decay(self, score: float, attempts: List[Dict]) -> float:
        """
        Apply decay based on how recent attempts are.
        """
        if not attempts:
            return score
        
        now = timezone.now()
        recent_attempts = attempts[:5]  # Consider last 5 attempts
        
        # Calculate weighted score with recency weighting
        total_weight = 0
        weighted_score = 0
        
        for attempt in recent_attempts:
            created_at = attempt.get('created_at')
            if not created_at:
                continue
            
            # Calculate days since attempt
            days_since = (now - created_at).days
            
            # Exponential decay weight
            weight = math.exp(-days_since / self.DECAY_HALF_LIFE)
            
            attempt_score = attempt.get('score', 0) / 100.0
            
            weighted_score += attempt_score * weight
            total_weight += weight
        
        if total_weight > 0:
            recency_score = weighted_score / total_weight
        else:
            recency_score = score
        
        # Apply decay if no recent activity (last attempt > 7 days)
        if attempts:
            last_attempt = attempts[0]
            last_date = last_attempt.get('created_at')
            if last_date:
                days_since_last = (now - last_date).days
                if days_since_last > 7:
                    decay_factor = math.exp(-days_since_last / 60)
                    recency_score *= decay_factor
        
        return self.normalize_score(recency_score)
    
    def _calculate_consistency_boost(self, attempts: List[Dict]) -> float:
        """
        Calculate consistency boost for performance.
        """
        if len(attempts) < 2:
            return 0.0
        
        scores = [a.get('score', 0) for a in attempts[:10]]
        if not scores:
            return 0.0
        
        consistency = self.calculate_consistency(scores)
        
        # Boost based on consistency
        if consistency >= self.CONSISTENCY_THRESHOLD:
            boost = (consistency - self.CONSISTENCY_THRESHOLD) * 0.15
            return min(boost, 0.1)
        
        return 0.0
    
    def _get_evidence_boost(self, concept_id: str) -> float:
        """
        Get boost from practical evidence for this concept.
        """
        try:
            # Get evidence related to this concept
            evidence = CompetencyEvidence.objects.filter(
                user=self.user,
                activity_type__in=['simulation', 'practical', 'project'],
                competencies_demonstrated__contains=[{'concept_id': concept_id}]
            )
            
            if not evidence:
                return 0.0
            
            # Calculate average performance in practical activities
            avg_performance = evidence.aggregate(
                Avg('performance_score')
            )['performance_score__avg']
            
            if avg_performance:
                # Boost based on performance
                boost = (avg_performance / 100.0) * self.EVIDENCE_BOOST_MAX
                return min(boost, self.EVIDENCE_BOOST_MAX)
            
            return 0.0
            
        except (ImportError, AttributeError):
            # Evidence app not installed yet
            return 0.0
    
    def _update_topic_mastery(self):
        """
        Aggregate concept mastery to topic level.
        """
        topic_mastery = {}
        
        # Get all concepts in the profile
        concept_ids = [int(cid) for cid in self.profile.concept_mastery.keys() if cid.isdigit()]
        
        if not concept_ids:
            return
        
        try:
            # Group concepts by topic
            concepts = Concept.objects.filter(
                id__in=concept_ids
            ).select_related('topic')
            
            topic_concepts = {}
            for concept in concepts:
                topic_id = str(concept.topic.id)
                if topic_id not in topic_concepts:
                    topic_concepts[topic_id] = []
                
                mastery = self.profile.concept_mastery.get(str(concept.id), 0)
                weight = 1.5 if concept.is_core else 1.0
                topic_concepts[topic_id].append((mastery, weight))
            
            # Calculate weighted average for each topic
            for topic_id, concept_data in topic_concepts.items():
                if concept_data:
                    masteries = [d[0] for d in concept_data]
                    weights = [d[1] for d in concept_data]
                    topic_mastery[topic_id] = self.weighted_average(masteries, weights)
            
            self.profile.topic_mastery = topic_mastery
            
        except (ImportError, AttributeError):
            # Knowledge graph not installed yet
            pass
    
    def _update_subject_mastery(self):
        """
        Aggregate topic mastery to subject level.
        """
        subject_mastery = {}
        
        # Get all topics in the profile
        topic_ids = [int(tid) for tid in self.profile.topic_mastery.keys() if tid.isdigit()]
        
        if not topic_ids:
            return
        
        try:
            # Group topics by subject
            topics = Topic.objects.filter(
                id__in=topic_ids
            ).select_related('subject')
            
            subject_topics = {}
            for topic in topics:
                subject_id = str(topic.subject.id)
                if subject_id not in subject_topics:
                    subject_topics[subject_id] = []
                
                mastery = self.profile.topic_mastery.get(str(topic.id), 0)
                weight = 1 + (topic.difficulty_level - 1) * 0.1
                subject_topics[subject_id].append((mastery, weight))
            
            # Calculate weighted average for each subject
            for subject_id, topic_data in subject_topics.items():
                if topic_data:
                    masteries = [d[0] for d in topic_data]
                    weights = [d[1] for d in topic_data]
                    subject_mastery[subject_id] = self.weighted_average(masteries, weights)
            
            self.profile.subject_mastery = subject_mastery
            
        except (ImportError, AttributeError):
            # Knowledge graph not installed yet
            pass
    
    def _update_weaknesses(self):
        """
        Identify weaknesses based on mastery scores.
        """
        weaknesses = []
        
        for concept_id, mastery in self.profile.concept_mastery.items():
            # A concept is a weakness if mastery is below threshold
            if mastery < self.MASTERY_THRESHOLD and mastery > 0:
                gap_score = self.MASTERY_THRESHOLD - mastery
                priority = int(gap_score * 10)  # 1-10 scale
                
                # Check if this concept has been practiced recently
                attempts = self._get_concept_attempts(concept_id)
                recent_attempt = attempts[0].get('created_at') if attempts else None
                
                weakness = {
                    'concept_id': concept_id,
                    'gap_score': gap_score,
                    'priority': min(priority, 10),
                    'identified_at': timezone.now().isoformat(),
                    'last_attempt': recent_attempt.isoformat() if recent_attempt else None,
                    'attempt_count': len(attempts),
                }
                weaknesses.append(weakness)
        
        # Sort by priority (highest first)
        weaknesses.sort(key=lambda x: x['priority'], reverse=True)
        
        # Keep top 20 weaknesses
        self.profile.weaknesses = weaknesses[:20]
    
    def _update_growth_rate(self):
        """
        Calculate knowledge growth rate.
        """
        # Get historical mastery data if available
        historical_data = self.get_cached(f"history_{self.profile.id}")
        
        if not historical_data:
            # Store current state for future comparison
            self.set_cached(
                f"history_{self.profile.id}",
                {
                    'timestamp': timezone.now().isoformat(),
                    'mastery': self.profile.concept_mastery.copy()
                },
                timeout=2592000  # 30 days
            )
            self.profile.knowledge_growth_rate = 0.0
            return
        
        # Calculate growth rate
        prev_mastery = historical_data.get('mastery', {})
        current_mastery = self.profile.concept_mastery
        
        # Calculate average improvement
        improvements = []
        for concept_id, current in current_mastery.items():
            prev = prev_mastery.get(concept_id, 0)
            if prev > 0:
                improvement = (current - prev) / prev
                improvements.append(improvement)
        
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            self.profile.knowledge_growth_rate = avg_improvement * 100  # Percentage
        else:
            self.profile.knowledge_growth_rate = 0.0
        
        # Update historical data
        self.set_cached(
            f"history_{self.profile.id}",
            {
                'timestamp': timezone.now().isoformat(),
                'mastery': current_mastery.copy()
            },
            timeout=2592000  # 30 days
        )
    
    def get_mastery_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive mastery analytics.
        
        Returns:
            Dict with analytics data
        """
        analytics = {
            'user_id': str(self.user.id),
            'mastery_summary': {
                'total_concepts': len(self.profile.concept_mastery),
                'average_mastery': 0,
                'mastered_concepts': 0,
                'weak_concepts': 0,
                'growth_rate': self.profile.knowledge_growth_rate,
            },
            'by_difficulty': {},
            'by_domain': {},
            'recent_progress': [],
            'recommendations': [],
        }
        
        # Calculate summary statistics
        if self.profile.concept_mastery:
            masteries = list(self.profile.concept_mastery.values())
            analytics['mastery_summary']['average_mastery'] = sum(masteries) / len(masteries)
            analytics['mastery_summary']['mastered_concepts'] = len([
                m for m in masteries if m >= self.MASTERY_THRESHOLD
            ])
            analytics['mastery_summary']['weak_concepts'] = len([
                m for m in masteries if m < self.MASTERY_THRESHOLD * 0.5
            ])
        
        # Group by difficulty
        try:
            concept_ids = [int(cid) for cid in self.profile.concept_mastery.keys() if cid.isdigit()]
            concepts = Concept.objects.filter(id__in=concept_ids)
            
            for concept in concepts:
                difficulty = concept.difficulty
                mastery = self.profile.concept_mastery.get(str(concept.id), 0)
                
                if difficulty not in analytics['by_difficulty']:
                    analytics['by_difficulty'][difficulty] = []
                analytics['by_difficulty'][difficulty].append(mastery)
            
            # Calculate averages by difficulty
            for difficulty, masteries in analytics['by_difficulty'].items():
                analytics['by_difficulty'][difficulty] = sum(masteries) / len(masteries)
                
        except (ImportError, AttributeError, ValueError):
            pass
        
        # Add recommendations
        analytics['recommendations'] = self._generate_recommendations()
        
        return analytics
    
    def _generate_recommendations(self) -> List[Dict]:
        """
        Generate learning recommendations based on mastery data.
        """
        recommendations = []
        
        # 1. Weak concepts that need remediation
        for weakness in self.profile.weaknesses[:5]:
            concept_id = weakness['concept_id']
            gap = weakness['gap_score']
            
            recommendations.append({
                'type': 'remediation',
                'concept_id': concept_id,
                'priority': weakness['priority'],
                'reason': f"Mastery gap of {gap:.2f} needs attention",
                'action': 'Study and practice this concept',
                'estimated_time': 15 + (weakness['priority'] * 5),  # minutes
            })
        
        # 2. Concepts ready for advancement
        for concept_id, mastery in self.profile.concept_mastery.items():
            if mastery >= self.MASTERY_THRESHOLD * 1.1:  # Exceeded threshold
                try:
                    concept = Concept.objects.get(id=int(concept_id))
                    next_concepts = concept.get_recommended_next_concepts()
                    
                    for next_concept in next_concepts[:2]:
                        recommendations.append({
                            'type': 'advancement',
                            'concept_id': str(next_concept.id),
                            'concept_name': next_concept.name,
                            'priority': 8,
                            'reason': f"Ready to advance from {concept.name}",
                            'action': 'Start learning the next concept',
                            'estimated_time': 20,
                        })
                except (ImportError, AttributeError, ValueError):
                    pass
        
        # 3. Practice recommendations
        for concept_id, mastery in self.profile.concept_mastery.items():
            if 0.4 <= mastery < 0.7:  # Medium mastery - ideal for practice
                recommendations.append({
                    'type': 'practice',
                    'concept_id': concept_id,
                    'priority': 5,
                    'reason': f"Current mastery is {mastery:.2f} - practice to improve",
                    'action': 'Practice exercises for this concept',
                    'estimated_time': 10,
                })
                break  # Only one practice recommendation
        
        return recommendations[:10]  # Limit to 10 recommendations
