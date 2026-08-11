from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from api.models import Assessment
from intelligence.models import ItemAttempt


class AssessmentSubmitTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.client.force_authenticate(self.user)

    def test_assessment_submit_creates_item_attempts(self):
        # create an assessment with two questions
        assessment = Assessment.objects.create(title='T1', questions=[
            {'id': '0', 'question': 'Q1', 'correct_answer': 'A'},
            {'id': '1', 'question': 'Q2', 'correct_answer': 'B'},
        ])

        url = f"/api/assessments/{assessment.id}/submit/"
        resp = self.client.post(url, {'answers': {'0': 'A', '1': 'C'}}, format='json')
        self.assertIn(resp.status_code, (200, 201))

        # check StudentScore created indirectly via API behavior
        attempts = ItemAttempt.objects.filter(user=self.user, assessment=assessment).order_by('question_index')
        self.assertEqual(attempts.count(), 2)
        self.assertEqual(attempts[0].score, 1.0)
        self.assertEqual(attempts[1].score, 0.0)
