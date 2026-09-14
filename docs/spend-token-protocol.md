---
type: media
title: The Spend Token Protocol
date: September 2026
audience: protocol, investors, businesses
identity: crinkl-whitepaper-programmable-commerce.md
document_id: spend-token-protocol
revision: 7
subtitle: User-Owned, Programmable Commerce
collection: whitepapers
document_type: whitepaper
source_filename: Crinkl_Whitepaper_Programmable_Commerce_Rewrite_3.md
---

# CRINKL PROTOCOL

# The Spend Token Protocol

## User-Owned, Programmable Commerce

**PriceChain Labs**  
**Whitepaper draft, September 2026**

> **Architecture status:** This paper describes Crinkl's intended completed protocol and market architecture. An earlier alpha completed an end-to-end reference run and is preserved as a historical record. The non-production substrate now demonstrates two materially different positive conditions—a single-product purchase and four distinct Campaign-influenced purchases in 45 days—through private proof, their own frozen Solana Devnet verifiers, replay rejection and isolated exactly-once Platform Outcomes. This is not a generic history-query engine. Authenticated buyer-state evaluation in a production runtime, complete-history or absence claims, external escrow and controlled-experiment support remain unproven or separate initiatives. Multi-issuer operation and distributed authority are staged network transitions and are not yet available.

---

## Contents

00. Abstract  
01. Commerce Is Already Programmatic  
02. Changing What a Purchase Produces  
03. Spend Tokens  
04. Programmable Commerce  
05. Credible Facts Without Public Histories  
06. Building the Initial Network  
07. From Proof Supply to Business Demand  
08. Product-Led Progressive Ownership  
09. What the Network Must Prove  
10. Conclusion

---

## 00. Abstract

Commerce is already programmatic. Retail media networks match purchase histories to audience segments and trigger media spend. Card-linked platforms detect a qualifying transaction and bill the merchant for the reward. Receipt platforms run pay-per-sale offers against item-level purchase data. Retailer loyalty systems match ad exposure to store sales. Commerce runs on automated if-then programs, and purchase data is what they run on.

Money is already programmable. Stablecoins move under smart-contract logic at scale: escrowed funds release when a delivery confirms, payouts split among parties in a single transaction, value moves the moment a condition is met.

The two have never been connected: our reviewed research found no rail that settles brand marketing spend against a proven buyer state. Programmatic commerce automated the decision, not the money: the program chooses who sees an offer and reports what happened, and payment follows on separate rails: a card charged at a billing threshold, a monthly invoice against redemptions, agency terms that stretch past ninety days. Fast or slow, the structure is the same. In programmatic commerce, a met condition produces a report, and money follows it. In programmable commerce, money can move only after a condition is proven, and it moves under rules committed before the proof existed.

And the person whose purchases power all of it stands outside both. The buyer creates the activity, but cannot direct or repeatedly benefit from the commerce state that activity produces.

Crinkl connects them — and begins with the participant both systems left out.

A buyer submits evidence of a purchase to a Verification Issuer. The issuer evaluates the evidence under its verification rules and, if it qualifies, signs a Spend Token: a user-held attestation about the purchase. Raw evidence remains inside the issuer's private verification boundary. The buyer receives a Spend Token that can omit identity, then authorizes its use for specific commerce conditions.

**The purchase becomes buyer-controlled commerce state.**

That state can prove a limited condition without exposing the history behind it. A buyer may prove they are a recent category buyer, a repeat buyer, a lapsed buyer, a competitor buyer, or new to a brand, each answer scoped to the rules of a particular opportunity.

Businesses program value against those answers. A campaign defines the qualifying condition, intervention, reward, outcome, measurement, and settlement terms, committed before the result is known. A buyer authorizes the required proof. If a resulting purchase is required, a new Spend Token establishes the conversion. The condition is proven; acceptance, outcome, and settlement then follow as separate steps under terms committed in advance. A campaign is a conditional payment whose condition is a proven buyer state.

**Proof moves. The profile does not.**

Proof creates business value through what it makes possible: purchasing activity can qualify its holder across merchants, brands, applications, and agents, while the buyer authorizes each use and the underlying history remains undisclosed.

Crinkl begins with a familiar rewards product because participation makes the protocol useful. A finite Data Density Burn Reserve subsidizes the initial construction of verified commerce state. Users may choose immediate value in bitcoin or elect $CRINKL, the network's native asset. As useful density develops, businesses replace protocol subsidy by funding qualified actions and verified outcomes.

The progression is deliberate:

> **Contributor → proof holder → market participant → owner**

The product must create value before ownership can carry meaning. Crinkl's thesis is that ordinary commerce participation can become a quiet on-ramp to a user-owned, programmable commerce network.

---

## 01. Commerce Is Already Programmatic

Every purchase leaves evidence: a paper receipt, a digital receipt, a merchant order, a loyalty entry, a payment record, a point-of-sale event.

Intermediaries make that evidence economically useful by organizing it. Retail media networks build purchase-based audiences, activate media, and connect exposure to sales. Loyalty systems recognize repeat behavior. Payment and advertising systems match pseudonymous identifiers across databases. Data providers add inferred characteristics and intent. This infrastructure delivers real utility (targeting, activation, measurement, and insight at scale), and businesses pay for all of it.

But each program runs only where its operator's data reaches.

> **Commerce becomes programmatic only inside the systems that collect, match, and control the underlying data.**

A retailer can make its own transaction history useful. A loyalty platform can make its enrolled history useful. A payment network can make its payment view useful. Each can extend that reach through advertising platforms, clean rooms, and identity matching, but the extension is always negotiated between systems, and the buyer remains the subject being activated and measured, never a participant in the program.

The arrangement has a fixed shape: the buyer's activity creates the commercial signal, the intermediary decides how the signal can be used, and the brand pays the intermediary for access to it. The buyer may collect a discount at the moment of purchase, while the continuing economic use of that purchase stays inside the intermediary's system.

What the buyer loses is not a payment. It is a position.

A coffee purchase can establish that someone participates in the category. Several purchases can establish frequency. The absence of a later purchase can establish lapse. A purchase after an intervention can establish conversion. These states are what businesses actually pay to reach. Today, each is usable only by the intermediary that happens to hold the relevant record.

Yet no intermediary holds them all. The same person buys coffee from a national chain, orders from an independent brand, swipes a card at a local cafe, and picks up an energy drink at the convenience store. Each system sees its fragment. Only the buyer stands on every side of those boundaries, and only the buyer has access to evidence across all of them.

Buyers already supply that evidence when it pays to do so. Receipt rewards operate at mass-market scale: the receipt-rewards platform Fetch alone reported 12.5 million monthly active users scanning billions of receipts in 2025. Crinkl begins with that familiar action — submit evidence of a purchase, receive immediate value — and changes what the action leaves behind: verified commerce state the buyer retains.

The central question follows:

> **Can real-world purchasing activity become programmable while the resulting commerce state stays under the buyer's control?**

Answering it requires changing what a purchase produces.

---

## 02. Changing What a Purchase Produces

In a conventional data system, a purchase becomes another entry in a platform-controlled history. The record may improve targeting, attribution, forecasting, or audience construction, but the enduring commercial asset stays with the system that assembled it.

Crinkl changes the output:

> **Purchase evidence → buyer-controlled commerce state**

A verified purchase keeps creating value for the buyer after the initial receipt reward. A verified coffee purchase earns its reward at submission. Later, it can privately qualify its holder for an offer from another coffee brand. If the buyer accepts and purchases, that transaction becomes new commerce state, which can qualify the buyer for the next opportunity, or prove a campaign outcome. The buyer retains this state throughout and authorizes each specific use.

That reorders the transaction between buyer and business. Today, a brand relies on an intermediary to define the audience, provide access, and report what happened, using data the intermediary controls. With Crinkl, the business defines the condition and outcome it will fund, the buyer proves qualification, and the business receives the scoped answer and the measurement it needs. The purchase history never reaches the brand, the campaign, or the chain.

The result is reusable economic capability:

- Purchasing activity qualifies the buyer for relevant opportunities.
- The same underlying fact can support different authorized uses.
- Buyer state spans merchants through scoped proofs rather than a global identity-linked purchase repository.
- A later verified purchase establishes whether the intended outcome occurred.
- Applications compete to create value from shared proof standards rather than rebuilding closed histories.

This is what **user-owned spending** means in the protocol: the buyer receives and retains a reusable commerce artifact created from their own evidence, and decides when it answers a commerce condition.

The protocol object that carries this capability is the Spend Token.

---

## 03. Spend Tokens

**A Spend Token is a signed attestation about a specific purchase.**

A buyer submits purchase evidence to a Verification Issuer. The issuer evaluates the merchant, transaction details, amounts, evidence integrity, duplication signals, and any required product evidence under its verification rules. Only qualifying evidence produces a signed Spend Token.

The token can record facts such as where the purchase occurred, when it occurred, the transaction amount, the issuing Verification Issuer, and the verification version applied. Naming the issuer and version makes every token traceable to the rules that produced it; as independent issuers join the network, policies and accountability can expand without changing tokens already issued.

Just as important is what the token leaves out.

Product evidence stays inside the issuer's private boundary. An issuer can normalize and evaluate merchant, brand, category, SKU, and line-item detail without placing any of it in the token; campaigns declare the product conditions they accept and receive only the scoped proof required. The token can omit names, email addresses, phone numbers, account identifiers, and public wallet addresses: it describes the spend, not the person. And the raw evidence itself remains inside the issuer's verification boundary for its declared purpose and retention period. The buyer receives the attestation; campaigns, brands, and validators receive no receipt. The protocol's on-chain program verifies the supported proof and its public bindings without receiving the receipt or line items.

What the token asserts is correspondingly precise: a named issuer evaluated evidence under an identified verification version and signed the result. Its credibility rests on the evidence process, issuer accountability, key history, token status, and the rules governing later proof acceptance. Each admitted purchase must also be unique: replay and duplicate controls prevent the same evidence from inflating commerce or claiming the same benefit twice, and commitments and nullifiers enforce this without publishing the receipt.

Spend Tokens accumulate into a user-held **spend stream**: an append-only history of attestations whose later uses can be proven selectively. Recovery of the spend stream is not intended to depend on a single device: the buyer can present a previously issued attestation for re-signature, so recovery need not require the issuer to retain the buyer's complete purchase history. Accepted Spend Tokens can also be aggregated within a declared scope as **Verified GMV**: the gross merchandise value represented by qualifying purchase evidence under defined verification and acceptance rules.

When an application must route value, it can use a blinded wallet or account commitment rather than placing identity inside the token. A linked Reward Commitment can establish that value tied to the token was committed for the buyer's recipient scope. Where stronger assurance is required, the token can be bound to a per-token holder key, so that using it requires a fresh proof of holder control.

**A Spend Token preserves an attested purchase as reusable commerce state.**

Five properties determine what a purchase record is worth to any program that runs on it: how personal it is, how rich, how fresh, whether it can be verified, and whether it can be used again. A Spend Token is the same purchase as a receipt, scored differently on all five.

| | Receipt in a drawer | Receipt scanned to a rewards platform | Card-linked record | Retail media record | Spend Token |
|---|---|---|---|---|---|
| **Personal** | One person's purchase, held by them | One person's purchase, held by the platform | One person's purchase, held by the bank or its partner | One person's purchase, held by the retailer | One person's purchase, held by the buyer |
| **Rich** | Item level | Item level | Merchant, amount, time | Item level, at that retailer only | Item level, kept inside the issuer boundary and proven on demand |
| **Fresh** | Until it fades | At upload | Near real time, passively | At checkout, passively, at that retailer | At submission through any ingress; verified once, current every time it is used |
| **Verifiable** | Self-reported | Asserted by the platform; not independently checkable | Attested by the bank | Asserted by the retailer's closed-loop report; not independently checkable | Attested by a named issuer under a named rule version; every acceptance publicly re-verifiable |
| **Reusable** | No | By the platform, on its terms | By the bank or partner, within its program | By the retailer's media network, inside the retailer's data boundary | By the buyer, across any campaign, without the record moving |

Campaigns and applications apply their own economic rules to that state. Separating the purchase fact from each later use lets one purchase support different authorized opportunities without rewriting the underlying event. The order is fundamental:

1. The purchase is evaluated and attested.
2. The attestation becomes eligible for use under applicable acceptance rules.
3. The buyer authorizes a proof derived from the attestation.
4. A campaign or application acts on the proof according to its policy.

That separation turns a purchase record into a general primitive. The Spend Token supplies the fact. A condition gives the fact context. A campaign supplies the action and value.

---

## 04. Programmable Commerce

Commerce becomes programmable when the buyer holds verified commerce state and value can settle against it. A business declares a condition; the buyer authorizes a scoped proof; the proof establishes that the condition was satisfied. Acceptance of the proof, the campaign outcome, and the movement of value follow as separate steps, each under rules committed in advance. The underlying purchase history never transfers.

> **Proof supply → state qualification → action routing → verified outcome → settlement → learning**

### Scoped buyer state

A purchase has limited meaning by itself. Its utility increases when it can establish a relationship across merchant, category, market, and time.

A campaign might ask whether a buyer:

- Purchased within a category during the prior 30 days
- Purchased a particular brand more than once
- Purchased a competitor but not the campaign brand
- Previously purchased the campaign brand but has since lapsed
- Is new to the campaign brand within a defined lookback window
- Purchased after receiving a defined treatment

Each condition is contextual: a role that purchase facts play inside a declared rule. The same buyer can satisfy different conditions in different contexts while revealing only the answer required for each one. This replaces the privately asserted audience label, a platform's claim that a buyer belongs to a segment, with buyer-held state whose scoped use is publicly verifiable.

Product-level conditions are evaluated within the accepted issuer's declared evidence scope, and new-to-brand, lapse, and competitive-exclusion conditions use a defined observation window. A broader absence claim requires coverage sufficient to support it. Where coverage cannot support the claim, the condition returns no answer rather than a guess: an absence that cannot be established is indeterminate, not assumed.

The condition is frozen before action begins. It identifies the eligible evidence, time window, market scope, treatment, outcome, attribution period, reward, and settlement terms. A proof then answers whether the buyer's Spend Tokens satisfy that condition.

> **Buyer-product state remains private. Proof that it satisfies a declared condition can be verified publicly.**

### From qualification to outcome

Consider one campaign end to end:

1. A buyer holds a verified Starbucks purchase from the prior 30 days.
2. Raposa Coffee defines a campaign for recent coffee buyers who have not purchased Raposa during a specified lookback period.
3. The buyer's device or authorized service evaluates the condition against the buyer's Spend Tokens.
4. The buyer returns only the qualification proof; the Starbucks receipt and unrelated history remain private.
5. Raposa routes the declared offer.
6. If the buyer purchases Raposa Coffee, a new Spend Token establishes the conversion.
7. The campaign settles under its precommitted terms.

Now add the money. Raposa commits its budget and an all-in price per verified conversion before the campaign runs, and declares the buyer's reward, say five dollars on a verified first purchase. The buyer sees the declared reward. Raposa sees its declared price. The difference funds verification, proof, and settlement. Every term is fixed before the first proof is generated. Raposa is not buying impressions that might become customers; it is buying customers, at a price it set, against proof it can verify.

The Raposa purchase then becomes input to the next authorized condition, extending its value beyond the first reward. This is the economic importance of reuse: purchasing activity repeatedly qualifies the buyer for opportunities while the underlying history stays under the buyer's control. And buyer state is maintained independently of any one campaign: many campaigns with different products, windows, and thresholds evaluate the same buyer-held state at their own committed cutoffs. No campaign constructs its own copy of the buyer's history.

### Measurement and learning

Programmability includes measurement. A verified conversion establishes what happened; an incrementality test estimates what the campaign caused. A campaign therefore defines treatment and control assignment, an observation window, equal outcome collection, and a counterfactual before action begins. A campaign that runs without a holdout declares that in its committed terms, and its result is reported as observed conversion, not lift. Spend Tokens establish the observed purchases; the experiment establishes causal lift.

Experiment rights are part of the campaign commitment: holdout and measurement terms are declared in the escrowed terms before launch rather than negotiated after outcomes exist. And Crinkl publishes the specification a condition is evaluated against (variables, diagnostics, and validation results) so acceptance rules can be inspected rather than trusted. Validation results confirm that a test ran as declared; the lift a campaign measures is delivered to the brand that funded it and is not published.

Across completed campaigns, aggregate results can reveal which declared buyer states respond, which rewards clear, and where verified outcomes occur. This is commerce intelligence produced from scoped qualifications and outcomes rather than a centralized identity-linked purchase repository. Aggregate comparability requires declared test types: a spend-adjustment test and a true holdout are different evidence and are not pooled as if they were the same.

Intelligence may recommend a condition or optimize an offer. Deterministic campaign rules still decide who qualifies and what settles.

> **Intelligence proposes. Proof decides.**

### Applications and agents

The same machine-readable conditions serve consumer applications, brand interfaces, and authorized AI agents. With scoped authority, an agent can discover relevant campaigns, request the minimum required proof, compare opportunities, or execute an authorized purchase while the buyer retains the underlying history. Agents are one interface to the network: standardized commerce facts, permissions, conditions, and settlement rules give them reliable boundaries for discovery and execution.

The asymmetry is deliberate. A buyer's own agent, acting under the buyer's authorization, can read the full spend stream and use it to weigh opportunities; a campaign never receives more than the scoped answer. The spend stream is commerce memory the buyer carries between agents and applications, rather than memory that any one of them holds.

The capabilities in this section are at different stages of maturity; the architecture status note at the head of this paper states what has been demonstrated. Protocol semantics, platform implementation, on-chain verification support, runtime authority, and settlement behavior will reach general availability at different rates.

Programmable commerce therefore depends on something more difficult than expressive campaign rules. Businesses must be able to rely on the facts against which value is routed and settled.

---

## 05. Credible Facts Without Public Histories

Commerce begins outside the protocol. A purchase occurs at a store, through an application, inside a merchant system, or through a payment flow. Crinkl's trust path begins at the verification boundary, where an issuer evaluates private purchase evidence under a declared policy.

The protocol separates evidence review, user authorization, proof acceptance, and settlement so that each source of authority can be identified, constrained, audited, and withdrawn.

### Evidence, attestation, proof, and acceptance

The trust path has distinct stages:

1. **The buyer supplies evidence.** A receipt or merchant-origin record represents an event that occurred outside the protocol.
2. **A verification issuer evaluates it.** The issuer reads the private evidence under a declared policy and signs a Spend Token.
3. **The buyer authorizes later use.** The token remains in the buyer's spend stream, and the buyer authorizes scoped proofs.
4. **The on-chain program evaluates public claims.** The protocol's Solana program verifies the proof itself, rule and campaign bindings, issuer authority, key validity, token status, and uniqueness or nullifier rules. These conditions are deterministic; acceptance is program execution. The chain records the scoped answer: it never receives the buyer's receipts, identity, or unrelated product relationships.
5. **Validators probe what the chain cannot observe.** The program can verify mathematics and bindings; it cannot verify that the evidence behind an attestation was real. Validators today verify reported commerce at the aggregate level — attestation counts and Verified GMV — and receive no receipts. The role is designed to expand into adversarial probing: submitting deliberate duplicates and invalid evidence, checking attestation construction, reconciling merchant-side aggregates against accepted attestations, and investigating anomalous throughput.
6. **Applications and settlement act on the accepted result.** Campaign commitments prevent the rule or proof requirement from being rewritten after the outcome is known. Public acceptance of a proof is not itself a campaign outcome, a reward, or a settlement; those follow separately under terms committed before the result was known.

Verification is private because the evidence must be read. Acceptance is public because it executes on a public chain under rules anyone can re-verify.

> **Verification is private. Acceptance is public.**

On-chain acceptance establishes that a claim was evaluated according to declared protocol rules; the program's execution record is the acceptance record. The issuer remains accountable for the quality of the evidence process behind it, which requires resolvable verification rules and versions, issuer key history, attestation status, duplicate resistance, and the ability for applications and network governance to reject an issuer whose output loses credibility.

Authority is divided across the path:

- The issuer reads evidence and signs attestations under its verification rules.
- The on-chain program accepts proofs under public rules while raw receipts remain inside the verification boundary.
- Validators test issuer behavior against the reality the chain cannot observe.
- A business funds an outcome and receives the scoped qualification and measurement it needs.
- An application routes an opportunity against rules committed before results are observed.
- A buyer authorizes each proof, while replay controls bind each evidence item to its permitted uses.

The controls above are hygiene. What keeps the boundary honest is that fraud has nowhere to sell. A Spend Token is worth something only when a campaign later accepts a proof drawn from it, and a campaign pays only for a verified outcome: a new attested purchase of the campaign brand, which the brand can check against its own orders inside the dispute window. A fabricated token has no buyer behind it. Offers routed to it do not convert, brands bought against it do not return, and the value that a real token accumulates through acceptance never accrues to an invented one. Weak evidence degrades campaign performance, and with it confidence in the issuer that admitted it. Fraud cannot compound, because nothing in the network pays for a token twice and nothing pays for it at all until it converts.

What remains exposed is the reward paid at admission, before any campaign has accepted anything. That exposure is divided by the user's election. A bitcoin-elected reward is paid by the issuer that admitted the receipt, from its own funds — today, PriceChain Labs — so a false admission is an immediate cash loss to the issuer that made it. A $CRINKL-elected reward is paid by the protocol from the Data Density Burn Reserve, and the reserve's protection is admission: accepted commerce advances the reserve's schedule only after validators have proven it. Today PriceChain Labs is the only issuer and validators verify at the aggregate level, so the reserve pays only for the reference issuer's own admissions, and that issuer carries the bitcoin cost of its own mistakes. Admitting an independent issuer is a staged transition, and an independent issuer's output will not draw the reserve until it is subject to the validator probing described above.

The protocol's trust model is explicit:

> **Crinkl defines separate authority for evidence review, authorization, on-chain acceptance, adversarial probing, applications, and settlement, and makes accepted commerce claims accountable to issuer rules, public acceptance rules, and economic use.**

Credible facts are necessary but not sufficient. They become commercially useful only when the network holds enough commerce state across buyers, merchants, categories, markets, and time.

---

## 06. Building the Initial Network

Every proof network faces the same cold start:

> **No proof density → limited business utility → limited business demand**

Crinkl's answer starts from what already exists. Buyers already hold the evidence; immediate value gives them a reason to contribute it before business demand arrives. Crinkl begins with a product behavior people already understand:

> **Scan a receipt. Receive a reward.**

The familiar product creates the first proof supply. The protocol economy provides the temporary bridge to later business demand.

The scan is the first ingress, not the only one. Purchase evidence can arrive as a paper receipt, a digital or email receipt, a card-linked transaction record, or a merchant-origin record from commerce platforms and point of sale. Card-linked records can provide passive, near-complete merchant-level coverage; receipts and merchant records provide item-level truth where a condition requires it. The evidence type determines what a Spend Token can attest, not whether the buyer can participate.

### The Data Density Burn Reserve

Crinkl has a fixed total supply of **100,000,000 $CRINKL**. A finite **70,000,000 $CRINKL Data Density Burn Reserve** supports the initial construction of verified commerce state.

The reserve subsidizes early participation while the network builds enough density for businesses to fund continued activity. It receives no inflationary refill and depletes against verified commerce rather than time.

> **The reserve buys initial proof supply. It is designed to end.**

The reserve depletes on a published curve that reads dollars of verified commerce. Only one kind of dollar enters that measure: the value of proven purchases. Settled campaign revenue does not move the curve. Each step along the curve releases a tranche; users who elect $CRINKL are paid from it, and the remainder is burned. The reward each receipt earns is the issuer's policy. The reference issuer's policy is intended to prioritize useful coverage (recurring evidence across relevant buyers, merchants, categories, markets, and time) because commercial utility grows from the depth and relevance of coverage rather than volume alone, and campaign-funded activity progressively assumes coverage funding where demand exists. The full schedule, constants, and allocation are specified in the Data-Density Reserve tokenomics paper.

Early rewards create enough state to prove broad conditions. As coverage improves, the network can support more precise states: frequency, lapse, category participation, competitive relationships, market context, and verified conversion.

### Immediate utility and settlement choice

Users elect how eligible native rewards settle.

- A user who chooses **bitcoin** receives immediate value in a familiar external asset, paid by the issuer that admitted the receipt.
- A user who chooses **$CRINKL** elects participation in the network's native economy, paid by the protocol from the reserve.

When an eligible user chooses bitcoin, the corresponding $CRINKL allocation becomes residual supply designated for burn under the reserve design. The reserve funds participation while retiring unused subsidy.

Bitcoin and $CRINKL perform different jobs. Bitcoin makes the product useful before a user understands or wants ownership. $CRINKL gives a participant the option to hold the native economic asset after the product has demonstrated value.

This is the beginning of progressive ownership — and its continuation is not guaranteed. Business demand must replace protocol subsidy; otherwise Crinkl remains a finite rewards program.

> **The reserve can fund the first useful density. Businesses must fund what that density makes possible.**

---

## 07. From Proof Supply to Business Demand

Businesses already pay for purchase-based targeting, activation, sales measurement, and consumer insight. Crinkl's opportunity is to build the rail this requires: businesses funding actions and outcomes against buyer-controlled commerce state, across intermediary boundaries, with settlement that follows the proof. Our reviewed research found no such rail in operation.

The nearest businesses start from the same input. Fetch and Ibotta take the same receipt from tens of millions of shoppers and sell brands a panel report and a redemption count. The panel is richer per record than anything a campaign receives from Crinkl, and it is correlational: it shows who bought, inside the platform's walls, after the fact. From the same receipt, Crinkl produces a buyer-held proof that qualifies across every merchant the buyer shops, a campaign whose holdout and measurement terms are fixed before launch, and settlement that runs on the same rail as the outcome. Narrower per use, causal by construction, and reaching across the boundary every panel stops at.

Funded activation is not the only demand channel. For an emerging brand, verified trial and repeat purchasing is itself a commercial asset: evidence that buyers tried a product and returned is what a retailer weighs when deciding distribution. A campaign can therefore produce two results a business values: the activated buyer, and the verified evidence the brand carries into that decision.

A campaign defines:

- The qualifying buyer condition
- The eligible market and time period
- The action or treatment
- The reward and budget
- The required outcome
- The measurement method
- The settlement and dispute rules

The buyer authorizes a proof of the required condition. The campaign receives the scoped answer needed to act, while the full purchase history remains with the buyer. This changes what a business buys:

> **Access to an intermediary-defined audience → funded action against a buyer-proven condition**

Crinkl reorganizes intermediation rather than merely removing it. PriceChain Labs, the company developing Crinkl, currently forms and operates parts of the initial network, while the protocol defines verification, authorization, on-chain acceptance, adversarial probing, applications, and settlement as separable functions with shared conformance rules. This creates a path for independent issuers, validators, applications, and settlement services to participate as the network develops. Role separation makes authority boundaries explicit, and operational control can become progressively distributed without changing the underlying commerce facts. Institutional independence develops as independent participants actually assume those roles.

### Campaign funding and settlement

Campaign value is committed before routing. A business funds campaigns in stablecoin (USDC), held in escrow bound to the declared terms; no position in a network asset is required to buy outcomes. A business may also elect to fund in $CRINKL.

If a campaign pays for qualification or exposure, settlement follows the applicable proof and policy. If it pays for conversion, a later accepted Spend Token must establish the required purchase outcome. On-chain acceptance and a dispute period can precede final settlement. As campaigns settle, campaign escrow buys $CRINKL on the market and burns it, outside the reserve.

The campaign supplies the rule and budget. The buyer supplies authorized proof. The on-chain program establishes acceptance. Settlement closes the exchange. And because outcome verification and settlement run on the same rail, campaign measurement carries no external reporting lag and no dependency on a third party's settlement data.

### Demand replaces subsidy

The network's intended economic loop:

> **Rewards → proof density → programmable conditions → business-funded actions → verified outcomes → new proof**

Each cycle creates more useful state for the buyer and new intelligence for the business. A brand that funds a campaign buys two things: the verified conversions it pays for, and causal knowledge of its own buyers — which of its declared states responded, at which reward, in which markets, measured against a holdout fixed before launch, across every merchant those buyers shop. Today a brand gets a retailer's closed-loop report inside that retailer's walls, or a panel that shows who bought after the fact; neither is causal and neither crosses the boundary. The knowledge a brand takes from a campaign is the brand's to keep and to combine with whatever else it collects, and it is a reason to fund the next campaign independent of the conversions the last one produced. The purchase closes the current campaign and becomes input to future authorized opportunities.

Aggregate outcomes are where the network's own asset forms. Over repeated campaigns, PriceChain Labs learns which scoped buyer states respond, at which reward, in which markets, from aggregate results and declared conditions. What is public and what is private about a campaign is fixed. Each campaign's acceptance rules, test specification, and validation results are published, so anyone can confirm that a campaign was evaluated under the rules it declared and that its test ran as specified. The measured lift is delivered to the brand that funded the campaign and is not published. So no brand sees another brand's results, a campaign tool or agency sees only the campaigns it built, and the operator sees every campaign that has run. The picture across campaigns is therefore the operator's alone: the refined product of every campaign that has run, and what makes the next campaign's condition and price better than a guess. The public view of the network aggregates enough to show its reach without publishing that picture, and individual histories remain inside their respective trust boundaries throughout.

The same discipline applies to Verified GMV as a reference measure. On-chain finality makes the number trustworthy; market acceptance makes it a currency. Verified GMV becomes a reference standard when businesses, sellers, and analysts treat it as the number that settles questions, a status the network must earn, not declare.

The network becomes commercially useful when Crinkl can reach useful buyer states, route actions, verify outcomes, and measure results with competitive speed, cost, and reliability. The business test is direct:

> **Can buyer-controlled commerce state produce a valuable action or outcome that a business can purchase effectively?**

Paid demand answers it. And when businesses fund the loop, the buyer's role expands: from supplying evidence for a protocol reward to authorizing commerce state inside a market and receiving value when that state produces an outcome.

The contributor becomes a market participant.

---

## 08. Product-Led Progressive Ownership

Crypto has often introduced ownership as an initial obligation: acquire the asset, understand the network, accept volatility, and hope useful products follow.

Crinkl reverses that sequence.

The product begins with immediate, legible value. A buyer scans a receipt and receives a reward. Beneath that familiar interaction, the purchase becomes a Spend Token the buyer can reuse. Campaigns make that state economically useful. Business demand demonstrates that the network has value beyond its own subsidy.

Only then does ownership become meaningful.

The user progresses through four roles:

**Contributor.** The user supplies evidence of ordinary commerce and receives immediate product utility. No belief in the protocol is required.

**Proof holder.** The resulting Spend Token remains available to the user. The purchase can privately establish future conditions instead of ending as a one-time receipt reward.

**Market participant.** The user authorizes proofs, receives relevant opportunities, produces verified outcomes, and captures value from repeated use of their purchasing activity.

**Owner.** After experiencing the network's utility, the user may elect $CRINKL rather than bitcoin and hold part of the native economy their participation helps make useful.

> **The product proves its value first. Ownership follows demonstrated participation.**

This is product-led progressive ownership.

Settlement choice makes ownership voluntary. A user who prefers immediate utility can continue choosing bitcoin. A user who sees long-term value in the network can choose $CRINKL. Choice distinguishes a reward recipient from a voluntary owner.

> **Forced token rewards manufacture token holders. Choice reveals owners.**

$CRINKL does three jobs in the native economy: it pays users who elect it over bitcoin, it is bought on the market and burned by campaign escrow as campaigns settle, and it carries scarcity through a fixed supply that only falls — burned as users take bitcoin instead and burned as campaigns settle. Nothing in the network requires anyone to hold it. Spend Token validity remains a separate verification question. The asset's relevance must come from actual use and demand.

Progressive ownership also requires progressive authority. The protocol defines verification, authorization, on-chain acceptance, adversarial probing, applications, settlement, and governance as separable roles. Authority becomes progressively distributed as independent participants assume those roles while users continue to authorize proof use.

The progression is economic and institutional:

> **Useful product → buyer-controlled state → market participation → voluntary ownership → distributed authority**

The protocol and product must earn this progression through demonstrated utility and demand.

---

## 09. What the Network Must Prove

Crinkl's architecture establishes a capability. The product and market must prove that the capability is reliable, private, useful, and open in practice.

### Evidence integrity

Commerce evidence can be altered, duplicated, fabricated, or replayed. Crinkl answers with layered controls: evidence checks, declared issuer policies, duplicate detection, commitments and nullifiers, attestation status, key history, public acceptance rules, audits, bounded rewards, and disputes. The on-chain program confirms public proof and acceptance conditions; validators adversarially probe the evidence boundary; issuers remain accountable for the private evidence decisions that created each Spend Token.

Identity-free state raises a second question: how a campaign counts buyers without counting one person twice, or one operator as many people. Nullifiers prevent one purchase from qualifying twice. Counting distinct buyers over time uses pairwise, campaign-scoped identifiers: a buyer presents a stable identifier to one campaign and an unrelated identifier to another, so a campaign can measure new, repeat, and lapsed state within its own scope while no identifier links a buyer across campaigns or back to a person. What that leaves is one operator presenting many buyers, and that is the case the reward economics and validator probing in §05 exist to make expensive and detectable rather than the case any identifier could rule out.

### Privacy through separation and deletion

Under Crinkl's design, raw purchase evidence is confined to the Verification Issuer's boundary: the protocol role authorized to inspect the receipt and associated private data. The issuer evaluates it for a declared purpose, retains it for the period stated in its policy, and deletes it on that schedule. Spend Tokens can omit direct identity fields; proofs reveal campaign-scoped answers; the chain, brands, and campaigns receive no raw receipts. This separation sharply limits the information available to other participants and keeps raw purchase histories outside the public protocol. The same separation narrows legal exposure: outside the verification boundary, the network holds no identity-linked purchase histories — there is less to breach, subpoena, or litigate, and what exists is confined to one accountable role with a declared retention clock.

The retention policy is an operational trust commitment. Audits, published retention rules, and issuer accountability make deletion behavior credible, while users and applications can reject issuers whose practices fail that standard.

### Commercial usefulness

Useful density requires repeated coverage within relevant categories, merchants, markets, time periods, and buyer states. Campaigns must also separate observed conversion from causal lift through appropriate experimental design. Businesses will determine whether Crinkl offers sufficient reach, buying simplicity, outcome quality, measurement, speed, and cost to earn sustained demand. That demand must ultimately replace reserve subsidy.

### Open participation

The network becomes meaningfully open as independent issuers, validators, applications, and agents assume operational roles under shared rules. Role separation creates the path; actual participation distributes authority. $CRINKL's economic relevance must likewise arise from useful participation and business demand.

The operating boundary is concise:

> **Buyers originate evidence. Issuers attest under declared policies. Users authorize scoped proofs. The protocol program establishes acceptance under public rules. Validators probe what the chain cannot observe. Businesses fund actions and outcomes. Applications route utility. Markets decide whether the result is valuable.**

---

## 10. Conclusion

Commerce is already programmatic: automated if-then programs run on purchase data inside the systems that collect, match, and control it. Money is already programmable: value moves the moment a condition is met. Crinkl connects the two — and starts with the participant both systems left out. The buyer's activity powers every commerce program, yet the buyer neither controls the resulting commerce state nor shares in its continuing use.

Crinkl changes what a purchase produces.

A verified purchase becomes a user-held Spend Token that the buyer receives, retains, and authorizes for specific uses. The token can establish a scoped condition without disclosing the purchase history behind it. A business defines an action, outcome, reward, and settlement rule against that condition and commits the terms before the result is known. A later verified purchase closes the loop. The condition is proven; acceptance, outcome, and settlement follow as separate steps under terms committed in advance.

**Proof moves. The profile does not.**

The purpose is reuse: letting buyers capture and direct more of the economic value their purchasing activity creates.

A familiar receipt-rewards product creates the initial proof supply. The finite Data Density Burn Reserve subsidizes early density and is designed to end. Businesses must replace subsidy by funding conditions and outcomes that prove commercially useful.

As that happens, the buyer progresses:

> **Contributor → proof holder → market participant → owner**

Bitcoin provides immediate utility. $CRINKL provides optional participation in the native economy. Ownership follows use rather than preceding it.

The protocol defines verification, authorization, on-chain acceptance, adversarial probing, applications, and settlement as separable roles. As independent participants assume those roles, authority becomes progressively distributed while commerce remains programmable and the buyer retains the underlying history. Success depends on evidence quality, privacy, density, measurement, business demand, and the practical openness of the network.

Crinkl's proposition is simple:

> **Real-world spending can become buyer-controlled and programmable. A purchase can create immediate value, reusable commerce state, verified market participation, and, by choice, ownership in the network that participation helps build.**

The receipt is the entrance. The reward makes the entrance useful. The Spend Token preserves what the purchase can become.

---

## Evidence and scope notes

1. Walmart Connect describes using first-party online and in-store shopping data for insights, audience targeting, activation, and closed-loop sales measurement: <https://www.walmartconnect.com/about> and <https://www.walmartconnect.com/resources/articles/2026/expanding-access-to-walmart-first-party-data-across-leading-platforms>.
2. Kroger Precision Marketing describes purchase-based audiences built from loyalty data and sold through activation, measurement, and insight products: <https://www.krogerprecisionmarketing.com/faqs/>.
3. Unified ID 2.0 documentation describes normalizing and hashing email addresses or phone numbers so pseudonymous identifiers can be matched and used for targeted advertising: <https://unifiedid.com/docs/ref-info/ref-how-uid-is-created>.
4. Cardlytics describes purchase-based offers delivered through bank and fintech channels, with advertisers billed for incentives based on actual redemptions: <https://www.cardlytics.com/>.
5. Fetch reported 12.5 million monthly active users and billions of scanned receipts in 2025: <https://business.fetch.com/newsroom/fetch-reports-strong-momentum-for-2025>.
6. Ibotta reports consumer rewards through receipt upload, account linking, and publisher integrations. Its first-quarter 2025 filing reported 17.1 million redeemers and 82.8 million redemptions: <https://investors.ibotta.com/sec-filings/all-sec-filings/content/0001628280-25-025593/0001628280-25-025593.pdf>.
7. Shopify's Shop Campaigns is the nearest existing rail in the research reviewed for this paper. Shopify's documentation describes a brand-set maximum customer acquisition cost, targeting of new and lapsed customers, and payment only for successful acquisitions: <https://help.shopify.com/en/manual/online-sales-channels/shop/shop-campaigns/understanding-campaigns>. Our analysis: the buyer state is asserted by Shopify from its own network data rather than independently provable, its reach ends at Shopify's data boundary, and settlement follows Shopify's attribution report.
8. Raposa Coffee is used as an illustrative example of a crypto-native consumer brand; the scenarios in this paper are hypothetical and do not indicate a partnership or endorsement.
9. The incumbent sources above document representative business models. Crinkl's reach, performance, and economics remain to be demonstrated through product and market use.

---

**Document status:** Whitepaper draft describing Crinkl's intended completed architecture.  
**Protocol:** CRINKL  
**Organization:** PriceChain Labs
