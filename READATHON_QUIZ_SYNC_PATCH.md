# E-Readathon Quiz Sync Patch

Added `/api/readathon/quiz-score/`.

This endpoint stores book quiz results in `StudentScore`, enabling:
- weak-topic detection
- student intelligence
- adaptive recommendations
- parent reports
- teacher insight
- gamification/leveling

Frontend should call:

```js
await apiRequest('/readathon/quiz-score/', {
  method: 'POST',
  data: {
    book_id: activeQuiz.id,
    book_title: activeQuiz.title,
    topic: activeQuiz.category || 'Reading Comprehension',
    score,
    total: 100,
    correct,
    question_count: questions.length,
    answers: quizAnswers,
  },
});
```
