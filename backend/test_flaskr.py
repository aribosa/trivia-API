import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app, QUESTIONS_PER_PAGE
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client()
        self.database_name = "trivia_test"
        self.client_user = os.environ.get('SQL_USER')
        self.client_password = os.environ.get('SQL_PASSWORD')
        self.database_path = "postgresql://{}:{}@{}/{}".format(
            self.client_user,
            self.client_password,
            'localhost:5432',
            self.database_name
        )
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        categories = self.client.get('/categories')

        self.assertTrue(categories.status_code == 200)
        self.assertTrue(categories.get_json()['success'])
        self.assertTrue(categories.get_json()['total_categories'] > 1)


    def test_get_questions(self):
        questions = self.client.get('/questions')
        questions_data = questions.get_json()

        self.assertTrue(questions.status_code == 200)
        self.assertTrue(questions_data['success'])
        self.assertTrue(len(questions_data['questions']) <= QUESTIONS_PER_PAGE)
        self.assertTrue(questions_data['total_pages'] >= 1)
        self.assertTrue(questions_data['current_page'] >= 1)

    def test_delete_question(self):
        new_question = Question('What is you name?', 'Falafel', 6, 4)
        self.app.db.session.add(new_question)
        self.app.db.session.commit()

        # Delete Question - Test Completed
        req = self.client.delete(f'/questions/{new_question.id}')
        self.assertTrue(req.status_code == 200)

        # Delete Question - Test Failed
        req = self.client.delete(f'/questions/2000000')
        self.assertTrue(req.status_code == 404)


    def test_search_question(self):
        req = self.client.post('/questions', json={'searchTerm': 'team'})

        self.assertTrue(req.status_code == 200)
        self.assertTrue(len(req.get_json(['questions'])) >= 1)


    def test_new_question(self):
        req = self.client.post('/questions', json={
            'question': 'Which is the new question?',
            'answer': 'This one!',
            'difficulty': 5,
            'category': 1
        })

        # Check the question was created
        self.assertTrue(req.status_code == 200)

        total_pages = req.get_json()['total_pages']
        req = self.client.get(f'/questions?page={total_pages}')
        question = req.get_json()['questions'][-1]
        self.assertTrue(question['question'] == 'Which is the new question?')


    def test_quizz(self):
        req = self.client.post('/quizzes', json={'previous_questions': [12, 5], 'quiz_category': 4})
        question = req.get_json()['question']

        self.assertTrue(req.status_code == 200)
        self.assertTrue(question)
        self.assertFalse(not question['id'] in [12, 5])
        self.assertTrue(question['category'] == 4)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()