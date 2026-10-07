# Blinko Hub
![image](https://github.com/user-attachments/assets/e41f4fdf-8c44-4a2e-a826-cccac980882e)

A directory of Blinko sites worldwide. This repository serves as a centralized registry for all Blinko instances.

## Quick Add Your Site

[![Add Site](https://img.shields.io/badge/-Click%20to%20Add%20Site-blue?style=for-the-badge&logo=github)](https://github.com/blinko-space/blinko-hub/new/main/sites?filename=my-site.yml&value=title%3A%20%22Your%20Site%20Name%22%0Aurl%3A%20%22https%3A%2F%2Fyour-site-domain%22%0Atags%3A%20%0A%20%20-%20english%20%20%20%20%23%20main%20language%0A%20%20-%20blog%20%20%20%20%20%20%20%23%20site%20type%0Acreated_at%3A%20%222024-01-14%22%20%20%23%20creation%20date)

Click the button above to add your site and submit a PR.

## Data Format

Site Configuration Format:

```yaml
title: "Site Name"
url: "https://example.blinko.space"
tags: 
  - english    # language tag
  - blog       # site type
created_at: "2024-01-14"
```

## Manual Steps

1. Fork this repository
2. Create a new yml file in the `sites` directory
3. Submit a Pull Request

PRs targeting `main` that only add or modify `sites/*.yml` files are automatically
merged after validation. Each entry must include a non-placeholder title, an HTTP
or HTTPS URL, a nonempty list of text tags, and a valid creation date. Automatic
merging accepts at most 50 files, 1 MiB per file, and 5 MiB in total. Draft PRs,
deletions, renames, and PRs containing other changes require manual review.

The workflow runs the validator from the trusted base branch and reads submitted
YAML through GitHub's API at the PR's exact commit. It does not execute code from
contributors' branches, and it only merges the commit that passed validation.

To run the validator tests locally, install `pyyaml==6.0.3`, then run:

```bash
python -m unittest discover -s .github/scripts -p 'test_*.py'
```
