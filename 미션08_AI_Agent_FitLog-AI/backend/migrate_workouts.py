"""Explicit, create-only copy. Default is read-only dry-run; never auto-run."""
import argparse

from backend.firebase import get_firestore_client
from backend.schemas.data import WorkoutInput
from backend.services.repository import DuplicateRecord, FirestoreRepository


def copy_workouts(source_rows, target, *, apply=False):
    # Validate ALL source documents before any write. Existing target wins.
    rows = []
    seen = set()
    for source in source_rows:
        body = WorkoutInput.model_validate({k: v for k, v in source.items() if k != "id"})
        if source["id"] != body.date or body.date in seen:
            raise ValueError("Inconsistent source dates")
        seen.add(body.date)
        # Validate with the shared schema, but copy original values verbatim.
        # Its input normalizer strips memo whitespace, which a migration must preserve.
        rows.append({key: source[key] for key in ("date", "value", "memo")})
    existing = {row["id"] for row in target.list()}
    result = {"dry_run": not apply, "source_count": len(rows), "would_create": 0,
              "created": 0, "skipped": 0}
    for row in rows:
        if row["date"] in existing:
            result["skipped"] += 1
        elif not apply:
            result["would_create"] += 1
        else:
            try:
                target.create(row["date"], row)
                result["created"] += 1
            except DuplicateRecord:
                # A concurrent writer may have created it after the initial read.
                result["skipped"] += 1
    return result


def main():
    parser = argparse.ArgumentParser(description="Copy workouts to data without overwriting; default dry-run.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Read only (default)")
    mode.add_argument("--apply", action="store_true", help="Explicitly create missing data documents")
    args = parser.parse_args()
    try:
        snapshots = get_firestore_client().collection("workouts").stream(timeout=30)
        rows = [{**d.to_dict(), "id": d.id} for d in snapshots]
        print(copy_workouts(rows, FirestoreRepository("data"), apply=args.apply))
    except Exception:
        print("Migration stopped. Check connectivity and document format. No existing documents are overwritten; a retry skips documents already copied.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
