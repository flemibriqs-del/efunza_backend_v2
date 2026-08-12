from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Subject, Topic, Concept
from .services import KnowledgeGraphService

User = get_user_model()


class KnowledgeGraphModelTests(TestCase):
    """Test cases for knowledge graph models."""
    
    def setUp(self):
        self.subject = Subject.objects.create(
            name='Maritime',
            code='MAR',
            description='Maritime Studies',
            domain='maritime'
        )
        
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='Navigation',
            description='Navigation fundamentals',
            difficulty_level=3
        )
        
        self.concept = Concept.objects.create(
            topic=self.topic,
            name='Celestial Navigation',
            description='Navigation using celestial bodies',
            difficulty=4,
            is_core=True
        )
    
    def test_subject_creation(self):
        self.assertEqual(self.subject.name, 'Maritime')
        self.assertEqual(self.subject.domain, 'maritime')
    
    def test_topic_creation(self):
        self.assertEqual(self.topic.subject, self.subject)
        self.assertEqual(self.topic.difficulty_level, 3)
    
    def test_concept_creation(self):
        self.assertEqual(self.concept.topic, self.topic)
        self.assertEqual(self.concept.difficulty, 4)
        self.assertTrue(self.concept.is_core)
    
    def test_prerequisite_chain(self):
        concept2 = Concept.objects.create(
            topic=self.topic,
            name='GPS Navigation',
            description='GPS-based navigation',
            difficulty=2
        )
        concept2.prerequisites.add(self.concept)
        
        chain = concept2.get_prerequisites_chain()
        self.assertIn(self.concept, chain)
    
    def test_learning_path_service(self):
        path = KnowledgeGraphService.get_learning_path(self.subject.id)
        self.assertEqual(path['subject']['name'], 'Maritime')
        self.assertGreater(len(path['topics']), 0)


class KnowledgeGraphServiceTests(TestCase):
    """Test cases for knowledge graph services."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.subject = Subject.objects.create(
            name='Energy',
            code='ENR',
            description='Energy Studies',
            domain='energy'
        )
        
        self.topic = Topic.objects.create(
            subject=self.subject,
            name='Solar Power',
            description='Solar energy basics',
            difficulty_level=2
        )
        
        self.concept = Concept.objects.create(
            topic=self.topic,
            name='Solar Panels',
            description='Photovoltaic panels',
            difficulty=2,
            mastery_threshold=0.7
        )
    
    def test_get_concepts_with_mastery_no_user(self):
        concepts = Concept.objects.filter(topic=self.topic)
        result = KnowledgeGraphService.get_concepts_with_mastery(concepts)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Solar Panels')
        self.assertIsNone(result[0]['mastery'])
        self.assertEqual(result[0]['mastery_level'], 'Not started')
    
    def test_get_topics_with_progress_no_user(self):
        topics = Topic.objects.filter(subject=self.subject)
        result = KnowledgeGraphService.get_topics_with_progress(topics)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Solar Power')
        self.assertEqual(result[0]['progress'], 0)
        self.assertFalse(result[0]['is_completed'])
