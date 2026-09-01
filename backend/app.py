"""
Veritas Flask API Server

Provides /api/synthesize endpoint for concept-driven answer synthesis.
Integrates retrieval system with synthesis agent.
"""

import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict

# Load environment variables
load_dotenv()

# Import Veritas components
from agents.synthesis_agent import synthesize_answer
from retrieval.simple_retriever import retrieve_chunks, load_chunks
from ingestion.embed_chunks import generate_embedding
from abstraction.chunk_abstractor import abstract_chunks

app = Flask(__name__)

# Manual CORS headers (more reliable than flask-cors)
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin in ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:5175']:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Max-Age'] = '3600'
    return response

# Load embedded chunks on startup
CHUNKS_FILE = Path(__file__).parent.parent / "corpus" / "embeddings" / "all_tiers_embedded_chunks.json"
if CHUNKS_FILE.exists():
    ALL_CHUNKS = load_chunks(CHUNKS_FILE)
    print(f"Loaded {len(ALL_CHUNKS)} chunks")
else:
    ALL_CHUNKS = []
    print("Demo corpus not bundled in this hiring release")

# Count chunks by tier
tier_counts = {}
for chunk in ALL_CHUNKS:
    tier = chunk.get('source_tier', 0)
    tier_counts[tier] = tier_counts.get(tier, 0) + 1
print(f"Tier breakdown: {tier_counts}")


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "chunks_loaded": len(ALL_CHUNKS),
        "service": "veritas-api"
    })


@app.route('/api/synthesize', methods=['POST', 'OPTIONS'])
@app.route('/api/synthesize/<mode>', methods=['POST', 'OPTIONS'])
def synthesize(mode=None):
    """
    Synthesize concept-driven answer from question.
    
    Request body:
    {
        "question": "string (5-500 chars)"
    }
    
    Response:
    {
        "question": "string",
        "ideas": [
            {
                "title": "string",
                "paragraphs": ["string"],
                "sourceIds": ["string"]
            }
        ],
        "sources": {
            "id": "string"
        }
    }
    """
    # Validate request
    if not request.json or 'question' not in request.json:
        return jsonify({
            "error": "INVALID_REQUEST",
            "message": "Request must include 'question' field"
        }), 400
    
    question = request.json['question']

    if not ALL_CHUNKS:
        return jsonify({
            "error": "DEMO_CORPUS_NOT_INCLUDED",
            "message": "The hiring release omits corpus data; use the verified live demo."
        }), 503
    
    # Validate question length
    if len(question) < 5 or len(question) > 500:
        return jsonify({
            "error": "INVALID_REQUEST",
            "message": "Question must be between 5 and 500 characters"
        }), 400
    
    try:
        # Step 1: Generate query embedding
        print(f"Generating embedding for: {question}")
        query_embedding = generate_embedding(question)
        
        # Step 2: Retrieve relevant chunks
        print(f"Retrieving chunks...")
        retrieved_chunks = retrieve_chunks(
            query_embedding=query_embedding,
            all_chunks=ALL_CHUNKS,
            top_k=10  # Retrieve more chunks for better synthesis
        )
        print(f"Retrieved {len(retrieved_chunks)} chunks")
        
        # Step 2.5: Apply abstraction if mode is 'abstracted'
        if mode == 'abstracted':
            print(f"Applying abstraction to chunks...")
            retrieved_chunks = abstract_chunks(retrieved_chunks)
            print(f"Abstraction complete")
        
        # Step 3: Synthesize answer
        print(f"Synthesizing answer (mode: {mode or 'raw'})...")
        answer = synthesize_answer(
            question=question,
            retrieved_chunks=retrieved_chunks,
            model="gpt-4o"
        )
        
        # Check for synthesis errors
        if "error" in answer:
            return jsonify({
                "error": "SYNTHESIS_FAILED",
                "message": answer["error"]
            }), 500
        
        print(f"Synthesis complete: {len(answer.get('ideas', []))} ideas generated")
        
        # Return the synthesized answer without persisting user questions or traces.
        return jsonify({
            "question": answer["question"],
            "ideas": answer["ideas"],
            "sources": answer["sources"]
        })
        
    except FileNotFoundError as e:
        return jsonify({
            "error": "CORPUS_NOT_FOUND",
            "message": f"Embedded chunks file not found: {e}"
        }), 500
    except Exception as e:
        print(f"Error during synthesis: {e}")
        return jsonify({
            "error": "SYNTHESIS_FAILED",
            "message": f"Failed to synthesize answer: {str(e)}"
        }), 500


@app.route('/api/examples', methods=['GET'])
def examples():
    """Return example questions for testing."""
    return jsonify([
        {
            "id": "tool-use-errors",
            "question": "Why is Claude calling the wrong tool or using incorrect parameters?",
            "description": "Tool selection, schema design, parameter specification"
        },
        {
            "id": "streaming-tool-use",
            "question": "How do I stream tool use responses in Claude?",
            "description": "Event protocol, JSON accumulation, execution gating"
        },
        {
            "id": "vision-capabilities",
            "question": "What can Claude Vision analyze in images?",
            "description": "Image understanding, OCR, visual reasoning"
        }
    ])


if __name__ == '__main__':
    # Development server
    print("\n" + "="*60)
    print("Veritas API Server")
    print("="*60)
    print(f"Chunks loaded: {len(ALL_CHUNKS)}")
    print(f"Endpoints:")
    print(f"  - GET    /api/health")
    print(f"  - GET    /api/examples")
    print(f"  - POST   /api/synthesize")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
