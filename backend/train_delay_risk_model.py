"""Entrypoint script for training delay-risk model."""

from pathlib import Path
import sys

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.training.train_delay_risk_model import train_and_export

if __name__ == "__main__":
    train_and_export()
