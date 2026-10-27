"""Rodar a triagem estatística a partir dos Parquets oficiais já baixados."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from observatorio.triagem_secoes import main
if __name__ == "__main__":
    main()
