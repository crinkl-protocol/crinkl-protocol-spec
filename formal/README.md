# Formal Verification

TLA+ specifications for model checking protocol invariants.

## Files

- `CrinklProtocol.tla` — Main specification

## Running the Model Checker

### Prerequisites

Install TLA+ Toolbox or use CLI tools:

```bash
# Download tla2tools.jar
wget https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar
```

### Model Configuration

Create `CrinklProtocol.cfg`:

```
SPECIFICATION Spec

CONSTANTS
    ReceiptIds = {r1, r2, r3}
    WalletAddresses = {w1, w2}
    MaxEvents = 20

INVARIANTS
    TypeInvariant
    NoRewardWithoutVerification
    FinalRewardRequiresHardVerification
    CorrectionsAfterFinalization
    RewardLedgerImmutability
```

### Run TLC

```bash
java -jar tla2tools.jar -config CrinklProtocol.cfg CrinklProtocol.tla
```

## Verified Invariants

| Invariant | Description |
|-----------|-------------|
| `TypeInvariant` | All variables maintain correct types |
| `NoRewardWithoutVerification` | Rewards only issued after verification |
| `FinalRewardRequiresHardVerification` | Final rewards require hard verification |
| `CorrectionsAfterFinalization` | Corrections only possible post-finalization |
| `RewardLedgerImmutability` | Rewards never change state backwards (immutable) |

## State Space

With 3 receipts and 20 max events, TLC explores ~50,000 states.

Increasing to 5 receipts / 30 events: ~2M states (~5 min on modern hardware).

## Extending the Spec

To add new invariants:

1. Define predicate in `CrinklProtocol.tla`
2. Add to `INVARIANTS` in `.cfg` file
3. Re-run TLC

To model new features:

1. Add actions to `Next` relation
2. Update type definitions if needed
3. Verify existing invariants still hold
