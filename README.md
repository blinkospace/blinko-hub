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

## Batch Follow Script

Want to follow all Hub sites at once into your Blinko recommendation feed?

1. Open and log into your Blinko site in a browser.
2. Press `F12` to open Developer Tools and switch to the **Console** tab.
3. Copy and run the code from [scripts/batch-follow.js](scripts/batch-follow.js).

