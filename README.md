# PyPI Dependency Graph

TL;DR `stars.csv` contains the "Top 1000"[^1] PyPI packages and their GitHub stars[^2].

Use the [PyPI APIs](https://warehouse.pypa.io/api-reference/) to generate a dependency graph.

Load graph:
```python
import networkx as nx

G = nx.read_gexf('2022-09-01_pypi.gexf')
```
----

### Notes:
- `2022-09-01_pypi.db.zst` is compressed with [Zstandard](https://github.com/facebook/zstd).
- If you decide to play with the code, decompress `2022-09-01_pypi.db.zst` and rename it to `pypy.db` to give yourself a starting point instead of scraping PyPI for hours.


### Todo:
- Automate this.
- Find some other interesting stats.

[^1]: Run PageRank on the graph.
[^2]: Scrape the project's metadata for GitHub URLs. Not all packages host on GitHub, and some don't link back to their GitHub repo.
