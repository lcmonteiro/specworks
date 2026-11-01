     ```bash
     specworks start implement --change "<ref>"
     ```
     It runs the gates of the phases left behind (`gate design`, and
     `gate specify` too if the change skips design) and moves the change to
     implement only if they pass. When the change is already in implement
     (the {{other}} half started it), it re-checks `gate design` only.
   - If a gate fails, stop: show the failing checks and suggest
     `/specworks-design <ref>` (or `/specworks-specify <ref>` when the specs
     themselves fail).