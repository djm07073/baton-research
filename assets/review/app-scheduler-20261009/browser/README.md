# Local browser checks

`verification.json` and the adjacent PNGs hold the latest browser check. Timestamped snapshot directories preserve earlier available receipts before later runs replace the latest files. Reports and checkpoints scope their claims to the recorded check time; a browser check does not validate the protocol or imply later prose was inspected.

The checker starts a loopback-only server and local headless Chromium. It loads every current navigation page, decodes diagrams, checks navigation, requests every unique same-origin article link target, checks linked HTML fragment IDs, exercises search/mobile menu controls, and completes all three source-artifact downloads with byte-for-byte comparison to the repository originals. Each checked page records its source and generated HTML hashes. It does not fetch external websites or recursively browse downloaded reference documents. Screenshots are inspected separately, as named in the associated review report.
