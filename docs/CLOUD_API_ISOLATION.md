# Cloud API Isolation

Cloud APIs are disabled by default. When a later phase enables explicitly guarded
cloud workflows, cloud code may only read files from
`resources/cloud_resources/allowed_inputs/` and may only write files to
`resources/cloud_resources/allowed_outputs/`.

Cloud code must not read raw local resources, memory files, arbitrary state, or
logs by path traversal or convenience fallback. Data entering a cloud workflow
must be curated into the allowed input directory first.
