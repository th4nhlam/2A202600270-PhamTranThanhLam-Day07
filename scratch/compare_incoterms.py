from src.chunking import ChunkingStrategyComparator
from pathlib import Path

text = Path("docs/incoterms_any_mode_rules.md").read_text()
comp = ChunkingStrategyComparator()
results = comp.compare(text, chunk_size=200)

for name, stats in results.items():
    print(f"{name}: count={stats['count']}, avg={stats['avg_length']:.1f}")
