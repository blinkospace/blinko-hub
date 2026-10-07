import base64
import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("validate_pr", Path(__file__).with_name("validate_pr.py"))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

VALID_YAML = '''title: "Alice's Notes"
url: "https://notes.example.com"
tags: [english, blog]
created_at: "2026-10-07"
'''


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.pr = {
            "state": "open",
            "draft": False,
            "base": {"ref": "main"},
            "head": {"sha": "abc123", "repo": {"full_name": "alice/blinko-hub"}},
            "changed_files": 1,
        }
        self.file = {"filename": "sites/alice.yml", "status": "added", "sha": "blob123"}
        self.content = {
            "type": "file",
            "encoding": "base64",
            "sha": "blob123",
            "size": len(VALID_YAML.encode()),
            "content": base64.b64encode(VALID_YAML.encode()).decode(),
        }

    def validate(self, responses):
        with patch.object(validator, "github_api", side_effect=responses) as api:
            errors = validator.validate_submission("blinkospace/blinko-hub", "123", "alice/blinko-hub", "abc123")
        return errors, api

    def test_valid_fork_file_is_fetched_at_exact_commit(self):
        errors, api = self.validate([self.pr, [[self.file]], self.content, self.pr])
        self.assertEqual(errors, [])
        self.assertEqual(api.call_args_list[2].args[0], "repos/alice/blinko-hub/contents/sites/alice.yml?ref=abc123")

    def test_existing_entry_can_be_modified(self):
        self.file["status"] = "modified"
        self.assertEqual(self.validate([self.pr, [[self.file]], self.content, self.pr])[0], [])

    def test_mixed_pr_is_rejected_before_fetching_content(self):
        self.pr["changed_files"] = 2
        other = {"filename": ".github/workflows/pr-check.yml", "status": "modified"}
        errors, api = self.validate([self.pr, [[self.file, other]]])
        self.assertTrue(errors)
        self.assertEqual(api.call_count, 2)

    def test_only_direct_site_additions_and_modifications_are_permitted(self):
        for path, status in [
            ("sites/alice.yml", "removed"),
            ("sites/alice.yml", "renamed"),
            ("sites/subdir/alice.yml", "added"),
            ("sites/../workflow.yml", "added"),
            ("sites/alice.yaml", "added"),
            ("sites/alice\\file.yml", "added"),
            ("sites/alice\nfile.yml", "added"),
        ]:
            with self.subTest(path=path, status=status):
                self.assertFalse(validator.permitted_file({"filename": path, "status": status}))

    def test_incomplete_file_list_fails_closed(self):
        self.pr["changed_files"] = 2
        self.assertTrue(self.validate([self.pr, [[self.file]]])[0])

    def test_every_file_page_is_validated(self):
        self.pr["changed_files"] = 2
        second = dict(self.file, filename="sites/bob.yml")
        errors, api = self.validate([self.pr, [[self.file], [second]], self.content, self.content, self.pr])
        self.assertEqual(errors, [])
        self.assertTrue(api.call_args_list[1].kwargs["paginate"])

    def test_changed_head_is_rejected_before_validation(self):
        self.pr["head"]["sha"] = "new-sha"
        errors, api = self.validate([self.pr])
        self.assertTrue(errors)
        self.assertEqual(api.call_count, 1)

    def test_changed_head_during_validation_is_rejected(self):
        updated = copy.deepcopy(self.pr)
        updated["head"]["sha"] = "new-sha"
        self.assertTrue(self.validate([self.pr, [[self.file]], self.content, updated])[0])

    def test_retargeted_pr_is_rejected_after_validation(self):
        updated = copy.deepcopy(self.pr)
        updated["base"]["ref"] = "other"
        self.assertTrue(self.validate([self.pr, [[self.file]], self.content, updated])[0])

    def test_submission_file_limit_is_checked_before_downloads(self):
        files = [dict(self.file, filename=f"sites/site-{index}.yml") for index in range(validator.MAX_FILES + 1)]
        self.pr["changed_files"] = len(files)
        errors, api = self.validate([self.pr, [files]])
        self.assertTrue(errors)
        self.assertEqual(api.call_count, 2)

    def test_total_download_size_is_limited(self):
        files = [dict(self.file, filename=f"sites/site-{index}.yml") for index in range(6)]
        self.pr["changed_files"] = len(files)
        content = dict(self.content, size=validator.MAX_FILE_BYTES)
        self.assertTrue(self.validate([self.pr, [files]] + [content] * 6)[0])

    def test_draft_closed_and_wrong_base_are_rejected(self):
        for changes in [{"draft": True}, {"state": "closed"}, {"base": {"ref": "other"}}]:
            with self.subTest(changes=changes):
                self.assertTrue(self.validate([dict(self.pr, **changes)])[0])

    def test_wrong_blob_or_oversized_content_is_rejected(self):
        for changes in [{"sha": "wrong"}, {"size": validator.MAX_FILE_BYTES + 1}, {"type": "symlink"}]:
            with self.subTest(changes=changes):
                content = dict(self.content, **changes)
                self.assertTrue(self.validate([self.pr, [[self.file]], content, self.pr])[0])

    def test_invalid_yaml_and_field_types_are_rejected(self):
        for content in ["[", "null", "[]", "title: 123", VALID_YAML.replace("[english, blog]", "[]"), VALID_YAML.replace("https://notes.example.com", "ftp://example.com"), VALID_YAML.replace("2026-10-07", "not-a-date")]:
            with self.subTest(content=content):
                self.assertTrue(validator.validate_yaml(content, "sites/alice.yml"))
        self.assertTrue(validator.validate_yaml(VALID_YAML, "sites/my-site.yml"))

    def test_api_failure_keeps_merge_output_false(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            environment = {"GITHUB_OUTPUT": str(output), "GITHUB_REPOSITORY": "blinkospace/blinko-hub", "PR_NUMBER": "123", "PR_HEAD_REPO": "alice/blinko-hub", "PR_HEAD_SHA": "abc123"}
            with patch.dict(os.environ, environment), patch.object(validator, "github_api", side_effect=subprocess.CalledProcessError(1, ["gh", "api"])):
                self.assertEqual(validator.main(), 1)
            self.assertEqual(output.read_text(), "is_valid=false\n")


if __name__ == "__main__":
    unittest.main()
