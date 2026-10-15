# Contributing

Issues and pull requests are welcome.

- **Reporting a problem:** include your Blender version (`check_setup.py` prints it), the script that failed and the error text.
- **Adding to the notes:** only add what you ran in Blender. Mark anything unrun **untested**.
- **Adding a recipe or helper:** keep `SKILL.md` short and put detail in `skills/blender-studio/references/`. A helper goes in `bl_lib.py` only if two recipes need it.
- **Before a pull request:** run `python tools/smoke_test.py`. With Blender installed it also builds a keychain headless and checks the mesh.
- **Copy:** public pages and docs should read like a person wrote them. Run the slopmonster check if you have it.
- Open an issue before a large change so we agree on the direction first. Replies take about a week.
- Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md). Security problems go through [`SECURITY.md`](SECURITY.md), not a public issue.
- Do not commit generated zips, secrets, customer artwork or models you do not have the right to share.
