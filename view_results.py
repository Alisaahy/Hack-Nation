"""
View Results from Database
Simple script to query and display analysis results
"""

from database import get_db
from models import Paper, Analysis, ResearchIdea, Reference
import json

def view_all_papers():
    """List all papers in database"""
    db = get_db()
    try:
        papers = db.query(Paper).all()
        print(f"\n{'='*60}")
        print(f"Total Papers: {len(papers)}")
        print(f"{'='*60}\n")

        for paper in papers:
            print(f"ID: {paper.id}")
            print(f"File: {paper.pdf_filename}")
            print(f"Uploaded: {paper.upload_timestamp}")
            print(f"Analyses: {len(paper.analyses)}")
            print("-" * 60)
    finally:
        db.close()


def view_all_analyses():
    """List all analyses"""
    db = get_db()
    try:
        analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
        print(f"\n{'='*60}")
        print(f"Total Analyses: {len(analyses)}")
        print(f"{'='*60}\n")

        for analysis in analyses:
            print(f"ID: {analysis.id}")
            print(f"Status: {analysis.status}")
            print(f"Progress: {analysis.progress}%")
            print(f"Topics: {', '.join(analysis.selected_topics) if analysis.selected_topics else 'None'}")
            print(f"Created: {analysis.created_at}")
            if analysis.status == 'complete':
                print(f"Ideas generated: {len(analysis.ideas)}")
            print("-" * 60)
    finally:
        db.close()


def view_analysis_details(analysis_id):
    """View detailed results for a specific analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()

        if not analysis:
            print(f"Analysis {analysis_id} not found")
            return

        print(f"\n{'='*60}")
        print(f"Analysis: {analysis.id}")
        print(f"{'='*60}\n")

        print(f"Status: {analysis.status}")
        print(f"Topics: {', '.join(analysis.selected_topics) if analysis.selected_topics else 'None'}")

        if analysis.reader_output:
            print(f"\nPaper Summary:")
            print(f"{analysis.reader_output.get('summary', 'N/A')}")

            concepts = analysis.reader_output.get('concepts', [])
            if concepts:
                print(f"\nKey Concepts: {', '.join(concepts[:5])}")

        # Research ideas
        ideas = db.query(ResearchIdea).filter_by(analysis_id=analysis_id).order_by(ResearchIdea.rank).all()

        print(f"\n{'='*60}")
        print(f"Research Ideas ({len(ideas)})")
        print(f"{'='*60}\n")

        for idea in ideas:
            print(f"#{idea.rank}: {idea.title}")
            print(f"  Description: {idea.description}")
            print(f"  Scores - Novelty: {idea.novelty_score}, Doability: {idea.doability_score}, "
                  f"Topic Match: {idea.topic_match_score}")
            print(f"  Composite: {idea.composite_score}")

            # References
            references = db.query(Reference).filter_by(idea_id=idea.id).all()
            print(f"  References: {len(references)}")
            print()

    finally:
        db.close()


def export_analysis_to_json(analysis_id, output_file=None):
    """Export analysis results to JSON file"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()

        if not analysis:
            print(f"Analysis {analysis_id} not found")
            return

        # Build complete result object
        result = analysis.to_dict()

        # Add paper info
        paper = db.query(Paper).filter_by(id=analysis.paper_id).first()
        result['paper'] = paper.to_dict() if paper else None

        # Add ideas with references
        ideas = db.query(ResearchIdea).filter_by(analysis_id=analysis_id).order_by(ResearchIdea.rank).all()
        result['ideas'] = []

        for idea in ideas:
            idea_dict = idea.to_dict()
            references = db.query(Reference).filter_by(idea_id=idea.id).all()
            idea_dict['references'] = [ref.to_dict() for ref in references]
            result['ideas'].append(idea_dict)

        # Save to file
        if not output_file:
            output_file = f"results/analysis_{analysis_id}.json"

        import os
        os.makedirs('results', exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"Analysis exported to: {output_file}")

    finally:
        db.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python view_results.py papers              # List all papers")
        print("  python view_results.py analyses            # List all analyses")
        print("  python view_results.py view <analysis_id>  # View analysis details")
        print("  python view_results.py export <analysis_id> [output_file]  # Export to JSON")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'papers':
        view_all_papers()
    elif command == 'analyses':
        view_all_analyses()
    elif command == 'view':
        if len(sys.argv) < 3:
            print("Error: analysis_id required")
            sys.exit(1)
        view_analysis_details(sys.argv[2])
    elif command == 'export':
        if len(sys.argv) < 3:
            print("Error: analysis_id required")
            sys.exit(1)
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        export_analysis_to_json(sys.argv[2], output_file)
    else:
        print(f"Unknown command: {command}")
