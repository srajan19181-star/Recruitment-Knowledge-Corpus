import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.ingest import ingest_directory  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDFs into the RAG pipeline")
    parser.add_argument("--path", required=True, help="Directory containing PDF files")
    args = parser.parse_args()
    ingest_directory(args.path)
