# Security

## What counts

The skill runs Python inside your own Blender session through the MCP for Blender add-on. A vulnerability here is anything that lets the skill's scripts do more than the user asked: writing outside the project folder, sending data off the machine, saving over or closing the user's file unprompted, resetting Blender's preferences, or running code from untrusted input such as asset descriptions.

The add-on's socket (default `127.0.0.1:9876`) has no authentication and the add-on executes arbitrary Python by design. Keep it on localhost and save your work before you start. Problems in the add-on itself belong in [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp).

## Reporting

Use GitHub's private vulnerability reporting: **Security** tab, then **Report a vulnerability**. Please do not open a public issue for a security problem.

I aim to reply within 7 days and to fix confirmed issues in the next release. This is a one-person project, so those are goals and not guarantees.

## Supported versions

Only the latest release on `main`.
