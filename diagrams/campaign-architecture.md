# Campaign architecture diagram

Status: target specification; `SPECIFIED_NOT_IMPLEMENTED` unless the
implementation matrix says otherwise.

```mermaid
flowchart TD
  CA[Campaign authority] --> CE[Signed CampaignEpoch]
  VI[Verification Issuer] --> ST[SpendToken or SpendTokens]

  CE --> AR{Audience rule present?}
  ST --> AR
  AR -- yes --> PA[ProofOfMatch AUDIENCE]
  PA --> VAC[finalized Solana ACCEPT: SolanaProofEvidence]
  AR -- no --> EXP{Multiple experimental arms?}
  VAC --> EXP

  EXP -- yes --> AS[Deterministic assignment state or AssignmentRecord]
  AS --> EX[Exposure state if delivered]
  EXP -- no --> CT[Conversion SpendToken or SpendTokens]
  EX --> CT

  CT --> PC[ProofOfMatch CONVERSION]
  CE --> PC
  PC --> VCC[finalized Solana ACCEPT: SolanaProofEvidence]
  VCC --> EA{Economic admission required?}

  CE --> EA
  EA -- yes --> AL[Authoritative capacity/budget ledger]
  AL --> AD[Atomic ADMITTED or REJECTED evidence]
  EA -- no --> CO[CampaignOutcome]
  AD --> CO
  VAC -. when applicable .-> CO
  AS -. when applicable .-> CO
  EX -. when applicable .-> CO

  CO --> MEAS[Measurement input]
  CO --> ENT{Reward obligation created?}
  ENT -- yes --> RO[RewardObligation]
  RO --> SR[SettlementRecord]
  ENT -- no --> STOP[Measurement-only or capacity-rejected outcome]
```

The frozen Solana verifier program accepts exact proof subjects under
Procedure Profile V3, and the relying Consumer reconstructs the finalized
`ACCEPT` as `SolanaProofEvidenceV1`. Neither produces assignment, economic
admission, Outcomes, obligations, or settlement. The procedure has
`stateTransition = NONE`; the program's `ACCEPT` record blocks exact proof
replay only, and any capacity, Reward Ledger, or settlement state change names
its own authoritative registry, ledger, or chain.
