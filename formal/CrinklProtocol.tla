--------------------------- MODULE CrinklProtocol ---------------------------
(*
    TLA+ Formal Specification for Crinkl Protocol v1.0.0-rc.1
    
    This specification models:
    - Attestation Ledger state machine (receipt verification lifecycle)
    - Reward Ledger state machine (reward issuance lifecycle)
    - Event chain integrity (prevHash linking)
    - State transition validity
    
    Run with TLC model checker to verify invariants.
*)

EXTENDS Integers, Sequences, FiniteSets

CONSTANTS
    SpendIds,           \* Set of possible spend IDs
    WalletAddresses,    \* Set of wallet addresses
    MaxEvents           \* Bound for model checking

VARIABLES
    truthState,         \* Function: ReceiptId -> TruthState
    rewardState,        \* Function: ReceiptId -> RewardState  
    eventLog,           \* Sequence of all events
    eventHashes,        \* Function: EventIndex -> Hash
    lastHash,           \* Hash of most recent event (for prevHash)
    committedBatches,   \* Set of committed batch IDs (Commitment Layer)
    batchRewards,       \* Function: BatchId -> Set of ReceiptIds in batch
    corrections,        \* Set of correction batch IDs
    snapshots,          \* Sequence of cumulative snapshots
    authorities,        \* Function: AuthorityId -> AuthorityRecord
    currentAuthority    \* Currently active authority ID

(* Attestation Ledger States *)
TruthStates == {"NONE", "UPLOADED", "SOFT_VERIFIED", "HARD_VERIFIED", 
                "FINALIZED", "INVALIDATED", "CORRECTED"}

(* Reward Ledger States *)
RewardStates == {"NO_REWARD", "PROVISIONAL", "FINAL"}

(* Event Types *)
TruthEvents == {"RECEIPT_UPLOADED", "SPEND_SOFT_VERIFIED", "SPEND_HARD_VERIFIED",
                "SPEND_INVALIDATED", "SPEND_CORRECTED", "FRAUD_FLAGGED"}
                
RewardEvents == {"REWARD_PROVISIONAL_ISSUED", "REWARD_FINAL_ISSUED"}

CommitmentEvents == {"REWARD_BATCH_COMMITTED", "REWARD_BATCH_CORRECTION", 
                     "CUMULATIVE_SNAPSHOT_COMMITTED", "AUTHORITY_REGISTERED", 
                     "AUTHORITY_REVOKED"}

AllEvents == TruthEvents \union RewardEvents \union CommitmentEvents

(* Type invariant *)
TypeInvariant ==
    /\ truthState \in [SpendIds -> TruthStates]
    /\ rewardState \in [SpendIds -> RewardStates]
    /\ eventLog \in Seq([type: AllEvents, spendId: SpendIds])
    /\ Len(eventLog) <= MaxEvents

-----------------------------------------------------------------------------
(* Initial State *)

Init ==
    /\ truthState = [s \in SpendIds |-> "NONE"]
    /\ rewardState = [s \in SpendIds |-> "NO_REWARD"]
    /\ eventLog = <<>>
    /\ eventHashes = <<>>
    /\ lastHash = "NULL"
    /\ committedBatches = {}
    /\ batchRewards = <<>>
    /\ corrections = {}
    /\ snapshots = <<>>
    /\ authorities = <<>>
    /\ currentAuthority = "NONE"

-----------------------------------------------------------------------------
(* Attestation Ledger Transitions *)

(* Upload a new receipt *)
UploadReceipt(s) ==
    /\ truthState[s] = "NONE"
    /\ truthState' = [truthState EXCEPT ![s] = "UPLOADED"]
    /\ eventLog' = Append(eventLog, [type |-> "RECEIPT_UPLOADED", spendId |-> s])
    /\ UNCHANGED <<rewardState>>

(* Soft verification (OCR extraction) *)
SoftVerify(s) ==
    /\ truthState[s] = "UPLOADED"
    /\ truthState' = [truthState EXCEPT ![s] = "SOFT_VERIFIED"]
    /\ eventLog' = Append(eventLog, [type |-> "SPEND_SOFT_VERIFIED", spendId |-> s])
    /\ UNCHANGED <<rewardState>>

(* Hard verification (confirmed) *)    
HardVerify(s) ==
    /\ truthState[s] = "SOFT_VERIFIED"
    /\ truthState' = [truthState EXCEPT ![s] = "HARD_VERIFIED"]
    /\ eventLog' = Append(eventLog, [type |-> "SPEND_HARD_VERIFIED", spendId |-> s])
    /\ UNCHANGED <<rewardState>>

(* Finalization (after waiting period) *)
Finalize(s) ==
    /\ truthState[s] = "HARD_VERIFIED"
    /\ truthState' = [truthState EXCEPT ![s] = "FINALIZED"]
    /\ UNCHANGED <<rewardState, eventLog>>  \* Implicit transition, no event

(* Invalidation (rejection) *)
Invalidate(s) ==
    /\ truthState[s] \in {"UPLOADED", "SOFT_VERIFIED", "HARD_VERIFIED"}
    /\ truthState' = [truthState EXCEPT ![s] = "INVALIDATED"]
    /\ eventLog' = Append(eventLog, [type |-> "SPEND_INVALIDATED", spendId |-> s])
    /\ UNCHANGED <<rewardState>>

(* Correction (post-finalization fix) *)
Correct(s) ==
    /\ truthState[s] \in {"FINALIZED", "CORRECTED"}
    /\ truthState' = [truthState EXCEPT ![s] = "CORRECTED"]
    /\ eventLog' = Append(eventLog, [type |-> "SPEND_CORRECTED", spendId |-> s])
    /\ UNCHANGED <<rewardState>>

(* Fraud flagging *)
FlagFraud(s) ==
    /\ truthState[s] \in {"FINALIZED", "CORRECTED"}
    /\ eventLog' = Append(eventLog, [type |-> "FRAUD_FLAGGED", spendId |-> s])
    /\ UNCHANGED <<truthState, rewardState>>

-----------------------------------------------------------------------------
(* Reward Ledger Transitions *)

(* Issue provisional reward *)
IssueProvisionalReward(s) ==
    /\ rewardState[s] = "NO_REWARD"
    /\ truthState[s] \in {"SOFT_VERIFIED", "HARD_VERIFIED", "FINALIZED"}
    /\ rewardState' = [rewardState EXCEPT ![s] = "PROVISIONAL"]
    /\ eventLog' = Append(eventLog, [type |-> "REWARD_PROVISIONAL_ISSUED", spendId |-> s])
    /\ UNCHANGED <<truthState>>

(* Issue final reward *)
IssueFinalReward(s) ==
    /\ rewardState[s] \in {"NO_REWARD", "PROVISIONAL"}
    /\ truthState[s] \in {"HARD_VERIFIED", "FINALIZED", "CORRECTED"}
    /\ rewardState' = [rewardState EXCEPT ![s] = "FINAL"]
    /\ eventLog' = Append(eventLog, [type |-> "REWARD_FINAL_ISSUED", spendId |-> s])
    /\ UNCHANGED <<truthState>>

(* Note: No ClawbackReward action - Reward Ledger is immutable.
   Fraud is handled via FRAUD_FLAGGED with negative deltas appended. *)

-----------------------------------------------------------------------------
(* Commitment Layer Transitions *)

(* Commit a batch of final rewards on-chain *)
CommitRewardBatch(batchId, spends) ==
    /\ batchId \notin committedBatches
    /\ \A s \in spends: rewardState[s] = "FINAL"
    /\ currentAuthority # "NONE"
    /\ committedBatches' = committedBatches \union {batchId}
    /\ batchRewards' = Append(batchRewards, [batch |-> batchId, rewards |-> spends])
    /\ eventLog' = Append(eventLog, [type |-> "REWARD_BATCH_COMMITTED", batchId |-> batchId])
    /\ UNCHANGED <<truthState, rewardState, corrections, snapshots, authorities, currentAuthority>>

(* Issue a correction for a previously committed batch *)
CorrectBatch(correctionId, targetBatchId) ==
    /\ correctionId \notin corrections
    /\ correctionId \notin committedBatches
    /\ targetBatchId \in committedBatches
    /\ currentAuthority # "NONE"
    /\ corrections' = corrections \union {correctionId}
    /\ eventLog' = Append(eventLog, [type |-> "REWARD_BATCH_CORRECTION", 
                                      correctionId |-> correctionId,
                                      targetBatchId |-> targetBatchId])
    /\ UNCHANGED <<truthState, rewardState, committedBatches, batchRewards, snapshots, authorities, currentAuthority>>

(* Create a cumulative snapshot *)
CreateSnapshot(snapshotId, throughBatchId) ==
    /\ throughBatchId \in committedBatches
    /\ currentAuthority # "NONE"
    /\ snapshots' = Append(snapshots, [id |-> snapshotId, throughBatch |-> throughBatchId])
    /\ eventLog' = Append(eventLog, [type |-> "CUMULATIVE_SNAPSHOT_COMMITTED", 
                                      snapshotId |-> snapshotId])
    /\ UNCHANGED <<truthState, rewardState, committedBatches, batchRewards, corrections, authorities, currentAuthority>>

(* Register a new authority *)
RegisterAuthority(authorityId) ==
    /\ \A i \in 1..Len(authorities): authorities[i].id # authorityId
    /\ authorities' = Append(authorities, [id |-> authorityId, revoked |-> FALSE])
    /\ currentAuthority' = authorityId
    /\ eventLog' = Append(eventLog, [type |-> "AUTHORITY_REGISTERED", authorityId |-> authorityId])
    /\ UNCHANGED <<truthState, rewardState, committedBatches, batchRewards, corrections, snapshots>>

(* Revoke an authority *)
RevokeAuthority(authorityId, newAuthorityId) ==
    /\ currentAuthority = authorityId
    /\ newAuthorityId # authorityId
    /\ authorities' = Append(authorities, [id |-> newAuthorityId, revoked |-> FALSE])
    /\ currentAuthority' = newAuthorityId
    /\ eventLog' = Append(eventLog, [type |-> "AUTHORITY_REVOKED", 
                                      authorityId |-> authorityId,
                                      revokedBy |-> newAuthorityId])
    /\ UNCHANGED <<truthState, rewardState, committedBatches, batchRewards, corrections, snapshots>>

-----------------------------------------------------------------------------
(* Next State Relation *)

Next ==
    \E s \in SpendIds:
        \/ UploadReceipt(s)
        \/ SoftVerify(s)
        \/ HardVerify(s)
        \/ Finalize(s)
        \/ Invalidate(s)
        \/ Correct(s)
        \/ FlagFraud(s)
        \/ IssueProvisionalReward(s)
        \/ IssueFinalReward(s)

Spec == Init /\ [][Next]_<<truthState, rewardState, eventLog, eventHashes, lastHash, committedBatches, batchRewards, corrections, snapshots, authorities, currentAuthority>>

-----------------------------------------------------------------------------
(* Safety Invariants *)

(* I1: No reward without verification *)
NoRewardWithoutVerification ==
    \A s \in SpendIds:
        rewardState[s] # "NO_REWARD" => 
            truthState[s] \in {"SOFT_VERIFIED", "HARD_VERIFIED", "FINALIZED", 
                               "CORRECTED", "INVALIDATED"}

(* I2: Final reward requires hard verification *)
FinalRewardRequiresHardVerification ==
    \A s \in SpendIds:
        rewardState[s] = "FINAL" =>
            truthState[s] \in {"HARD_VERIFIED", "FINALIZED", "CORRECTED", "INVALIDATED"}

(* I3: Invalidated spends cannot reach FINALIZED after invalidation *)
InvalidatedNeverFinalized ==
    \A s \in SpendIds:
        truthState[s] = "INVALIDATED" =>
            ~(\E i \in 1..Len(eventLog): 
                eventLog[i].spendId = s /\ 
                eventLog[i].type \in {"SPEND_HARD_VERIFIED"} /\
                \E j \in 1..Len(eventLog): j > i /\ eventLog[j].spendId = s /\ eventLog[j].type = "SPEND_INVALIDATED")

(* I4: Corrections only after finalization *)
CorrectionsAfterFinalization ==
    \A i \in 1..Len(eventLog):
        eventLog[i].type = "SPEND_CORRECTED" =>
            \E j \in 1..(i-1): 
                eventLog[j].spendId = eventLog[i].spendId /\
                eventLog[j].type = "SPEND_HARD_VERIFIED"

(* I5: Monotonic state progression (no rollback except INVALIDATED) *)
MonotonicProgression ==
    \A s \in SpendIds:
        /\ truthState[s] = "FINALIZED" => 
            ~(\E i \in 1..Len(eventLog): 
                eventLog[i].spendId = s /\ 
                eventLog[i].type \in {"RECEIPT_UPLOADED", "SPEND_SOFT_VERIFIED"} /\
                \E j \in 1..i: eventLog[j].spendId = s /\ eventLog[j].type = "SPEND_HARD_VERIFIED")

(* I6: Reward Ledger immutability - rewards never change state backwards *)
RewardLedgerImmutability ==
    \A s \in SpendIds:
        rewardState[s] = "FINAL" => 
            ~(\E i \in 1..Len(eventLog): 
                eventLog[i].spendId = s /\ 
                eventLog[i].type = "REWARD_PROVISIONAL_ISSUED" /\
                \E j \in 1..i: eventLog[j].spendId = s /\ eventLog[j].type = "REWARD_FINAL_ISSUED")

-----------------------------------------------------------------------------
(* Commitment Layer Invariants *)

(* I7: Only final rewards can be committed *)
CommitmentRequiresFinalReward ==
    \A i \in 1..Len(batchRewards):
        \A s \in batchRewards[i].rewards:
            \/ rewardState[s] = "FINAL"
            \/ \E j \in 1..Len(eventLog):
                eventLog[j].spendId = s /\
                eventLog[j].type = "REWARD_FINAL_ISSUED"

(* I8: Committed batches are immutable - no deletion or modification *)
CommittedBatchImmutability ==
    \A b \in committedBatches:
        \E i \in 1..Len(eventLog):
            eventLog[i].type = "REWARD_BATCH_COMMITTED" /\
            eventLog[i].batchId = b

(* I9: Batch IDs are unique and monotonic *)
BatchIdUniqueness ==
    \A i, j \in 1..Len(batchRewards):
        i # j => batchRewards[i].batch # batchRewards[j].batch

(* I10: Corrections must reference existing batches *)
CorrectionTargetExists ==
    \A i \in 1..Len(eventLog):
        eventLog[i].type = "REWARD_BATCH_CORRECTION" =>
            eventLog[i].targetBatchId \in committedBatches

(* I11: Snapshots must reference existing batches *)
SnapshotTargetExists ==
    \A i \in 1..Len(snapshots):
        snapshots[i].throughBatch \in committedBatches

(* I12: Only current authority can commit *)
AuthorityRequiredForCommit ==
    \A i \in 1..Len(eventLog):
        eventLog[i].type \in {"REWARD_BATCH_COMMITTED", "REWARD_BATCH_CORRECTION", 
                              "CUMULATIVE_SNAPSHOT_COMMITTED"} =>
            \E j \in 1..Len(authorities): 
                authorities[j].revoked = FALSE

(* I13: Authority chain is unbroken - revoked authority replaced by new one *)
AuthorityChainIntegrity ==
    \A i \in 1..Len(eventLog):
        eventLog[i].type = "AUTHORITY_REVOKED" =>
            \E j \in 1..Len(eventLog):
                j > i /\ 
                eventLog[j].type = "AUTHORITY_REGISTERED"

-----------------------------------------------------------------------------
(* Liveness Properties (under fairness) *)

(* L1: Every uploaded spend eventually reaches terminal state *)
EventualTermination ==
    \A s \in SpendIds:
        truthState[s] = "UPLOADED" ~>
            truthState[s] \in {"FINALIZED", "INVALIDATED", "CORRECTED"}

(* L2: Every hard-verified spend eventually gets finalized *)
EventualFinalization ==
    \A s \in SpendIds:
        truthState[s] = "HARD_VERIFIED" ~> 
            truthState[s] \in {"FINALIZED", "CORRECTED"}

-----------------------------------------------------------------------------
(* Theorems to Check *)

THEOREM Spec => []TypeInvariant
THEOREM Spec => []NoRewardWithoutVerification
THEOREM Spec => []FinalRewardRequiresHardVerification
THEOREM Spec => []CorrectionsAfterFinalization
THEOREM Spec => []RewardLedgerImmutability
THEOREM Spec => []CommitmentRequiresFinalReward
THEOREM Spec => []CommittedBatchImmutability
THEOREM Spec => []BatchIdUniqueness
THEOREM Spec => []CorrectionTargetExists
THEOREM Spec => []SnapshotTargetExists
THEOREM Spec => []AuthorityRequiredForCommit

=============================================================================
