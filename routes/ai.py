from flask import Blueprint, jsonify, request, session
from models.database import db, User
from functools import wraps
import requests
import os
from dotenv import load_dotenv

load_dotenv()

ai = Blueprint("ai", __name__)

conversation_cache = {}

def get_user_conversation(user_id):
    if user_id not in conversation_cache:
        conversation_cache[user_id] = []
    return conversation_cache[user_id]

def clear_user_conversation(user_id):
    if user_id in conversation_cache:
        conversation_cache[user_id] = []

# Login required decorator
def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Redirects to login page if user is not in session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")

@ai.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    try:
        user_id = session['user_id']
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400

        conversation = get_user_conversation(user_id)

        conversation.append({
            'role': 'user',
            'content': user_message
        })

        response = requests.post(
            OLLAMA_API_URL.replace('/api/generate', '/api/chat'),
            json={
                "model": MODEL_NAME,
                "messages": conversation,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 512,
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            },
            timeout=180
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('message', {}).get('content', '')

            conversation.append({
                'role': 'assistant',
                'content': ai_response
            })

            MAX_MESSAGES = 40
            if len(conversation) > MAX_MESSAGES:
                conversation_cache[user_id] = conversation[-MAX_MESSAGES:]

            return jsonify({
                'success': True,
                'response': ai_response
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Ollama API error: {response.status_code}'
            }), 500

    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timed out. The model is taking too long to respond. Try using a smaller model like llama3.2:1b'
        }), 504

    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Cannot connect to Ollama. Make sure Ollama is running (ollama serve)'
        }), 500

    except Exception as e:
        print(f"Error: {str(e)}")
        conversation = get_user_conversation(user_id)
        if conversation and conversation[-1]['role'] == 'user':
            conversation.pop()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ai.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    user_id = session['user_id']
    clear_user_conversation(user_id)
    return jsonify({
        'success': True,
        'message': 'Conversation cleared'
    })

@ai.route('/api/chat/history', methods=['GET'])
@login_required
def get_chat_history():
    user_id = session['user_id']
    return jsonify({
        'success': True,
        'history': get_user_conversation(user_id)
    })
