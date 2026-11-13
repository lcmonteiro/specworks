   **Back from review**: when `specworks cycle --change "<ref>" --json`
   lists open findings whose `phase` is {{phases}} (`R<n>` from review.md,
   `V<n>` from validation.md), you carried out their agreed proposal (the
   Decision, else the Proposal); once the gate passes, record each one by its
   ID{{note}}:
   ```bash
   specworks finding done <ID> --in {{in}} --change "<ref>" "<what changed>"
   ```
   It stays open: review checks it, and the step that found it closes it
   (review its `R` findings, validate its `V` findings).
