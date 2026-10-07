import base64
import binascii
import json
import os
from pathlib import PurePosixPath
import subprocess
import sys
from datetime import datetime
from urllib.parse import quote

import yaml

MAX_FILE_BYTES = 1024 * 1024
MAX_FILES = 50
MAX_TOTAL_BYTES = 5 * 1024 * 1024


def github_api(endpoint, paginate=False):
    command = ["gh", "api", endpoint]
    if paginate:
        command.extend(["--paginate", "--slurp"])
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def validate_yaml(content, file_path):
    errors = []
    if PurePosixPath(file_path).name == "my-site.yml":
        errors.append("Cannot use default filename 'my-site.yml'")
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return errors + ["Invalid YAML"]
    if not isinstance(data, dict):
        return errors + ["Site entry must be a YAML mapping"]

    for field in ["title", "url", "tags", "created_at"]:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            errors.append("Title must be a nonempty string")
        elif data["title"] in ["Site Name", "Your Site Name"]:
            errors.append("Cannot use a default title")
    if "url" in data and (
        not isinstance(data["url"], str)
        or not data["url"].startswith(("http://", "https://"))
    ):
        errors.append("URL must start with http:// or https://")
    if "tags" in data and (
        not isinstance(data["tags"], list)
        or not data["tags"]
        or any(not isinstance(tag, str) or not tag.strip() for tag in data["tags"])
    ):
        errors.append("Tags must be a nonempty list of nonempty strings")
    if "created_at" in data:
        try:
            datetime.strptime(str(data["created_at"]), "%Y-%m-%d")
        except ValueError:
            errors.append("created_at must use YYYY-MM-DD format")
    return errors


def permitted_file(file):
    path = PurePosixPath(file["filename"])
    return (
        len(path.parts) == 2
        and path.parts[0] == "sites"
        and path.suffix == ".yml"
        and "\\" not in file["filename"]
        and not any(ord(character) < 32 for character in file["filename"])
        and file["status"] in ("added", "modified")
    )


def validate_submission(repository, pr_number, head_repository, head_sha):
    endpoint = f"repos/{repository}/pulls/{pr_number}"
    pr = github_api(endpoint)
    if pr["state"] != "open" or pr["draft"]:
        return ["PR must be open and ready for review"]
    if pr["base"]["ref"] != "main":
        return ["PR must target main"]
    if pr["head"]["sha"] != head_sha or pr["head"]["repo"]["full_name"] != head_repository:
        return ["PR head changed; wait for validation of the latest commit"]

    pages = github_api(f"{endpoint}/files?per_page=100", paginate=True)
    files = [file for page in pages for file in page]
    if not files or len(files) != pr["changed_files"]:
        return ["Could not retrieve the complete list of changed files"]
    if len(files) > MAX_FILES:
        return [f"Automatic merging accepts at most {MAX_FILES} site files per PR"]
    if any(not permitted_file(file) for file in files):
        return ["Automatic merging only accepts additions or modifications to sites/*.yml"]

    errors = []
    total_bytes = 0
    for file in files:
        path = file["filename"]
        content = github_api(
            f"repos/{head_repository}/contents/{quote(path, safe='/')}?ref={quote(head_sha, safe='')}"
        )
        if (
            content.get("type") != "file"
            or content.get("encoding") != "base64"
            or content.get("sha") != file["sha"]
            or not isinstance(content.get("size"), int)
            or content["size"] > MAX_FILE_BYTES
        ):
            errors.append(f"{path}: Could not retrieve a matching YAML file of at most 1 MiB")
            continue
        total_bytes += content["size"]
        if total_bytes > MAX_TOTAL_BYTES:
            return ["Automatic merging accepts at most 5 MiB of site files per PR"]
        try:
            raw = base64.b64decode("".join(content["content"].split()), validate=True)
            if len(raw) > MAX_FILE_BYTES:
                raise ValueError("File too large")
            text = raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            errors.append(f"{path}: Invalid or oversized UTF-8 file")
            continue
        errors.extend(f"{path}: {error}" for error in validate_yaml(text, path))

    latest = github_api(endpoint)
    if latest["head"]["sha"] != head_sha:
        errors.append("PR head changed during validation; wait for the latest run")
    if latest["base"]["ref"] != "main" or latest["state"] != "open" or latest["draft"]:
        errors.append("PR must still be open, ready for review, and targeting main")
    return errors


def write_output(valid):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"is_valid={str(valid).lower()}\n")


def main():
    write_output(False)
    try:
        errors = validate_submission(
            os.environ["GITHUB_REPOSITORY"],
            os.environ["PR_NUMBER"],
            os.environ["PR_HEAD_REPO"],
            os.environ["PR_HEAD_SHA"],
        )
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError) as error:
        print(f"Validation could not complete ({type(error).__name__})", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error)
        return 1
    write_output(True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
