"""
Knowledge Graph Services
Business logic for the knowledge graph operations
"""

from django.core.cache import cache
from django.db.models import Q, Count, Avg
from django.utils import timezone
from typing import List, Dict, Optional, Any
import logging

from .models import Subject, Topic, Concept

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """
    Service class for knowledge graph operations.
    """
    
    CACHE_KEY_PREFIX = 'kg_'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_learning_path(cls, subject_id: str, user=None) -> Dict[str, Any]:
        """
        Get the recommended learning path for a subject.
        
        Args:
            subject_id: UUID of the subject
            user: Optional user to personalize the path
        
        Returns:
            Dict with learning path structure
        """
        cache_key = f"{cls.CACHE_KEY_PREFIX}learning_path_{subject_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            subject = Subject.objects.get(id=subject_id)
            topics = subject.topics.filter(is_active=True).order_by('order')
            
            learning_path = {
                'subject': {
                    'id': str(subject.id),
                    'name': subject.name,
                    'description': subject.description,
                },
                'topics': []
            }
            
            for topic in topics:
                concepts = topic.concepts.filter(is_active=True).order_by('order')
                topic_data = {
                    'id': str(topic.id),
                    'name': topic.name,
                    'difficulty': topic.difficulty_level,
                    'concepts': []
                }
                
                for concept in concepts:
                    concept_data = {
                        'id': str(concept.id),
                        'name': concept.name,
                        'difficulty': concept.difficulty,
                        'is_core': concept.is_core,
                        'prerequisites': [str(p.id) for p in concept.prerequisites.all()],
                        'learning_objectives': concept.learning_objectives,
                    }
                    topic_data['concepts'].append(concept_data)
                
                learning_path['topics'].append(topic_data)
            
            # Cache the result
            cache.set(cache_key, learning_path, cls.CACHE_TIMEOUT)
            return learning_path
            
        except Subject.DoesNotExist:
            return {'error': 'Subject not found'}
    
    @classmethod
    def get_concepts_with_mastery(cls, concepts, user=None) -> List[Dict]:
        """
        Get concepts with mastery data for a user.
        
        Args:
            concepts: QuerySet of Concept objects
            user: User instance to get mastery data for
        
        Returns:
            List of concept data with mastery information
        """
        concept_data = []
        
        for concept in concepts:
            data = {
                'id': str(concept.id),
                'name': concept.name,
                'difficulty': concept.difficulty,
                'is_core': concept.is_core,
                'prerequisite_count': concept.prerequisites.count(),
                'mastery': None,
                'mastery_level': 'Not started',
                'has_evidence': False,
            }
            
            if user and hasattr(user, 'intelligence_profile'):
                mastery = user.intelligence_profile.get_mastery_for_concept(str(concept.id))
                if mastery > 0:
                    data['mastery'] = mastery
                    if mastery >= concept.mastery_threshold:
                        data['mastery_level'] = 'Mastered'
                    elif mastery >= concept.mastery_threshold * 0.7:
                        data['mastery_level'] = 'Proficient'
                    elif mastery >= concept.mastery_threshold * 0.4:
                        data['mastery_level'] = 'Developing'
                    else:
                        data['mastery_level'] = 'Needs Improvement'
            
            concept_data.append(data)
        
        return concept_data
    
    @classmethod
    def get_topics_with_progress(cls, topics, user=None) -> List[Dict]:
        """
        Get topics with progress data.
        
        Args:
            topics: QuerySet of Topic objects
            user: User instance to get progress data for
        
        Returns:
            List of topic data with progress information
        """
        topic_data = []
        
        for topic in topics:
            concepts = topic.concepts.filter(is_active=True)
            total_concepts = concepts.count()
            mastered_concepts = 0
            
            if user and hasattr(user, 'intelligence_profile'):
                for concept in concepts:
                    mastery = user.intelligence_profile.get_mastery_for_concept(str(concept.id))
                    if mastery >= concept.mastery_threshold:
                        mastered_concepts += 1
            
            progress = (mastered_concepts / total_concepts * 100) if total_concepts > 0 else 0
            
            data = {
                'id': str(topic.id),
                'name': topic.name,
                'difficulty': topic.difficulty_level,
                'total_concepts': total_concepts,
                'mastered_concepts': mastered_concepts,
                'progress': round(progress, 2),
                'is_completed': progress >= 100,
                'prerequisites': [str(p.id) for p in topic.prerequisites.all()],
            }
            
            topic_data.append(data)
        
        return topic_data
    
    @classmethod
    def get_skills_for_topic(cls, topic_id: str) -> List[Dict]:
        """
        Get all skills required for a topic.
        
        Args:
            topic_id: UUID of the topic
        
        Returns:
            List of skills with descriptions
        """
        from skills.models import Skill  # Assuming you'll create a skills app
        
        try:
            topic = Topic.objects.get(id=topic_id)
            concepts = topic.concepts.filter(is_active=True)
            skills = Skill.objects.filter(concepts__in=concepts).distinct()
            
            return list(skills.values('id', 'name', 'description', 'level'))
            
        except Topic.DoesNotExist:
            return []
    
    @classmethod
    def get_prerequisite_chain(cls, concept_id: str) -> List[Dict]:
        """
        Get the full prerequisite chain for a concept.
        
        Args:
            concept_id: UUID of the concept
        
        Returns:
            List of concepts in prerequisite order
        """
        try:
            concept = Concept.objects.get(id=concept_id)
            prerequisites = concept.get_prerequisites_chain()
            
            return [
                {
                    'id': str(p.id),
                    'name': p.name,
                    'difficulty': p.difficulty,
                    'topic_name': p.topic.name,
                }
                for p in prerequisites
            ]
            
        except Concept.DoesNotExist:
            return []
    
    @classmethod
    def suggest_learning_path(cls, user, subject_id: str) -> Dict:
        """
        Suggest a personalized learning path based on user's mastery.
        
        Args:
            user: User instance
            subject_id: UUID of the subject
        
        Returns:
            Dict with recommended path
        """
        try:
            subject = Subject.objects.get(id=subject_id)
            topics = subject.topics.filter(is_active=True).order_by('order')
            
            suggested_path = {
                'subject': subject.name,
                'topics': [],
                'recommended_start': None,
                'weakness_area': None,
            }
            
            for topic in topics:
                concepts = topic.concepts.filter(is_active=True).order_by('order')
                topic_status = {
                    'topic_id': str(topic.id),
                    'topic_name': topic.name,
                    'concepts': [],
                    'readiness': 'ready'
                }
                
                for concept in concepts:
                    mastery = user.intelligence_profile.get_mastery_for_concept(str(concept.id))
                    concept_status = {
                        'concept_id': str(concept.id),
                        'concept_name': concept.name,
                        'mastery': mastery,
                        'threshold': concept.mastery_threshold,
                        'status': 'mastered' if mastery >= concept.mastery_threshold else 'needs_work'
                    }
                    topic_status['concepts'].append(concept_status)
                
                suggested_path['topics'].append(topic_status)
            
            return suggested_path
            
        except Subject.DoesNotExist:
            return {'error': 'Subject not found'}
    
    @classmethod
    def preload_cache(cls):
        """
        Preload commonly accessed data into cache.
        """
        try:
            subjects = Subject.objects.filter(is_active=True)
            for subject in subjects:
                cls.get_learning_path(subject.id)
            logger.info("Knowledge graph cache preloaded successfully")
        except Exception as e:
            logger.error(f"Error preloading knowledge graph cache: {str(e)}")
