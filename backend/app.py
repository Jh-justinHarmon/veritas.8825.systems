"""
Veritas Flask API Server

Provides /api/synthesize endpoint for concept-driven answer synthesis.
Integrates retrieval system with synthesis agent.
"""

import json
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.exceptions import NotFound
from claims.runtime_status import LocalEvidenceAdapter, mediate_runtime_status
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict

# Load environment variables
load_dotenv()

# Import Veritas components
from agents.synthesis_agent import synthesize_answer
from retrieval.simple_retriever import retrieve_chunks, load_chunks
from ingestion.embed_chunks import generate_embedding
from history.history_store import HistoryStore
from abstraction.chunk_abstractor import abstract_chunks

STATIC_FOLDER = Path(__file__).parent.parent / "frontend" / "dist"
CLAIM_MANIFEST_PATH = Path(__file__).parent / "claims" / "runtime_status_manifest.json"
app = Flask(__name__, static_folder=None)
app.config["VERITAS_INTERNAL_CLAIMS_ENABLED"] = os.getenv("VERITAS_INTERNAL_CLAIMS", "") == "1"

# Initialize history store
history_store = HistoryStore()

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

# Handle narrow CORS preflight requests for the local frontend API surface.
@app.route('/api/synthesize', methods=['OPTIONS'])
@app.route('/api/synthesize/<mode>', methods=['OPTIONS'])
@app.route('/api/history', methods=['OPTIONS'])
@app.route('/api/history/<session_id>', methods=['OPTIONS'])
def handle_options(mode=None, session_id=None):
    return '', 204


@app.route('/api/claims/runtime-status', methods=['GET'])
def runtime_status_claim():
    """Serve the bundled runtime claim only when explicitly enabled on loopback."""
    loopback = request.remote_addr in {'127.0.0.1', '::1'}
    if not app.config.get("VERITAS_INTERNAL_CLAIMS_ENABLED") or not loopback:
        return jsonify({"error": "NOT_FOUND"}), 404
    try:
        claim = mediate_runtime_status(
            LocalEvidenceAdapter.from_bundled_manifest(CLAIM_MANIFEST_PATH)
        )
    except (OSError, ValueError):
        return jsonify({"error": "CLAIM_SOURCE_UNAVAILABLE"}), 503
    return jsonify(claim)


# Load embedded chunks on startup, validated against the approved source
# manifest. A corpus containing placeholder/unapproved material fails
# closed: synthesis is refused, health reports the corpus defect.
print("Loading embedded chunks...")
CORPUS_DIR = Path(__file__).parent.parent / "corpus"
CHUNKS_FILE = CORPUS_DIR / "embeddings" / "all_tiers_embedded_chunks.json"
CORPUS_MANIFEST_FILE = CORPUS_DIR / "embeddings" / "all_tiers_manifest.json"
SOURCE_MANIFEST_FILE = CORPUS_DIR / "source_manifest.json"

sys.path.insert(0, str(Path(__file__).parent / "ingestion"))
from source_policy import (
    chunk_is_production_safe,
    corpus_inventory_hash,
    load_source_manifest,
)  # noqa: E402

ALL_CHUNKS = load_chunks(CHUNKS_FILE)
CORPUS_MANIFEST = {}
CORPUS_CLEAN = False
CORPUS_DEFECT = None
try:
    CORPUS_MANIFEST = json.loads(CORPUS_MANIFEST_FILE.read_text(encoding="utf-8"))
    _source_manifest = load_source_manifest(SOURCE_MANIFEST_FILE)
    _unsafe = [c["chunk_id"] for c in ALL_CHUNKS
               if not chunk_is_production_safe(c, _source_manifest)]
    if _unsafe:
        CORPUS_DEFECT = f"{len(_unsafe)} chunks outside approved manifest"
    elif CORPUS_MANIFEST.get("manifest_sha256") != \
            corpus_inventory_hash(ALL_CHUNKS):
        CORPUS_DEFECT = "manifest hash mismatch with loaded chunks"
    else:
        CORPUS_CLEAN = True
except Exception as e:  # fail closed, detail sanitized at the edge
    CORPUS_DEFECT = f"corpus manifest validation failed: {type(e).__name__}"
print(f"Loaded {len(ALL_CHUNKS)} chunks; corpus_clean={CORPUS_CLEAN} defect={CORPUS_DEFECT}")

# Count chunks by tier
tier_counts = {}
for chunk in ALL_CHUNKS:
    tier = chunk.get('source_tier', 0)
    tier_counts[tier] = tier_counts.get(tier, 0) + 1
print(f"Tier breakdown: {tier_counts}")


def _corpus_binding() -> dict:
    return {
        "corpus_version": CORPUS_MANIFEST.get("corpus_version"),
        "manifest_sha256": CORPUS_MANIFEST.get("manifest_sha256"),
        "chunks_loaded": len(ALL_CHUNKS),
    }


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy" if CORPUS_CLEAN else "degraded",
        "chunks_loaded": len(ALL_CHUNKS),
        "service": "veritas-api",
        "corpus": {
            "version": CORPUS_MANIFEST.get("corpus_version"),
            "manifest_sha256": CORPUS_MANIFEST.get("manifest_sha256"),
            "clean": CORPUS_CLEAN,
        }
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
    
    # Validate question length
    if not CORPUS_CLEAN:
        return jsonify({
            "error": "CORPUS_UNCLEAN",
            "message": "Corpus failed manifest validation; synthesis refused"
        }), 503
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
        
        # Save to history with trace data
        trace = {
            "retrieved_chunks": [
                {
                    "source_name": chunk.get("source_name"),
                    "title": chunk.get("title"),
                    "tier": chunk.get("source_tier"),
                    "text_preview": chunk.get("text", "")[:100]
                }
                for chunk in retrieved_chunks
            ],
            "chunk_count": len(retrieved_chunks),
            "synthesis_model": answer.get("model", "gpt-4o"),
            "timestamp": answer.get("timestamp"),
            "corpus": _corpus_binding()
        }
        
        session_id = history_store.save_synthesis(
            question=question,
            answer={
                "ideas": answer["ideas"],
                "sources": answer["sources"]
            },
            trace=trace
        )
        
        # Return synthesized answer with session ID and corpus binding —
        # receipts downstream bind to the exact corpus build that
        # produced this answer.
        return jsonify({
            "session_id": session_id,
            "question": answer["question"],
            "ideas": answer["ideas"],
            "sources": answer["sources"],
            "corpus": _corpus_binding()
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


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get synthesis history (paginated)."""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    history = history_store.get_all_history(limit=limit, offset=offset)
    return jsonify(history)


@app.route('/api/history/<session_id>', methods=['GET'])
def get_history_by_id(session_id):
    """Get a specific history entry by ID."""
    entry = history_store.get_history_by_id(session_id)
    
    if entry is None:
        return jsonify({
            "error": "NOT_FOUND",
            "message": f"History entry {session_id} not found"
        }), 404
    
    return jsonify(entry)


@app.route('/api/history/<session_id>', methods=['DELETE'])
def delete_history(session_id):
    """Delete a history entry."""
    deleted = history_store.delete_history(session_id)
    
    if not deleted:
        return jsonify({
            "error": "NOT_FOUND",
            "message": f"History entry {session_id} not found"
        }), 404
    
    return jsonify({"success": True})


@app.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve built frontend assets for same-origin production topology."""
    return send_from_directory(STATIC_FOLDER / 'assets', filename)


@app.route('/')
def serve_frontend():
    """Serve the built frontend for same-origin production topology."""
    return send_from_directory(STATIC_FOLDER, 'index.html')


@app.route('/<path:path>')
def serve_frontend_path(path):
    """Serve frontend assets and fall back to the SPA for non-API routes."""
    if path.startswith('api/'):
        return jsonify({"error": "NOT_FOUND", "message": f"API route not found: /{path}"}), 404
    try:
        return send_from_directory(STATIC_FOLDER, path)
    except NotFound:
        return send_from_directory(STATIC_FOLDER, 'index.html')


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
    print(f"  - GET    /api/history")
    print(f"  - GET    /api/history/<id>")
    print(f"  - DELETE /api/history/<id>")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
