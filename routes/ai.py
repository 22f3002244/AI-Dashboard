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
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b")  # Optimized for your 16GB RAM
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))  # 2 minutes for 8b model

@ai.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    user_id = session['user_id']
    conversation = get_user_conversation(user_id)
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400

        # Add user message to conversation
        conversation.append({
            'role': 'user',
            'content': user_message
        })

        # Construct the correct API URL
        chat_url = OLLAMA_API_URL.replace('/api/generate', '/api/chat')
        
        # System prompt for IoT dashboard context
        messages = conversation.copy()
        if len(messages) == 1:  # First message in conversation
            messages.insert(0, {
                'role': 'system',
                'content': 'You are an expert AI assistant specialized in IoT dashboard design and development. You help users create modern, responsive IoT dashboards with focus on: data visualization (charts, graphs, real-time metrics), IoT device management, sensor data monitoring, user interface design, and best practices for dashboard architecture. Provide practical, actionable, and technical advice. Be concise but thorough.'
            })

        response = requests.post(
            chat_url,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,       # Balanced creativity
                    "num_predict": 1024,      # Longer responses for detailed explanations
                    "top_k": 40,
                    "top_p": 0.9,
                    "num_ctx": 8192,          # Large context window for technical discussions
                    "repeat_penalty": 1.1,    # Avoid repetition
                    "num_thread": 10          # Use all 10 CPU cores
                }
            },
            timeout=OLLAMA_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('message', {}).get('content', '')

            # Only add assistant response if we got valid content
            if ai_response:
                conversation.append({
                    'role': 'assistant',
                    'content': ai_response
                })

                # Trim conversation to prevent memory issues
                # Keep last 24 messages (12 exchanges) - good balance for IoT context
                MAX_MESSAGES = 24
                if len(conversation) > MAX_MESSAGES:
                    conversation_cache[user_id] = conversation[-MAX_MESSAGES:]

                return jsonify({
                    'success': True,
                    'response': ai_response,
                    'model': MODEL_NAME
                })
            else:
                # No valid response received, remove user message
                if conversation and conversation[-1]['role'] == 'user':
                    conversation.pop()
                return jsonify({
                    'success': False,
                    'error': 'Empty response from AI model'
                }), 500
        else:
            # API returned error status, remove user message
            if conversation and conversation[-1]['role'] == 'user':
                conversation.pop()
            return jsonify({
                'success': False,
                'error': f'Ollama API error: {response.status_code}'
            }), 500

    except requests.exceptions.Timeout:
        # Clean up conversation on timeout
        if conversation and conversation[-1]['role'] == 'user':
            conversation.pop()
        return jsonify({
            'success': False,
            'error': f'Request timed out after {OLLAMA_TIMEOUT} seconds. The model might be busy. Please try again.'
        }), 504

    except requests.exceptions.ConnectionError:
        # Clean up conversation on connection error
        if conversation and conversation[-1]['role'] == 'user':
            conversation.pop()
        return jsonify({
            'success': False,
            'error': 'Cannot connect to Ollama. Make sure Ollama is running with: ollama serve'
        }), 500

    except Exception as e:
        # Clean up conversation on any other error
        print(f"Error: {str(e)}")
        if conversation and conversation[-1]['role'] == 'user':
            conversation.pop()
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
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

@ai.route('/api/chat/model', methods=['GET'])
@login_required
def get_model_info():
    """Get current model information"""
    return jsonify({
        'success': True,
        'model': MODEL_NAME,
        'timeout': OLLAMA_TIMEOUT,
        'max_context': 8192
    })