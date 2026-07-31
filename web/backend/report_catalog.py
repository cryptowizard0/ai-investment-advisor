"""Incremental in-memory catalog for local investment reports."""

from __future__ import annotations

import base64
import sqlite3
from pathlib import Path
from queue import Empty, Full, Queue
from threading import RLock
from typing import Literal, NotRequired, TypedDict

from web.backend.report_index import (
    ReportMetadata,
    collect_report_metadata,
    collect_report_metadata_for_path,
    duplicate_identity,
    report_relative_path,
)

class ReportItem(TypedDict):
    id: str
    category: str
    skill: str
    date: str
    title: str
    tickers: list[str]
    themes: list[str]
    dupeGroup: str
    isLatestInGroup: bool
    snippet: NotRequired[str]


class ReportEvent(TypedDict):
    type: Literal["added", "updated", "removed"]
    report: ReportItem


ReportSubscriber = Queue[ReportEvent | None]


def report_id(relative_path: str) -> str:
    encoded = base64.urlsafe_b64encode(relative_path.encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


class ReportEvents:
    def __init__(self) -> None:
        self._subscribers: set[ReportSubscriber] = set()
        self._lock = RLock()

    def subscribe(self) -> ReportSubscriber:
        subscriber: ReportSubscriber = Queue(maxsize=256)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: ReportSubscriber) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, event: ReportEvent) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(event)
            except Full:
                self.unsubscribe(subscriber)
                try:
                    while True:
                        subscriber.get_nowait()
                except Empty:
                    pass
                subscriber.put_nowait(None)


class ReportCatalog:
    def __init__(self, output_dir: Path, events: ReportEvents) -> None:
        self.output_dir = output_dir.resolve()
        self.events = events
        self._items_by_path: dict[str, ReportItem] = {}
        self._paths_by_id: dict[str, str] = {}
        self._loaded = False
        self._lock = RLock()
        self._search_index = sqlite3.connect(":memory:", check_same_thread=False)
        self._search_index.execute(
            "CREATE VIRTUAL TABLE report_search "
            "USING fts5(report_id UNINDEXED, body, tokenize='trigram')"
        )

    def load(self) -> None:
        with self._lock:
            if self._loaded:
                return
            for metadata in collect_report_metadata(self.output_dir):
                relative_path = str(metadata["relative_path"])
                item = self._build_item(metadata)
                self._items_by_path[relative_path] = item
                self._paths_by_id[item["id"]] = relative_path
                self._insert_search_row(
                    item["id"],
                    (self.output_dir / relative_path).read_text(encoding="utf-8"),
                )
            self._refresh_all_duplicate_groups()
            self._loaded = True

    def reports(self) -> list[ReportItem]:
        self.load()
        with self._lock:
            return sorted(
                (dict(item) for item in self._items_by_path.values()),
                key=lambda report: (
                    report["date"],
                    report["title"],
                    report["id"],
                ),
                reverse=True,
            )

    def path_for_id(self, requested_id: str) -> Path | None:
        self.load()
        with self._lock:
            relative_path = self._paths_by_id.get(requested_id)
        if relative_path is None:
            return None
        return self.output_dir / relative_path

    def search(self, query: str) -> list[tuple[str, str]]:
        self.load()
        literal_query = '"' + query.replace('"', '""') + '"'
        with self._lock:
            return self._search_index.execute(
                "SELECT report_id, "
                "snippet(report_search, 1, '<mark>', '</mark>', '…', 24) "
                "FROM report_search "
                "WHERE report_search MATCH ? "
                "ORDER BY bm25(report_search), rowid",
                (literal_query,),
            ).fetchall()

    def close(self) -> None:
        with self._lock:
            self._search_index.close()

    def rebuild_path(self, path: Path) -> ReportEvent | None:
        self.load()
        relative_path = report_relative_path(self.output_dir, path)
        if relative_path is None:
            return None

        with self._lock:
            previous = self._items_by_path.get(relative_path)
            try:
                metadata = collect_report_metadata_for_path(self.output_dir, path)
                body = path.read_text(encoding="utf-8") if metadata else None
            except (OSError, UnicodeDecodeError):
                return None

            if metadata is None:
                if previous is None:
                    return None
                self._delete_item(relative_path, previous)
                self._refresh_duplicate_group(previous["dupeGroup"])
                event: ReportEvent = {
                    "type": "removed",
                    "report": dict(previous),
                }
            else:
                if previous is not None:
                    self._delete_search_row(previous["id"])
                item = self._build_item(metadata)
                self._items_by_path[relative_path] = item
                self._paths_by_id[item["id"]] = relative_path
                self._insert_search_row(item["id"], body or "")
                self._refresh_duplicate_group(item["dupeGroup"])
                event = {
                    "type": "updated" if previous else "added",
                    "report": dict(self._items_by_path[relative_path]),
                }

        self.events.publish(event)
        return event

    def _build_item(self, metadata: ReportMetadata) -> ReportItem:
        relative_path = str(metadata["relative_path"])
        group, _ = duplicate_identity(relative_path)
        return {
            "id": report_id(relative_path),
            "category": str(metadata["category"]),
            "skill": str(metadata["skill"]),
            "date": str(metadata["date"]),
            "title": str(metadata["title"]),
            "tickers": list(metadata["tickers"]),
            "themes": list(metadata["themes"]),
            "dupeGroup": group,
            "isLatestInGroup": True,
        }

    def _delete_item(self, relative_path: str, item: ReportItem) -> None:
        del self._items_by_path[relative_path]
        self._paths_by_id.pop(item["id"], None)
        self._delete_search_row(item["id"])

    def _insert_search_row(self, item_id: str, body: str) -> None:
        self._search_index.execute(
            "INSERT INTO report_search (report_id, body) VALUES (?, ?)",
            (item_id, body),
        )

    def _delete_search_row(self, item_id: str) -> None:
        self._search_index.execute(
            "DELETE FROM report_search WHERE report_id = ?",
            (item_id,),
        )

    def _refresh_all_duplicate_groups(self) -> None:
        for group in {
            item["dupeGroup"] for item in self._items_by_path.values()
        }:
            self._refresh_duplicate_group(group)

    def _refresh_duplicate_group(self, group: str) -> None:
        group_items = [
            (relative_path, item)
            for relative_path, item in self._items_by_path.items()
            if item["dupeGroup"] == group
        ]
        if not group_items:
            return
        latest_version = max(
            duplicate_identity(relative_path)[1]
            for relative_path, _ in group_items
        )
        for relative_path, item in group_items:
            item["isLatestInGroup"] = (
                duplicate_identity(relative_path)[1] == latest_version
            )
