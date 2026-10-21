"""PDF Document Reconstructor — ponto de entrada.

Exemplos:
    python main.py documento.pdf
    python main.py --input ./input --output ./output
    python main.py documento.pdf --mode visual
"""
import sys

from app.main import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
