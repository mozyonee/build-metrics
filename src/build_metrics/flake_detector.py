from __future__ import annotations

from collections import defaultdict

from build_metrics.store import Store


class FlakeDetector:
    def find(self, store: Store, repo: str) -> list[dict]:
        rows = store.conn.execute(
            """
            SELECT tr.name, tr.sha, tr.conclusion
            FROM test_results tr
            JOIN workflow_runs wr ON wr.id = tr.run_id
            WHERE wr.full_name = ?
            """,
            (repo,),
        ).fetchall()
        if not rows:
            raise LookupError("no test results")

        groups: dict[tuple[str, str], set[str]] = defaultdict(set)
        for row in rows:
            groups[(row["name"], row["sha"])].add(row["conclusion"])

        # LookupError when every test has only a single result overall
        # (no name/sha pair has two results recorded as separate rows with different outcomes possible)
        # Spec: "якщо жоден тест не має двох результатів, LookupError"
        counts: dict[tuple[str, str], int] = defaultdict(int)
        for row in rows:
            counts[(row["name"], row["sha"])] += 1
        if all(c < 2 for c in counts.values()):
            raise LookupError("single results only")

        flakes = []
        for (name, sha), conclusions in groups.items():
            if "pass" in conclusions and "fail" in conclusions:
                flakes.append({"name": name, "sha": sha, "results": sorted(conclusions)})
        return flakes
