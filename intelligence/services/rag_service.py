"""
RAG Service
Learner-aware RAG that uses the learner's profile for context-aware retrieval
"""

from django.core.cache import cache
from django.db import models
from typing import List, Dict, Any, Optional
import logging
import json

from intelligence.models import StudentIntelligenceProfile
from knowledge_graph.models import Concept, Topic

logger = logging.getLogger(__name__)


class RAGService:
    """
    Learner-aware RAG service that personalizes content retrieval
    based on the learner's level, mastery, weaknesses, goals, and context.
    """
    
    def __init__(self, user, profile: Optional[StudentIntelligenceProfile] = None):
        """
        Initialize the RAG service.
        
        Args:
            user: The user instance
            profile: Optional profile (will fetch if not provided)
        """
        self.user = user
        self.profile = profile or StudentIntelligenceProfile.objects.get(user=user)
    
    def retrieve_content(
        self,
        query: str,
        context: Optional[Dict] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve content personalized for the learner.
        
        Args:
            query: The search query
            context: Additional context (current concept, topic, etc.)
            max_results: Maximum number of results to return
        
        Returns:
            List of content items with relevance scores
        """
        logger.info(f"Retrieving content for user {self.user.id}: {query[:50]}...")
        
        # Step 1: Analyze query and get base results
        base_results = self._get_base_results(query, max_results * 2)
        
        # Step 2: Personalize based on learner profile
        personalized_results = self._personalize_results(
            base_results, 
            self.profile,
            context
        )
        
        # Step 3: Rank and filter results
        ranked_results = self._rank_results(personalized_results)
        
        # Step 4: Add learning context to results
        enhanced_results = self._enhance_with_context(ranked_results)
        
        return enhanced_results[:max_results]
    
    def _get_base_results(self, query: str, limit: int) -> List[Dict]:
        """
        Get base content results from the knowledge base.
        This would connect to your vector database (pgvector, Pinecone, etc.)
        """
        # Placeholder: This should connect to your actual RAG system
        # For now, we'll simulate with concept search
        
        try:
            # Search concepts by name/description
            concepts = Concept.objects.filter(
                models.Q(name__icontains=query) |
                models.Q(description__icontains=query)
            )[:limit]
            
            results = []
            for concept in concepts:
                results.append({
                    'id': str(concept.id),
                    'type': 'concept',
                    'title': concept.name,
                    'description': concept.description,
                    'difficulty': concept.difficulty,
                    'topic': concept.topic.name,
                    'topic_id': str(concept.topic.id),
                    'prerequisites': [str(p.id) for p in concept.prerequisites.all()],
                    'mastery_required': concept.mastery_threshold,
                    'base_score': 0.5,  # Placeholder similarity score
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in base retrieval: {str(e)}")
            return []
    
    def _personalize_results(
        self,
        results: List[Dict],
        profile: StudentIntelligenceProfile,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Personalize results based on learner profile.
        """
        personalized = []
        
        for result in results:
            concept_id = result.get('id')
            
            # 1. Adjust based on mastery
            mastery = profile.get_mastery_for_concept(concept_id)
            if mastery >= 0.7:
                # Already mastered - lower priority for learning
                result['personalization_score'] = 0.3
                result['personalization_reason'] = 'Already mastered'
            elif mastery >= 0.3:
                # Developing - good for practice
                result['personalization_score'] = 0.8
                result['personalization_reason'] = 'Developing - practice recommended'
            else:
                # Beginner - good for learning
                result['personalization_score'] = 1.0
                result['personalization_reason'] = 'New - learning recommended'
            
            # 2. Adjust based on weaknesses
            is_weakness = any(
                w.get('concept_id') == concept_id 
                for w in profile.weaknesses
            )
            if is_weakness:
                result['personalization_score'] *= 1.3
                result['personalization_reason'] = 'Weakness - prioritize'
            
            # 3. Adjust based on prerequisites
            prerequisites = result.get('prerequisites', [])
            if prerequisites:
                prerequisites_met = all(
                    profile.get_mastery_for_concept(prereq) >= 0.6
                    for prereq in prerequisites
                )
                if not prerequisites_met:
                    result['personalization_score'] *= 0.5
                    result['personalization_reason'] = 'Prerequisites not met'
            
            # 4. Adjust based on goals
            if profile.learning_goals:
                # Check if concept aligns with goals
                # This would need more sophisticated matching
                result['personalization_score'] *= 1.1
            
            # 5. Adjust based on engagement
            engagement_factor = profile.engagement_score
            result['personalization_score'] *= (0.5 + engagement_factor * 0.5)
            
            # Normalize score
            result['personalization_score'] = min(1.0, result['personalization_score'])
            
            personalized.append(result)
        
        return personalized
    
    def _rank_results(self, results: List[Dict]) -> List[Dict]:
        """
        Rank results by relevance and personalization.
        """
        # Sort by personalization score
        results.sort(key=lambda x: x.get('personalization_score', 0), reverse=True)
        
        # Add ranking metadata
        for i, result in enumerate(results):
            result['rank'] = i + 1
            result['relevance_score'] = result.get('base_score', 0) * result.get('personalization_score', 0.5)
        
        return results
    
    def _enhance_with_context(self, results: List[Dict]) -> List[Dict]:
        """
        Enhance results with additional context.
        """
        enhanced = []
        
        for result in results:
            # Add domain context
            try:
                if result.get('concept_id'):
                    concept = Concept.objects.get(id=result.get('concept_id'))
                    result['domain'] = concept.topic.subject.domain
                    result['subject'] = concept.topic.subject.name
            except:
                pass
            
            # Add suggested learning path
            if result.get('prerequisites'):
                result['suggested_path'] = {
                    'prerequisites': result['prerequisites'],
                    'next_steps': self._get_next_steps(result),
                }
            
            # Add difficulty context
            difficulty = result.get('difficulty', 3)
            result['difficulty_label'] = self._get_difficulty_label(difficulty)
            
            enhanced.append(result)
        
        return enhanced
    
    def _get_next_steps(self, result: Dict) -> List[str]:
        """
        Get next steps for a concept.
        """
        try:
            concept = Concept.objects.get(id=result.get('id'))
            next_concepts = concept.get_recommended_next_concepts()
            return [str(c.id) for c in next_concepts[:3]]
        except:
            return []
    
    def _get_difficulty_label(self, difficulty: int) -> str:
        """Get difficulty label."""
        labels = {
            1: 'Beginner',
            2: 'Elementary',
            3: 'Intermediate',
            4: 'Upper Intermediate',
            5: 'Advanced',
            6: 'Expert',
            7: 'Master',
            8: 'Genius',
            9: 'Legendary',
            10: 'Mythical',
        }
        return labels.get(difficulty, 'Unknown')
    
    def get_personalized_context(self) -> Dict[str, Any]:
        """
        Get personalized context for the learner.
        """
        context = {
            'profile': {
                'level': self._determine_level(),
                'mastery_summary': self._get_mastery_summary(),
                'weaknesses': self.profile.weaknesses[:5],
                'goals': self.profile.learning_goals,
                'engagement': self.profile.engagement_score,
            },
            'recommended_focus': self._get_recommended_focus(),
            'learning_style': self.profile.preferred_learning_styles,
        }
        
        return context
    
    def _determine_level(self) -> str:
        """Determine the learner's overall level."""
        if not self.profile.concept_mastery:
            return 'beginner'
        
        average = sum(self.profile.concept_mastery.values()) / len(self.profile.concept_mastery)
        
        if average >= 0.8:
            return 'advanced'
        elif average >= 0.6:
            return 'intermediate'
        elif average >= 0.3:
            return 'developing'
        else:
            return 'beginner'
    
    def _get_mastery_summary(self) -> Dict:
        """Get mastery summary."""
        if not self.profile.concept_mastery:
            return {'total': 0, 'average': 0}
        
        masteries = list(self.profile.concept_mastery.values())
        return {
            'total': len(masteries),
            'average': sum(masteries) / len(masteries),
            'mastered': len([m for m in masteries if m >= 0.7]),
        }
    
    def _get_recommended_focus(self) -> List[str]:
        """Get recommended focus areas."""
        if not self.profile.weaknesses:
            return []
        
        return [w['concept_id'] for w in self.profile.weaknesses[:3]]
