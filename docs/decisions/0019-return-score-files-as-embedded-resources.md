<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-FileContributor: bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 19. Return score files as embedded resources

- Status: accepted
- Date: 2026-11-23
- Issue: #15

## Context

Users want to receive a score in the conversation, in any MCP client, not
only open a copy on their computer. The released MCP revision (2026-07-28)
lets a tool result carry a file as an embedded resource (`blob` with a
media type) or point to one with a `resource_link`; what a host does with
it is up to the host. MCP Apps adds `ui/download-file` (`App.downloadFile`),
through which a view asks the host to save embedded or linked contents,
when the host advertises the `downloadFile` capability.

The download targets of the experimental `io.modelcontextprotocol/files`
extension need HTTPS URLs, which personal mode over stdio does not have.

A file returned to the model may be passed into its context, which is
costly for large files.

## Decision

- Tools return files through an SDK-independent `ToolFile` (name, media
  type, bytes) in `ToolResult.files`. The MCP adapter turns each one into
  an `EmbeddedResource` with a `BlobResourceContents` whose URI is
  `file:///<percent-encoded name>`, the convention of the MCP Apps
  examples, since an embedded resource has no other place for a file name.
- `get_score_file(score_id)`, called by the model, returns the score as
  such a file, up to 2 MiB of content; above, it refuses and points to
  `open_score` and to the Work view.
- `download_score(score_id)` is app-only: the Work view calls it and gives
  the embedded resource to `App.downloadFile`. The 2 MiB limit is lifted
  only for a call whose client declared MCP Apps support
  (`io.modelcontextprotocol/ui` with the `text/html;profile=mcp-app` media
  type), which keeps app-only tools away from the model; a client without
  it may expose the tool to its model, so the limit applies.
  The Download button is shown only when the host advertises
  `downloadFile`.

## Alternatives considered

- **`resource_link` to a `mbc://scores/{id}` resource template read with
  `resources/read`**: lighter results, but no host is required to read
  the link, and `downloadFile` with a link expects the host to fetch it.
  Rejected.
- **One tool with an "unlimited" argument**: the model could pass it and
  bypass the conversation limit. Rejected.
- **Tools returning SDK content types**: breaks the isolation of the MCP
  SDK in the adapter. Rejected.
- **The limit as a configuration key**: it is not specific to an
  environment. Kept as a constant injected through the constructor.

## Consequences

- Hosts that accept embedded resources can show or save the score; the
  text of the result stays self-sufficient for those that do not.
- A score of up to 2 MiB may enter the model context of hosts that pass
  embedded resources to the model.
- A download from the view moves up to about 67 MB of base64 between the
  view and the host, like the existing upload.
- The capability is declared by the client, not proven: it guards against a
  client exposing app-only tools to its model by mistake, not against a
  client that lies about its capabilities.
- The file name given to hosts is the download name: the original name
  made safe, with the extension of the detected format, so a saved file
  opens with the application of its real format. The original name stays
  unchanged in the score's metadata.
