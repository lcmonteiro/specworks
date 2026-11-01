   **Back from review**: when `specworks cycle --change "<ref>" --json`
   lists open findings whose `phase` is {{phases}}, you carried out their
   agreed proposal (the Decision); once the gate passes, record each one{{note}}:
   ```bash
   specworks finding done R<n> --in {{in}} --change "<ref>" "<what changed>"
   ```
   It stays open: review checks it and closes it.
