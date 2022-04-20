import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from math import ceil
from numpy.random import choice
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    cors = CORS(
        app,
        resources={
            r'/api/*': {'origins': '*'}
        }
    )

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,PUT,DELETE,OPTIONS')
        return response


    def get_paginated_results(results, req, number_of_records=QUESTIONS_PER_PAGE):
        page = req.args.get('page', default=1, type=int)
        start = (page - 1) * number_of_records
        end = start + number_of_records
        end = end if end <= len(results) else len(results)

        if start > len(results):
            return None

        else:
            return results[start:end]

    def get_random_question(questions, previous_questions):
        ids = [x['id'] for x in questions]

        if len(questions) == len(previous_questions):
            return None

        while True:
            random_id = choice(ids, 1)
            if not random_id in previous_questions:
                break

        return questions[random_id]


    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()

        if categories:
            return jsonify({
                'success': True,
                'categories': [cat.format() for cat in categories],
                'total_categories': len(categories)
            }), 200

        else:
            return jsonify({
                'success': False,
                'categories': [],
                'total_categories': None
            }), 400


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = Question.query.order_by(Question.id).all()
        categories = Category.query.all()

        page = request.args.get('page', default=1, type=int)

        results = get_paginated_results(questions, request, number_of_records=QUESTIONS_PER_PAGE)

        if results:
            return jsonify({
                'success': True,
                'questions': [q.format() for q in results],
                'current_page': page,
                'total_pages': ceil(len(questions) / QUESTIONS_PER_PAGE),
                'categories': [cat.format() for cat in categories]
            }), 200

        else:
            return jsonify({
                'success': False,
                'questions': [],
                'current_page': page,
                'total_pages': ceil(len(questions) / QUESTIONS_PER_PAGE)
            }), 204




    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)

        if question:
            try:
                question.delete()
                return jsonify({
                    'success': True,
                    'message': f'Question {question_id} deleted'
                }), 200

            except:
                app.db.rollback()

        return jsonify({'success': False}), 404


    @app.route('/questions', methods=['POST'])
    def post_questions():
        client_req = request.get_json()

        # If searchTearm is present, we are dealing with a search from the front end
        if client_req.get('searchTerm'):
            search = client_req.get('searchTerm')

            # Case Insensitive Search
            questions = Question.query.filter(Question.question.ilike(f'%{search}%')).all()
            if len(questions) > 0:
                return jsonify(
                    {
                        'success': True,
                        'questions': [question.format() for question in questions],
                        'total_questions': len(questions)
                    }), 200
            else:
                return jsonify({'success': False}), 404

        else:
            question = client_req.get('question')
            answer = client_req.get('answer')
            difficulty = client_req.get('difficulty')
            category = client_req.get('category')

            if question and answer and difficulty and category:
                try:
                    new_question = Question(question=question, answer=answer, difficulty=difficulty, category=int(category))
                    new_question.insert()
                    selection = Question.query.order_by(Question.id).all()
                    paginated = get_paginated_results(selection, request, QUESTIONS_PER_PAGE)
                    categories = Category.query.all()

                    return jsonify({
                        'success': True,
                        'questions': [q.format() for q in paginated],
                        'current_page': request.args.get('page', default=1, type=int),
                        'total_pages': ceil(len(selection) / QUESTIONS_PER_PAGE),
                        'categories': [cat.format() for cat in categories]
                    }), 200

                except:
                    return jsonify({'success': False}), 422

            else:
                return jsonify({
                    'success': False,
                    'message': 'The required argument were not provided'}), 422


    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def get_category_questions(category_id):
        cat = Category.query.get(category_id)
        questions = Question.query.filter_by(Question.category == category_id).all()
        paginated = get_paginated_results(questions, request)
        if cat and questions:
            return jsonify({
                'success': True,
                'questions': [q.format() for q in paginated],
                'total_questions': len(questions),
                'current_category': cat.type
            }), 200

        else:
            return jsonify({'success': False, 'message': 'Category not found'}), 404

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def next_question():
        body = request.get_json()
        prev_questions = body.get('previous_questions', [])
        category = body.get('quiz_category', 0)

        # Get questions for the given Category, or all categories if no category is given
        cat_questions = Question.query.all() if category == 0 else Question.query.filter_by(Question.category == category).all()
        random_question = get_random_question(cat_questions, prev_questions)  # Random question

        # Return success when no new possibilities exist (all questions used)
        try:
            if not random_question:
                return jsonify({'success': True})

            else:
                return jsonify({
                    'success': True,
                    'question': random_question.format()
                })

        except:
            abort(404)


    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(500)
    def system_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Server error"
        }), 500

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app

