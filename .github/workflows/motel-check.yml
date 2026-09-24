name: motel-check
on:
  schedule:
    - cron: '30 */3 * * *'
  workflow_dispatch:
jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: python checker_1.py
      - name: Commit
        run: |
          git config user.name "auto"
          git config user.email "auto@auto.com"
          git add -f final_60.m3u final_60.m3u8 final_60.xml DCcatalog_60.m3u DCcatalog_60.m3u8 DCcatalog_60.xml full_ca_us.m3u
          git diff --staged --quiet && exit 0
          git commit -m "auto update final_60 60ch from DCcatalog + guide - 3h @ :30"
          git push
