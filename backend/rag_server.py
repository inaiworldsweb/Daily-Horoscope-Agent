"""
RAG Server - Python Flask API for answering questions using the RAG dataset
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add the current directory to the path to import agent module
sys.path.insert(0, os.path.dirname(__file__))

from agent import RAGEngine

app = Flask(__name__)
CORS(app)

# Initialize RAG Engine
rag_engine = RAGEngine()

@app.route('/api/rag/question', methods=['POST'])
def answer_question():
    """Answer a question using the RAG dataset"""
    try:
        data = request.json
        question = data.get('question', '')
        sign = data.get('sign', None)
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Use RAG engine to answer
        answer = rag_engine.answer_question(question, sign)
        
        return jsonify({
            'answer': answer,
            'question': question,
            'sign': sign
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/search', methods=['POST'])
def search_documents():
    """Search documents in the RAG dataset"""
    try:
        data = request.json
        query = data.get('query', '')
        sign = data.get('sign', None)
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Search documents
        results = rag_engine.search_documents(query, sign=sign, limit=limit)
        
        return jsonify({
            'results': results,
            'count': len(results),
            'query': query,
            'sign': sign
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rag/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'documents_loaded': len(rag_engine.rag_documents)
    })

if __name__ == '__main__':
    port = int(os.environ.get('RAG_PORT', 5001))
    print(f"Starting RAG Server on port {port}...")
    print(f"Loaded {len(rag_engine.rag_documents)} RAG documents")
    app.run(host='0.0.0.0', port=5001, debug=False)
