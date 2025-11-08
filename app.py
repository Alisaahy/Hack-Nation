"""
Research Discovery Agent - Flask Backend
Main application file with API endpoints
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.pdf_parser import extract_text_from_pdf
from agents.reader import ReaderAgent
from agents.searcher import SearcherAgent
from database import get_db, init_db
from models import Paper, Analysis, ResearchIdea, Reference

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='.')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/api/upload', methods=['POST'])
def upload_paper():
    """
    Upload a research paper PDF
    Returns: job_id for tracking the analysis
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400

        # Generate unique IDs
        paper_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())

        # Save file
        filename = secure_filename(file.filename)
        pdf_filename = f"{paper_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        file.save(filepath)

        # Get file size
        file_size = os.path.getsize(filepath)

        # Create database records
        db = get_db()
        try:
            # Create paper record
            paper = Paper(
                id=paper_id,
                pdf_filename=pdf_filename,
                pdf_size_bytes=file_size
            )
            db.add(paper)

            # Create analysis record
            analysis = Analysis(
                id=analysis_id,
                paper_id=paper_id,
                status='uploaded',
                progress=10
            )
            db.add(analysis)

            db.commit()

            return jsonify({
                'job_id': analysis_id,  # Use analysis_id as job_id
                'filename': filename,
                'message': 'File uploaded successfully'
            }), 200

        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_paper():
    """
    Start analysis of uploaded paper
    Expects: job_id (analysis_id), topics (array of topic strings)
    """
    job_id = None
    db = get_db()

    try:
        data = request.get_json()
        job_id = data.get('job_id')  # This is the analysis_id
        topics = data.get('topics', [])

        if not job_id:
            return jsonify({'error': 'job_id is required'}), 400

        # Get analysis record
        analysis = db.query(Analysis).filter_by(id=job_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404

        if not topics:
            return jsonify({'error': 'At least one topic must be selected'}), 400

        # Update analysis status
        analysis.selected_topics = topics
        analysis.status = 'parsing'
        analysis.progress = 20
        db.commit()

        # Step 1: Parse PDF
        paper = db.query(Paper).filter_by(id=analysis.paper_id).first()
        if not paper:
            raise Exception('Paper not found')

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], paper.pdf_filename)
        paper_text = extract_text_from_pdf(filepath)

        if not paper_text:
            analysis.status = 'error'
            analysis.error_message = 'Failed to extract text from PDF'
            db.commit()
            return jsonify({'error': 'Failed to extract text from PDF'}), 500

        # Update status to reading
        analysis.status = 'reading'
        analysis.progress = 30
        db.commit()

        # Step 2: Reader Agent
        reader = ReaderAgent()
        reader_results = reader.analyze_paper(paper_text, topics)

        # Store reader output
        analysis.reader_output = reader_results
        analysis.status = 'searching'
        analysis.progress = 50
        db.commit()

        # Step 3: Searcher Agent
        searcher = SearcherAgent()
        final_results = searcher.research_ideas(reader_results['ideas'], topics)

        # Store searcher output
        analysis.searcher_output = final_results

        # Create ResearchIdea records for top 3 ideas
        for rank, idea_data in enumerate(final_results['top_ideas'], 1):
            research_idea = ResearchIdea(
                analysis_id=analysis.id,
                rank=rank,
                title=idea_data.get('title', ''),
                description=idea_data.get('description', ''),
                rationale=idea_data.get('rationale', ''),
                novelty_score=idea_data.get('novelty_score'),
                doability_score=idea_data.get('doability_score'),
                topic_match_score=idea_data.get('topic_match_score'),
                composite_score=idea_data.get('composite_score'),
                novelty_assessment=idea_data.get('novelty_assessment', {}),
                doability_assessment=idea_data.get('doability_assessment', {}),
                literature_synthesis=idea_data.get('literature_synthesis', {})
            )
            db.add(research_idea)
            db.flush()  # Get the research_idea.id

            # Create Reference records for this idea
            for ref_data in idea_data.get('references', []):
                reference = Reference(
                    idea_id=research_idea.id,
                    title=ref_data.get('title', ''),
                    authors=ref_data.get('authors', []),
                    year=ref_data.get('year'),
                    venue=ref_data.get('venue', ''),
                    abstract=ref_data.get('abstract', ''),
                    url=ref_data.get('url', ''),
                    citation_count=ref_data.get('citationCount', 0),
                    relevance_category=ref_data.get('relevance_category', ''),
                    summary=ref_data.get('summary', '')
                )
                db.add(reference)

        # Mark analysis as complete
        analysis.status = 'complete'
        analysis.progress = 100
        analysis.completed_at = datetime.utcnow()
        db.commit()

        return jsonify({
            'job_id': job_id,
            'status': 'complete',
            'message': 'Analysis complete'
        }), 200

    except Exception as e:
        db.rollback()
        if job_id:
            try:
                analysis = db.query(Analysis).filter_by(id=job_id).first()
                if analysis:
                    analysis.status = 'error'
                    analysis.error_message = str(e)
                    db.commit()
            except:
                pass
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Get status of analysis job
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=job_id).first()

        if not analysis:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify({
            'job_id': job_id,
            'status': analysis.status,
            'progress': analysis.progress,
            'error': analysis.error_message
        }), 200

    finally:
        db.close()


@app.route('/api/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """
    Get final results for completed analysis
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=job_id).first()

        if not analysis:
            return jsonify({'error': 'Job not found'}), 404

        if analysis.status != 'complete':
            return jsonify({'error': 'Analysis not complete'}), 400

        # Get paper info
        paper = db.query(Paper).filter_by(id=analysis.paper_id).first()

        # Get top ideas from searcher_output (already stored)
        top_ideas = analysis.searcher_output.get('top_ideas', []) if analysis.searcher_output else []

        return jsonify({
            'job_id': job_id,
            'filename': paper.pdf_filename if paper else '',
            'paper_summary': analysis.reader_output.get('summary', '') if analysis.reader_output else '',
            'concepts': analysis.reader_output.get('concepts', []) if analysis.reader_output else [],
            'ideas': top_ideas
        }), 200

    finally:
        db.close()


@app.route('/api/papers', methods=['GET'])
def get_papers():
    """
    Get list of all uploaded papers with their analyses
    """
    db = get_db()
    try:
        papers = db.query(Paper).order_by(Paper.upload_timestamp.desc()).all()

        papers_list = []
        for paper in papers:
            paper_dict = paper.to_dict()
            # Add analysis count
            paper_dict['analysis_count'] = len(paper.analyses)
            papers_list.append(paper_dict)

        return jsonify({
            'papers': papers_list,
            'total': len(papers_list)
        }), 200

    finally:
        db.close()


@app.route('/api/analyses/<analysis_id>', methods=['GET'])
def get_analysis(analysis_id):
    """
    Get full details of a specific analysis including all research ideas and references
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()

        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404

        # Get paper info
        paper = db.query(Paper).filter_by(id=analysis.paper_id).first()

        # Get research ideas with references
        ideas_list = []
        ideas = db.query(ResearchIdea).filter_by(analysis_id=analysis_id).order_by(ResearchIdea.rank).all()

        for idea in ideas:
            idea_dict = idea.to_dict()

            # Get references for this idea
            references = db.query(Reference).filter_by(idea_id=idea.id).all()
            idea_dict['references'] = [ref.to_dict() for ref in references]

            ideas_list.append(idea_dict)

        return jsonify({
            'analysis': analysis.to_dict(),
            'paper': paper.to_dict() if paper else None,
            'ideas': ideas_list
        }), 200

    finally:
        db.close()


@app.route('/api/papers/<paper_id>/analyses', methods=['GET'])
def get_paper_analyses(paper_id):
    """
    Get all analyses for a specific paper
    """
    db = get_db()
    try:
        paper = db.query(Paper).filter_by(id=paper_id).first()

        if not paper:
            return jsonify({'error': 'Paper not found'}), 404

        analyses = db.query(Analysis).filter_by(paper_id=paper_id).order_by(Analysis.created_at.desc()).all()

        return jsonify({
            'paper': paper.to_dict(),
            'analyses': [analysis.to_dict() for analysis in analyses],
            'total': len(analyses)
        }), 200

    finally:
        db.close()


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    # Initialize database if needed
    init_db()

    # Run Flask app
    app.run(debug=True, port=5001)
