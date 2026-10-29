---
name: manage-dev-library
description: Use when the user asks to save, annotate, remove or retrieve a project or article in the personal AI Dev Radar library.
---

# Manage the development library

Status: draft workflow; runtime behavioral acceptance is pending.

Resolve the user's target to an exact item ID using the current conversation or `radar_items_search`. If ambiguous, clarify before writing. A recommendation is not itself a request to save.

For an explicit save or note update, call `radar_bookmark_save(item_id, request_key, note)`. The note replaces the existing note; when the user asks to append, read the current item first and compose the combined text. Notes are limited to 5000 characters.

For explicit removal, call `radar_bookmark_remove(item_id, request_key)`. Removal affects the bookmark, not the collected item.

Create one unique request key per user operation and retain it with the exact arguments. Retry an uncertain operation using the SAME key and arguments. A new user operation receives a new key. On CONFLICT, investigate the original operation; do not automatically generate a new key to bypass the conflict. On NOT_FOUND, resolve the item again.

A replay receipt describes the ORIGINAL operation outcome, which may differ from current state. Always use `radar_item_get` after mutation/replay and report the current bookmark/note. If read-back fails, say the operation returned a receipt but current state could not be confirmed. Do not claim success from a proposed tool call.

To retrieve saved items in another conversation, query with `bookmarked=true`; do not assume the previous conversation is available. Bookmark persistence is separate from conversation persistence.
