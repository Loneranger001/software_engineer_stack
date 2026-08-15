#!/usr/bin/env python3
"""Jira story workflow utility for review-file validation and publish orchestration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

from _session import JIRA_URL, get_session
from write import (
    _resolve_issue_type,
    _resolve_project_key,
    _validate_parent_for_create,
    convert_markdown_to_adf,
)


STORY_HEADING_RE = re.compile(r"^## \[(STORY-\d+)\] (.+)$")
ALLOWED_FLAG_VALUES = {"Y", "N"}
REQUIRED_METADATA_ORDER = [
    "Epic",
    "Reviewed",
    "Created",
    "Jira Key",
    "Created Date",
    "Story Points",
    "Dependencies",
    "Labels",
]


@dataclass
class StoryBlock:
    story_id: str
    title: str
    heading_line_index: int
    metadata_line_indexes: dict[str, int]
    metadata: dict[str, str]
    body_lines: List[str]

    @property
    def clean_title(self) -> str:
        return self.title.strip()

    @property
    def description_markdown(self) -> str:
        return "\n".join(self.body_lines).strip()

    def is_reviewed(self) -> bool:
        return self.metadata["Reviewed"] == "Y"

    def is_created(self) -> bool:
        return self.metadata["Created"] == "Y" or bool(self.metadata["Jira Key"])


def parse_story_file(file_path: Path) -> List[StoryBlock]:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    story_indices = [index for index, line in enumerate(lines) if STORY_HEADING_RE.match(line)]
    if not story_indices:
        raise ValueError(f"No story headings found in {file_path}")

    stories: List[StoryBlock] = []
    for offset, start_index in enumerate(story_indices):
        end_index = story_indices[offset + 1] if offset + 1 < len(story_indices) else len(lines)
        heading_match = STORY_HEADING_RE.match(lines[start_index])
        assert heading_match is not None
        block_lines = lines[start_index:end_index]
        stories.append(parse_story_block(block_lines, start_index, file_path))
    return stories


def parse_story_block(block_lines: Sequence[str], start_index: int, file_path: Path) -> StoryBlock:
    heading_match = STORY_HEADING_RE.match(block_lines[0])
    if heading_match is None:
        raise ValueError(f"Invalid story heading at line {start_index + 1} in {file_path}")

    metadata: dict[str, str] = {}
    metadata_line_indexes: dict[str, int] = {}

    for relative_index, field_name in enumerate(REQUIRED_METADATA_ORDER, start=1):
        if relative_index >= len(block_lines):
            raise ValueError(
                f"Story {heading_match.group(1)} in {file_path} is missing metadata line '{field_name}:'"
            )
        raw_line = block_lines[relative_index]
        expected_prefix = f"{field_name}:"
        if not raw_line.startswith(expected_prefix):
            raise ValueError(
                f"Story {heading_match.group(1)} in {file_path} must define metadata in the exact order "
                f"{', '.join(REQUIRED_METADATA_ORDER)}"
            )
        metadata[field_name] = raw_line[len(expected_prefix):].strip()
        metadata_line_indexes[field_name] = start_index + relative_index

    blank_line_index = len(REQUIRED_METADATA_ORDER) + 1
    if blank_line_index >= len(block_lines) or block_lines[blank_line_index].strip() != "":
        raise ValueError(
            f"Story {heading_match.group(1)} in {file_path} must include a blank line after the Labels metadata"
        )

    validate_story_metadata(heading_match.group(1), metadata, file_path)

    return StoryBlock(
        story_id=heading_match.group(1),
        title=heading_match.group(2),
        heading_line_index=start_index,
        metadata_line_indexes=metadata_line_indexes,
        metadata=metadata,
        body_lines=list(block_lines[blank_line_index + 1 :]),
    )


def validate_story_metadata(story_id: str, metadata: dict[str, str], file_path: Path) -> None:
    for field_name in ("Reviewed", "Created"):
        value = metadata[field_name]
        if value not in ALLOWED_FLAG_VALUES:
            raise ValueError(f"Story {story_id} in {file_path} has invalid {field_name}: {value}. Expected Y or N.")

    if metadata["Created"] == "Y" and not metadata["Jira Key"]:
        raise ValueError(f"Story {story_id} in {file_path} is Created: Y but Jira Key is blank.")

    if metadata["Dependencies"] == "":
        raise ValueError(f"Story {story_id} in {file_path} must set Dependencies to None or a story list.")

    if metadata["Story Points"] == "":
        raise ValueError(f"Story {story_id} in {file_path} must include Story Points.")

    if metadata["Labels"] == "":
        raise ValueError(f"Story {story_id} in {file_path} must include Labels.")


def select_eligible_stories(stories: Sequence[StoryBlock]) -> List[StoryBlock]:
    return [story for story in stories if story.is_reviewed() and not story.is_created()]


def build_issue_payload(session, story: StoryBlock, epic_key: str, issue_type_name: str):
    project_key = _resolve_project_key(session, parent_key=epic_key)
    issue_type, _ = _resolve_issue_type(session, project_key, issue_type_name)
    _validate_parent_for_create(session, project_key, issue_type, epic_key)
    fields = {
        "project": {"key": project_key},
        "summary": story.clean_title,
        "description": convert_markdown_to_adf(story.description_markdown),
        "issuetype": {"id": issue_type["id"]},
        "parent": {"key": epic_key},
        "labels": [label.strip() for label in story.metadata["Labels"].split(",") if label.strip()],
    }
    return {"fields": fields}


def update_story_creation_metadata(file_path: Path, story: StoryBlock, jira_key: str) -> None:
    lines = file_path.read_text(encoding="utf-8").splitlines()
    lines[story.metadata_line_indexes["Created"]] = "Created: Y"
    lines[story.metadata_line_indexes["Jira Key"]] = f"Jira Key: {jira_key}"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines[story.metadata_line_indexes["Created Date"]] = f"Created Date: {timestamp}"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_selection_summary(stories: Sequence[StoryBlock], eligible_stories: Sequence[StoryBlock]) -> None:
    eligible_ids = {story.story_id for story in eligible_stories}
    print(f"Stories found: {len(stories)}")
    for story in stories:
        if story.story_id in eligible_ids:
            status = "eligible"
        elif story.metadata["Reviewed"] != "Y":
            status = "skipped: Reviewed != Y"
        else:
            status = "skipped: already created"
        print(f"- {story.story_id}: {story.clean_title} [{status}]")


def cmd_validate(args) -> int:
    file_path = Path(args.file).resolve()
    stories = parse_story_file(file_path)
    eligible_stories = select_eligible_stories(stories)
    print_selection_summary(stories, eligible_stories)
    if not eligible_stories:
        print("No eligible stories found. Nothing to validate.")
    return 0


def cmd_publish(args) -> int:
    file_path = Path(args.file).resolve()
    if args.epic == "[EPIC-PLACEHOLDER]":
        raise ValueError("Epic key cannot be [EPIC-PLACEHOLDER] for publish or dry-run.")

    stories = parse_story_file(file_path)
    eligible_stories = select_eligible_stories(stories)
    print_selection_summary(stories, eligible_stories)
    if not eligible_stories:
        print("No eligible stories found. Nothing to process.")
        return 0

    session = get_session()
    for story in eligible_stories:
        payload = build_issue_payload(session, story, args.epic, args.issue_type)
        print(f"\nStory: {story.story_id}")
        print(f"Summary: {story.clean_title}")
        if args.dry_run:
            print("Mode: dry-run")
            print(json.dumps(payload, indent=2, sort_keys=True))
            continue

        response = session.post(f"{JIRA_URL}/rest/api/3/issue", json=payload)
        if response.status_code not in (200, 201):
            print(
                f"FAIL: Could not create {story.story_id}: {response.status_code} {response.text[:500]}",
                file=sys.stderr,
            )
            return 1
        jira_key = response.json()["key"]
        print(f"Created: {jira_key}")
        update_story_creation_metadata(file_path, story, jira_key)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jira story review-file workflow utility")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate story-file structure and selection logic")
    validate_parser.add_argument("file", help="Path to jira-stories markdown file")

    publish_parser = sub.add_parser("publish", help="Dry-run or publish reviewed stories from a markdown file")
    publish_parser.add_argument("file", help="Path to jira-stories markdown file")
    publish_parser.add_argument("--epic", required=True, help="Epic key used as the parent for story creation")
    publish_parser.add_argument("--issue-type", default="Story", help="Jira issue type name")
    publish_parser.add_argument("--dry-run", action="store_true", help="Validate payloads without creating Jira issues")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "publish":
        return cmd_publish(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)