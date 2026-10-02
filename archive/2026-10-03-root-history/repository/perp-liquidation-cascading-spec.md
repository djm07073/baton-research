# Perpetual Liquidation Cascading — Implementation Spec

> Target: a CLOB (central-limit-order-book) perpetual-futures DEX.
> Purpose: define a **deterministic, cascading liquidation engine** that a separate engineer or AI agent can implement without further context.
> Reference systems: **Lighter (LLP)**, **Hyperliquid (HLP)**, **Aster (ALP + insurance fund)** (reverse-engineered from public docs + binary analysis), and **GTE (GTL + InsuranceFund)** — the latter is **open-source Solidity** (Code4rena/Zellic audit repos) and is used as the concrete reference implementation (see Appendix §17).
> **Project decision (default architecture): single mandated backstop vault (Hyperliquid/Lighter-style raw transfer at mark price) for guaranteed absorption, WITH a separate insurance fund as the final loss absorber behind it. No competitive backstop order book (GTE-style) in the default.** See §7 "Recommended architecture". Alternative models (pure GTE competitive-book, pure LP-fused) are kept documented for reference. Everything else (state machine, formulas, ADL) is shared.
>
> Rationale: the single mandated vault **guarantees** the position is absorbed by rule (does not depend on backstop liquidators showing up to quote), which is the property that makes the cascade deterministic and solvent. Keeping the insurance fund **separate** means backstop losses are isolated in a dedicated fund rather than socialized onto market-making LP depositors.

Language note: the normative spec is in English for precision/portability. Inline `NOTE:` lines give rationale.

---

## 0. Glossary & Notation

| Symbol | Meaning |
|---|---|
| `pos_i` | signed position size in market `i` (base units; + long, − short) |
| `S_i` | `|pos_i|` (absolute size) |
| `mark_i` | mark price of market `i` (oracle-derived, §5) |
| `entry_i` | volume-weighted average entry price of `pos_i` |
| `I_i`, `M_i`, `C_i` | initial / maintenance / close-out **margin fractions** for market `i`, with `C_i < M_i < I_i` |
| `collateral` | account's deposited collateral (USDC/USDT), realized PnL included |
| `AV` | **Account Value** (a.k.a. equity) = `collateral + Σ (mark_i − entry_i)·pos_i` |
| `IMR`, `MMR`, `CMR` | Initial / Maintenance / Close-out **Margin Requirement** (currency units) |
| `side` | `+1` for long, `−1` for short |
| `LP` | backstop liquidity pool (HLP/LLP/ALP analogue) |
| `IF` | insurance fund |
| `ZP_i` | zero price of market `i` (§6.3) |

Requirement sums (cross-margin):
```
IMR = Σ S_i · mark_i · I_i
MMR = Σ S_i · mark_i · M_i
CMR = Σ S_i · mark_i · C_i
AV  = collateral + Σ (mark_i − entry_i) · pos_i
```

`NOTE:` This mirrors Lighter's formulation exactly. Hyperliquid/Aster express the same idea with a single maintenance tier + a bankruptcy price; we generalize to 3 tiers and treat "bankruptcy price" as the price where `AV = 0`.

---

## 1. Reference Summary (reverse-engineered)

The three systems implement the **same core waterfall** — *order book → partial liquidation → backstop → ADL* — but differ in (a) who absorbs the loss, (b) how many margin tiers, (c) execution/verifiability model.

| Dimension | Lighter (LLP) | Hyperliquid (HLP) | Aster (ALP) |
|---|---|---|---|
| Margin tiers | 3: initial / maintenance / **close-out** | 2: maintenance + backstop trigger at **2/3 · MMR** | 2: maintenance + **bankruptcy price** |
| Order-book liq. order type | IoC limit @ **zero price**, one position at a time | market order; **20% chunks** if pos > 100k USDC, **30s cooldown** | single large **IoC** order |
| Cancel user's resting orders first | yes | (implicit) | **yes** |
| Backstop absorber | **LLP** (insurance fund + MM), takes over below CMR | **HLP liquidator vault** (sub-strategy of HLP), takes over below 2/3 MMR | **Insurance fund** takes position @ bankruptcy price; **ALP** is MM pool, not the loss-taker |
| Backstop / MM fused? | **Yes** (LLP is both) | **Yes** (HLP is both) | **No** (ALP = MM; IF = loss absorber) → dYdX-like split |
| Loss isolation | **Yes** — per-strategy collateral shards (crypto/FX/RWA) | No — single pooled NAV, PnL socialized | Insurance fund is separate; ALP protected via funding-rate skew |
| Liq fee | up to **1%** of price-improvement → LLP | **none** (retains user's maintenance margin as buffer instead) | "Insurance Clearance Fee" portion → IF |
| ADL trigger | account `AV<0` and LP cannot cover | book + HLP fail and account would go negative | mark hits bankruptcy price before liq completes / IF cannot cover |
| ADL ranking | leverage + unrealized PnL | leverage + unrealized PnL | `PnL% · effLev` (signed formula, §8) |
| Mark price | oracle mark | weighted-median CEX + own book, validators ~3s | funding + basket of spot CEX prices |
| Execution / verifiability | single sequencer + **ZK proofs** | closed binary, on-chain state | on-chain (BNB-chain era) |
| Determinism of *rules* | full (ZK-certified) | full (documented rules) | full (documented rules) |
| MM strategy public? | partial (liq math public, MM hidden) | **no** (proprietary binary) | partial |

**GTE (open-source Solidity) — concrete reference.** GTE runs a **hybrid**: an ERC4626 LP vault **GTL** ("GTE Liquidity Pool") *and* a separate **InsuranceFund**, plus a **dedicated BACKSTOP order book** and **permissioned liquidator roles**. Flow: normal `liquidate()` fills the position against the **STANDARD** book (liquidation fee → InsuranceFund); if that can't clear, `backstopLiquidate()` fills against the **BACKSTOP** book (where GTL provides liquidity) retaining prorated margin as buffer; residual bad debt is covered by `InsuranceFund.claim()`; `deleverage()` (ADL) is the last resort, pairing an underwater *maker* with a profitable *taker* at the **maker's bankruptcy price**. This is the single best implementation blueprint we have because it is real, audited code — see §17 for the file/function map. Key structural choices worth copying: (a) backstop as a *separate book* rather than a raw position transfer; (b) LP vault with **queued withdrawals** (no instant redeem); (c) a hard **solvency invariant** (see §12.9); (d) fee routing that is symmetric (`pay` on surplus, `claim` on shortfall).

**Design takeaways for our implementation**

1. Make the **liquidation waterfall a total, deterministic state machine** (§6). Every unfilled remainder deterministically escalates. This is the property all three rely on and ZK-provability requires.
2. Separate two liquidity layers with **opposite guarantees**: (i) *strategic* order-book MM liquidity that may withdraw (non-deterministic, best-effort), and (ii) *mandatory* backstop that must absorb by rule (deterministic).
3. Choose a backstop model (§7). Fused (HL/Lighter) = strong cascade absorption but depositor tail risk. Split (Aster/dYdX) = risk isolation, needs a separately funded insurance fund.
4. Prefer **loss isolation** (Lighter strategy shards) if listing long-tail/pre-launch markets, so one thin market cannot drain backstop capital of majors.

---

## 2. Scope & Non-Goals

In scope: margin accounting, health classification, mark-price contract, the liquidation state machine (partial → backstop → ADL), both backstop models, ADL selection, determinism/execution requirements, data structures, pseudocode, parameters, invariants, tests.

Out of scope: matching engine internals, funding-rate computation (referenced only), oracle transport/consensus, deposit/withdraw accounting beyond what liquidation touches, front-end.

---

## 3. Account & Margin Model

### 3.1 Margin modes
- **Cross**: all cross positions + cross collateral form one risk unit; shared liquidation price. `margin_available = AV − MMR`.
- **Isolated**: each isolated position is its own risk unit with `AllocatedMargin`; `margin_available = AllocatedMargin − MMR_position`. Cross positions untouched when an isolated position is liquidated, and vice versa.

`NOTE:` Implement isolated positions as internal sub-accounts running the identical state machine with `collateral := AllocatedMargin` and a single-market requirement set.

### 3.2 Margin tiers (size-dependent leverage)
Effective leverage must **compress as position notional grows**. Define per market a tier table:

```
tier = { upper_notional, I, M, C, max_leverage }   // ascending by upper_notional
```
For a position of notional `N = S·mark`, select the tier whose `upper_notional ≥ N` (highest applicable). `I,M,C` come from that tier. For assets with tiers, maintenance leverage used in the liq-price formula is the tier at the *liquidation price*, not entry.

Defaults (majors): `max_leverage` 40x → `I=2.5%`, `M=1.25%`, `C≈0.8·M`. Long-tail: 3x–10x, wider fractions. (HL uses `M = I/2`; keep that relation as default and set `C = k_C·M`, `k_C ∈ [0.5, 0.8]`.)

User-set leverage: `I_i := max(user_fraction, tier_min_fraction)` (user can de-risk, not exceed tier).

---

## 4. Health Classification (per risk unit, evaluated every tick)

Compute `AV, IMR, MMR, CMR` at current marks, then classify:

| State | Condition | Allowed actions |
|---|---|---|
| **HEALTHY** | `AV ≥ IMR` | any |
| **PRE_LIQ** | `IMR > AV ≥ MMR` | only actions that (a) do not increase any `S_i` and (b) do not decrease `AV/IMR` ratio (i.e., reduce-only / add-margin) |
| **PARTIAL_LIQ** | `MMR > AV > CMR` | engine liquidates (partial, §6.4) |
| **BACKSTOP** | `CMR ≥ AV > 0` | engine hands position to backstop (§7) |
| **BANKRUPT** | `AV ≤ 0` | backstop absorbs if capitalized, else ADL (§8) |

`NOTE:` Two-tier reference systems collapse PARTIAL_LIQ and BACKSTOP by triggering backstop at a fixed fraction (HL: `AV < 2/3·MMR`). Our 3-tier model (Lighter-style) gives an explicit "try the book harder" band before the LP must eat it. If you prefer the 2-tier model, set `CMR = (2/3)·MMR` and skip the distinct close-out fraction.

---

## 5. Mark Price Contract (oracle)

Liquidations MUST use `mark_i`, never last trade price. Required properties:

1. `mark_i` = robust function of **external CEX prices** (weighted median) optionally blended with own-book mid.
   - Reference weights (Hyperliquid): weighted median of {Binance 3, OKX 2, Bybit 2, Kraken 1, Kucoin 1, Gate 1, MEXC 1, own-spot 1}.
2. Update cadence bounded (e.g. ≤ 3s) and **the same `mark` snapshot is used for all accounts within one liquidation tick/batch** (determinism).
3. Expose a per-tick immutable `oracle_snapshot { market → mark }` to the engine.

`NOTE:` Median-of-CEX makes on-chain book manipulation ineffective (defends JELLY/POPCAT-style attacks). Trade-off: mark can lag violent moves → stale-quote pick-off; bound cadence and consider a spread/deviation guard.

---

## 6. Liquidation State Machine (deterministic core)

The engine runs a **tick** (per block/batch). Within a tick, `oracle_snapshot` is fixed. The engine is a **total function**: any fill outcome maps to a defined next state; unfilled remainder escalates. This is the invariant that makes the cascade deterministic given inputs (see §9).

### 6.1 Tick loop (top level)
```
for each risk_unit in scan_order:          # scan_order MUST be deterministic (§9)
    classify(risk_unit)                     # §4 using oracle_snapshot
    match state:
        HEALTHY, PRE_LIQ -> continue
        PARTIAL_LIQ      -> run_partial_liquidation(risk_unit)
        BACKSTOP         -> run_backstop(risk_unit)           # §7
        BANKRUPT         -> run_backstop_or_adl(risk_unit)    # §7/§8
```
Re-classification happens each tick; escalation across states happens naturally as `AV` changes tick-to-tick (a partial that fails to restore health falls through to BACKSTOP on a later tick, or immediately if `AV` already < CMR).

### 6.2 Liquidation price (monitoring / UI; also used for tier selection)
For a single position (cross uses aggregate `margin_available`):
```
liq_price = entry − side · margin_available / (S · (1 − l·side))       # careful: use the exact form below
```
Exact form (Lighter):
```
liq_price = price − side · margin_available / position_size / (1 − l·side)
  where l = 1 / MAINTENANCE_LEVERAGE  (tier-dependent at liq price)
        side = +1 long, −1 short
        margin_available(cross)    = AV − MMR
        margin_available(isolated) = AllocatedMargin − MMR_position
```
`NOTE:` For cross, `liq_price` is independent of chosen leverage (lower leverage just commits more collateral). For isolated it depends on allocated margin.

### 6.3 Zero price (partial-liquidation execution price)
The **zero price** is the price at which closing size leaves `AV/MMR` unchanged (health-neutral). Any fill at or better than ZP only improves health.
```
ZP_i(long)  = mark_i · (1 − M_i · AV / MMR)
ZP_i(short) = mark_i · (1 + M_i · AV / MMR)
```
Derivation (long) — closing size `TS` at price `ZP`:
```
AV'  = AV + (ZP − mark)·TS
MMR' = MMR − TS·mark·M_i
require AV'/MMR' = AV/MMR  ⟹  ZP = mark·(1 − AV·M_i/MMR)
```
`NOTE:` This is the mechanism that guarantees partial liquidation never worsens the account and that closing everything at ZP drives `AV→0` exactly (no bad debt if fully fillable at ≥ ZP).

### 6.4 `run_partial_liquidation(risk_unit)`
```
1. Cancel ALL of the user's resting orders in affected markets.        # frees margin, stops self-interference
2. Order the unit's positions by heuristic H (default: descending notional; tie-break market_id asc).
3. sizing:
   if per-market notional N_i > PARTIAL_THRESHOLD (default 100k USDC):
        chunk = CHUNK_FRAC · S_i        # default 20%
   else:
        chunk = S_i                     # small positions: full-size attempt
4. For the selected position, submit reduce-only IoC limit order:
        price = ZP_i (as limit)  ;  size = chunk  ;  direction closes the position
   Fills that occur are at ≥ ZP (book side better than ZP) — remainder auto-cancels (IoC).
5. Apply fills, update collateral/pos/AV. If a fill price is better than ZP,
   take LIQ_FEE (option-dependent, §7) and route to LP/IF.
6. Re-classify. If AV ≥ MMR -> STOP (healthy enough).
7. Cooldown rule (Hyperliquid-style, optional):
      after a partial fill in a block, set cooldown = COOLDOWN_SECS (default 30) on this unit.
      DURING cooldown, if still liquidatable, escalate: next liquidation order is FULL size (not chunked).
8. If after processing all positions the unit is still < CMR (or AV ≤ 0) -> transition to BACKSTOP.
```
`NOTE:` The IoC + zero-price design means step 4 never "hangs" an order; the unfilled part deterministically drops to the next step (chunk retry → full size → backstop). Chunking + cooldown reduces self-inflicted slippage and gives overshoot a chance to revert; the escalation clause prevents dragging a truly insolvent account (bad-debt risk).

---

## 7. Backstop Models

### 7.0 RECOMMENDED ARCHITECTURE (project default): mandated vault + separate insurance fund

Chosen design = **Hyperliquid/Lighter-style single mandated backstop vault** for execution + **a separate insurance fund** as the final loss absorber. **No competitive backstop order book.**

```
Waterfall:
  STANDARD book (partial liquidation, §6)
    → BACKSTOP: single mandated Backstop Vault takes over the residual position at MARK price
                (raw balance-sheet transfer, GUARANTEED — no dependence on liquidators quoting)
    → loss handling:
         buffer = retained maintenance margin + liquidation fees  → credited to INSURANCE FUND
         if takeover is at bad debt (AV < 0):  INSURANCE FUND covers the shortfall (claim)
         the Backstop Vault receives the position at a clean (non-negative) basis
    → the Backstop Vault UNWINDS over time (slice-sell + net vs opposite flow, §6 notes)
         its realized backstop P&L is settled against the INSURANCE FUND
         (vault warehouses/executes; insurance fund is the risk-bearer)
    → if INSURANCE FUND is exhausted → ADL (§8), last resort
```

Why this shape (ties the two prior decisions together):
- **Guaranteed absorption** — the mandated vault always takes the position by rule (like HLP/LLP), so the cascade never stalls waiting for backstop liquidators to post orders. This is why we drop the GTE competitive backstop book.
- **Isolated loss** — losses are borne by a **dedicated insurance fund**, not socialized onto market-making LP depositors. The backstop vault acts as executor/warehouse; the insurance fund is the balance-sheet that eats bad debt and backstop unwind losses.
- Net effect: HL/Lighter's *determinism & guaranteed absorption*, with dYdX/Aster's *risk isolation*.

Interface:
```
backstop_can_absorb(p):                     # mandated vault: effectively always true by rule,
    return true                             # subject to global solvency (§12.9) backed by insurance fund

takeover_price(p) = mark_p                   # raw transfer at mark (HL/Lighter)
on_takeover(p):
    buffer = retained_maintenance_margin(p) + liq_fee
    InsuranceFund.pay(buffer)
    if account_value(p) < 0:                 # bad debt at takeover
        InsuranceFund.claim(-account_value(p))     # covers shortfall; reverts→ADL if IF empty
    transfer p to BackstopVault at basis = mark_p
settle_unwind_pnl(realized):                 # when vault closes the warehoused position
    if realized < 0: InsuranceFund.claim(-realized)   # IF absorbs loss (→ADL if empty)
    else:            InsuranceFund.pay(realized)      # surplus replenishes IF
```
`NOTE:` The Backstop Vault may be protocol-capitalized (cleanest for loss isolation) or a community vault whose backstop P&L is fully hedged to the insurance fund. Either way, MM-LP depositors are not the backstop risk-bearer. If later you want community upside from backstop profits, you can route a share of positive unwind P&L to vault depositors while the insurance fund still caps downside.

The three reference models below are retained for context; the project uses 7.0.

---

Backstop is the **mandatory** counterparty invoked when the book cannot clear the position (state BACKSTOP/BANKRUPT). Unlike order-book MM, it cannot decline.

Common entry point:
```
run_backstop(risk_unit):
    for each position p in unit ordered by unrealized_pnl ASC:     # worst first
        if backstop_can_absorb(p):     # model-specific capital check
            transfer p (and pro-rata margin) to backstop account at takeover_price(p)
            apply LIQ_FEE / margin-retention per model
        else:
            enqueue p for ADL (§8)
    if unit has isolated-only positions: only that position + its margin move.
    if cross: all cross positions + cross margin move; user AV -> 0 if no isolated left.
```
`takeover_price(p)`: use `mark_i` with a **buffer** so the backstop is profitable on average. Two equivalent ways to realize the buffer:
- **Margin-retention (Hyperliquid):** takeover at `mark`, but the user's maintenance margin is **not** returned (kept by LP as buffer). No explicit fee.
- **Fee/zero-price (Lighter/Aster):** takeover at `ZP`/bankruptcy price; charge `LIQ_FEE` (≤1% Lighter; "insurance clearance fee" Aster) into the backstop.

### Model A — LP-vault-fused (Hyperliquid HLP / Lighter LLP)
The same community LP that market-makes is also the backstop. `NOTE:` The project default (§7.0) adopts this model's **single mandated vault + raw-transfer-at-mark execution** (guaranteed absorption) but **splits the loss absorber out into a separate insurance fund** rather than socializing it onto the MM vault's depositors.

```
backstop_can_absorb(p):    # Lighter rule
    return LP.account_value_after_absorbing(p) ≥ LP.IMR_after_absorbing(p)
```
- Deposits: single vault (or per-strategy shards, see loss isolation below). PnL socialized pro-rata; no performance fee.
- Absorbed positions are **unwound over time** by the LP's MM strategy (slice-sell + net against opposite flow). Backstop profit/loss flows to LP depositors.
- **Loss isolation (recommended for long-tail):** partition LP collateral into **strategy shards** keyed by market group. `backstop_can_absorb` and losses evaluated per shard; shard depletion → that shard's positions go to ADL, other shards untouched. (Lighter LLP Strategies.)

Pros: strongest cascade absorption; liquidation profit accrues to community; profitable in mechanical cascades (overshoot reversion). Cons: depositors bear tail risk from informed/manipulated one-sided flow.

### Model B — Separate insurance fund with competitive backstop book (dYdX / Aster / GTE)
Market-making / backstop liquidity is **distinct** from the loss-absorbing insurance fund (IF). The IF is the only thing that eats residual bad debt; LPs and backstop liquidators are never forced to inherit a losing position onto a socialized-PnL vault.

`NOTE:` The project default (§7.0) borrows this model's **insurance-fund separation** but replaces its *competitive backstop book* with a **single mandated vault** for guaranteed absorption. The GTE mechanics below are retained because they show the insurance-fund plumbing in audited code.

**GTE realization (audited reference).** GTE, though it also ships a GTL LP vault, structures its backstop exactly along Model-B lines — the loss absorber is the standalone `InsuranceFund`, and backstop execution is a *separate book fed by incentivized backstop liquidators*:

```
Backstop trigger:  liquidatable on BACKSTOP book ⟺ margin + uPnL < MMR / 3
                   (STANDARD trigger is  margin + uPnL < MMR ; backstop is deeper, 1/3 MMR)
backstopLiquidate(asset, account, subaccount):   # onlyBackstopLiquidator
  1. assertLiquidatable(BACKSTOP)                 # gate at 1/3 MMR (or bad-debt: minMargin==0 && margin<0)
  2. fill position on the BACKSTOP book           # book accepts ONLY MOC (post-only) reduce-only orders
                                                  # → backstop liquidators pre-post resting liquidity here
  3. proratedMargin = margin fraction for the closed size (buffer)   # not full maintenance margin
     margin -= proratedMargin
     proratedMargin += rpnl ; if <0 push back into margin, zero it
  4. fee = settleBackstopLiquidation(proratedMargin):
        liquidationFee = proratedMargin * liquidationFeeRate         # → returned, routed to IF
        distribute (proratedMargin - liquidationFee) to backstop liquidators
            weight_i = (pointShare_i + volumeShare_i) / 2            # 50% reputation points, 50% this-liq volume
  5. if margin < 0 and single position: fee += margin (realize bad debt); margin = 0
  6. if fee > 0: InsuranceFund.pay(fee)   else: InsuranceFund.claim(-fee)   # IF absorbs shortfall
  7. settleFill ; updateAccount
```
Key properties to copy:
- **Two-book design**: STANDARD book (open liquidation, anyone competes) + **BACKSTOP book restricted to MOC reduce-only** resting orders from backstop liquidators. Uniform "fill against a book" code path; backstop liquidity is *pre-committed*, not a raw transfer.
- **Deeper trigger for backstop** (`MMR/3`) than standard (`MMR`) — gives the standard book first crack, escalates only when much closer to insolvency.
- **Backstop liquidators are paid the prorated margin** (incentive), weighted by reputation points + volume; the LP vault (GTL) may participate as one such liquidator but bears no special socialized loss.
- **Only the InsuranceFund absorbs residual bad debt** (`claim`, reverts if empty → escalate to ADL). This is the clean risk separation you want.

Generic Model-B interface:

```
backstop_can_absorb(p):
    return IF.balance ≥ expected_loss(p)          # expected_loss = max(0, bankruptcy_shortfall)
```
- IF is funded by **liquidation fees** ("insurance clearance fee") and accumulates over time.
- On backstop: position closed at **bankruptcy price**; if user balance goes negative, IF covers the shortfall (Aster: auto-settle only if no open positions and shortfall ≤ 5,000 USDT; else manual).
- MM pool (ALP) provides book liquidity and is protected from directional exposure via **funding-rate skew**, not by taking over liquidations.

Pros: depositor risk isolation (MM LPs don't inherit bad debt); simpler risk attribution. Cons: IF must be sized/funded adequately; no community upside from liquidation PnL; a large gap can exhaust IF → ADL sooner.

### Model C — Hybrid (GTE: GTL vault + InsuranceFund + backstop book)

`NOTE:` The project default is **§7.0 (mandated vault + separate insurance fund)**, not this competitive-book hybrid. Model C is documented because GTE's audited code is a useful reference for insurance-fund plumbing and ADL. GTE's audited design:

```
Priority:  STANDARD book (liquidate)
        -> BACKSTOP book (backstopLiquidate; GTL LP quotes here)   # buffer = retained prorated margin
        -> InsuranceFund covers residual bad debt (claim)
        -> ADL (deleverage) pairs underwater maker ↔ profitable taker @ maker bankruptcy price
```
Distinctive implementation choices:
- **Backstop is a *separate order book* (`BookType.BACKSTOP`)**, not a raw position transfer. The LP vault (GTL) and/or `BACKSTOP_LIQUIDATOR_ROLE` post liquidity there. Liquidation fills against it like a normal match. This keeps the whole pipeline as "fill against a book" (uniform code path) and lets the buffer come from retained prorated margin.
- **LP vault = ERC4626 (`GTL`)** with **queued withdrawals** (`queueWithdrawal` → admin `processWithdrawals`); `maxWithdraw/maxRedeem = 0` so no instant redeem (analogous to HLP 4-day lock / Lighter). `totalAssets = idle USDC + orderbookCollateral + freeCollateral + Σ positive subaccount AV`.
- **InsuranceFund** is a minimal `{balance}` with `pay(amount)` (fee inflow) / `claim(amount)` (bad-debt outflow, reverts if insufficient → forces ADL).
- **Permissioned liquidators**: `LIQUIDATOR_ROLE` (liquidate/deleverage/delistClose), `BACKSTOP_LIQUIDATOR_ROLE` (backstopLiquidate). `NOTE:` this mirrors Hyperliquid's `allowed_liquidators` (the "liquidation cartel" reverse-engineering finding) — a deliberate trust/latency trade-off. If you want permissionless liquidation, replace the role check with an open entrypoint + keeper incentive; keep the rest identical.
- **Fee routing is symmetric**: `if fee > 0: InsuranceFund.pay(fee)  else: InsuranceFund.claim(-fee)`.

`NOTE:` If you don't adopt the full hybrid, you can still run **both** minimally: IF as first loss-absorber, LP-vault as secondary backstop, ADL last. Document the priority explicitly and keep each `can_absorb` check total.

---

## 8. Auto-Deleveraging (ADL) — last resort

Triggered when backstop cannot absorb (capital check fails) and/or account is BANKRUPT with residual position. ADL forcibly closes **opposite-side** traders against the bankrupt position at a health-neutral price.

### 8.1 Execution
```
run_adl(bankrupt_pos p):
    counter_side = opposite(p.side)
    candidates   = all accounts holding counter_side positions in market(p)
    rank(candidates) desc                    # §8.2
    remaining = p.size
    for c in candidates (highest rank first):
        fill = min(remaining, c.position_size)
        execute forced trade (p ↔ c) at settlement_price      # = ZP / previous oracle price
        remaining -= fill
        if remaining == 0: break
    # settlement_price MUST NOT be worse than each counterparty's zero price
    # (guarantees no counterparty's health decreases)
```
`settlement_price`: Lighter/HL use the bankrupt side's zero price / previous oracle price; Aster uses bankruptcy price. Requirement: `settlement_price` is health-neutral or better for the counterparty.

### 8.2 Ranking (who gets deleveraged first)
Reference-unified formula (Aster, explicit; HL/Lighter equivalent "leverage + uPnL"):
```
PnL_pct  = unrealized_pnl / |position_notional|
eff_lev  = |position_notional| / (account_balance + unrealized_pnl)
if PnL_pct ≥ 0:  rank = PnL_pct · eff_lev
else:            rank = PnL_pct / eff_lev
quantile = rank_index(rank) / total_counterparties      # higher => deleveraged first
```
`NOTE:` Rank prioritizes the most-profitable, highest-leverage counterparties — the ones who benefited most from the move that bankrupted `p`. Accounts with no position are never ADL'd.

---

## 9. Determinism & Execution Model

The **rules** are deterministic; realized outcomes depend on exogenous inputs (mark, live book, tx ordering). To make each tick reproducible/ZK-provable:

1. **Fixed oracle snapshot per tick** (§5). No mid-tick mark changes.
2. **Deterministic scan order** of risk units, e.g. ascending `(AV/MMR)` then `account_id`; or fixed account_id order. Must be a pure function of pre-tick state.
3. **Deterministic matching**: given the ordered batch of transactions + oracle snapshot, matching and fills are a pure function (single-sequencer or leader-proposer model). This is exactly what a ZK proof certifies (Lighter) — publish (pre-state, batch, oracle) → post-state is unique.
4. **Total transition**: never leave an "undefined" branch. Any fill amount (including 0) has a defined successor (retry chunk → full size → backstop → ADL).
5. **Contingency map is precomputable**: because decisions are `f(state, mark)`, a risk engine can pre-map "if mark = X, these units liquidate; LP absorbs Y (worst-case book empty); ADL hits Z". Use for monitoring/liquidation heatmaps and stress tests.
6. **Execution ≠ spec**: guarantee liquidations run each block even under load (reserve compute for liquidation/proof generation; do not let normal-order throughput starve the liquidation path — this was Lighter's Oct-2025 failure mode).

What remains non-deterministic (by nature, not a bug): future mark path, live order-book depth (who quotes), and tx arrival/order. These parameterize *magnitudes and which terminal stage absorbs*, not the *logic*.

---

## 10. Data Structures (reference)

```
Market {
  id
  oracle_cfg { sources[], weights[], cadence_ms }
  tier_table[ {upper_notional, I, M, C, max_leverage} ]
  partial_threshold          # default 100_000 (USDC)
  chunk_frac                 # default 0.20
  cooldown_secs              # default 30
  liq_fee_bps                # model B / Lighter: e.g. up to 100 (=1%)
  strategy_shard_id          # for LP loss isolation (Model A)
}

Account {
  id
  collateral                 # cross
  positions: map<market_id, Position>   # cross
  isolated: list<IsolatedUnit>
  resting_orders: list<Order>
  cooldown_until_ts
}

Position { market_id, size(signed), entry_vwap }

BackstopModelA_LP {
  shards: map<shard_id, { account_value, positions, IMR_fn }>
}
BackstopModelB_IF {
  insurance_fund_balance
  mm_pool (ALP)             # separate; not a loss absorber
}

OracleSnapshot { tick_id, marks: map<market_id, price> }   # immutable per tick
```

---

## 11. Reference Pseudocode (engine tick, Model-agnostic)

```python
def liquidation_tick(state, oracle: OracleSnapshot, cfg):
    adl_queue = []
    for unit in deterministic_scan_order(state):      # §9.2
        h = classify(unit, oracle, cfg)               # §4
        if h in (HEALTHY, PRE_LIQ):
            continue
        if h == PARTIAL_LIQ:
            partial_liquidate(unit, oracle, cfg)      # §6.4  (may fill via book)
            h = classify(unit, oracle, cfg)
        if h in (BACKSTOP, BANKRUPT):
            for p in sort_by_unrealized_pnl_asc(unit.positions):
                if backstop_can_absorb(p, cfg):       # §7 (model-specific)
                    absorb(p, oracle, cfg)            # transfer + buffer/fee
                else:
                    adl_queue.append(p)
    for p in adl_queue:                               # §8, last
        run_adl(p, oracle, cfg)
    assert_invariants(state)                          # §12
    return state
```
Partial-liquidate detail:
```python
def partial_liquidate(unit, oracle, cfg):
    cancel_all_resting(unit)
    for p in order_by_heuristic(unit.positions):
        N = abs(p.size) * oracle[p.market_id]
        if in_cooldown(unit): size = abs(p.size)                 # escalated full-size
        elif N > cfg.partial_threshold: size = cfg.chunk_frac*abs(p.size)
        else: size = abs(p.size)
        zp = zero_price(p, oracle, unit)                          # §6.3
        fills = submit_reduce_only_ioc(p, price=zp, size=size)    # book match
        apply_fills(unit, p, fills)
        take_liq_fee_if_improved(fills, zp, cfg)                  # §7
        set_cooldown(unit, cfg.cooldown_secs)
        if classify(unit, oracle, cfg) >= MMR: return             # healthy enough
```

---

## 12. Invariants (assert after every tick; also property-test targets)

1. **No health degradation from liquidation/ADL**: for any account, a liquidation or ADL fill executes at a price ≥ its zero price ⟹ `AV/MMR` non-decreasing for that account.
2. **Partial liquidation is monotone**: `AV` after `partial_liquidate` ≥ `AV` before (never worse).
3. **Backstop capital rule holds**: after Model-A absorb, `LP.AV ≥ LP.IMR` (per shard). After Model-B, `IF.balance ≥ 0`.
4. **Bad debt conservation**: any `AV<0` residual is fully covered by (IF and/or LP and/or ADL); global `Σ bad_debt = 0` after tick.
5. **Determinism**: `tick(pre_state, batch, oracle)` is a pure function (same inputs → identical post-state hash).
6. **Totality**: every position in BACKSTOP/BANKRUPT is either absorbed or enqueued to ADL; none dropped.
7. **Isolation (Model A shards / Model B)**: a loss in shard/market X does not reduce collateral attributed to shard/market Y beyond configured coupling.
8. **Fee routing**: liquidation fees are conserved and routed only to LP/IF per model.
9. **Global solvency (GTE main invariant)**: the manager contract's collateral-token balance MUST be ≥ the sum of all obligations:
   ```
   token_balance(PerpManager) ≥ Σ user_free_collateral + Σ user_margin_balance + insurance_fund_balance
   ```
   Assert this after every state-changing operation (deposit/withdraw/trade/liquidate/deleverage). It is the single strongest "no funds invented, no funds lost" check.

---

## 13. Parameters (defaults, tunable via governance)

| Param | Default | Source |
|---|---|---|
| `M_i` (majors) | `I_i/2` = 1.25% @40x | Hyperliquid |
| `C_i` | `k_C·M_i`, `k_C=0.5–0.8` (or `CMR=2/3·MMR` for 2-tier) | Lighter / HL |
| `partial_threshold` | 100,000 USDC (10k testnet) | Hyperliquid |
| `chunk_frac` | 20% | Hyperliquid |
| `cooldown_secs` | 30 | Hyperliquid |
| `liq_fee` (Model B / Lighter path) | ≤ 1% of price-improvement | Lighter |
| max leverage (majors) | 40x BTC / 25x ETH (post-incident caps) | Hyperliquid |
| oracle cadence | ≤ 3s | Hyperliquid |
| IF auto-settle cap (Model B) | ≤ 5,000 USDT, no open positions | Aster |

---

## 14. Test Scenarios (must pass)

1. **Clean partial**: thin adverse move; 20% chunk restores health; leftover margin returned; no LP/IF touch.
2. **Gap to bankruptcy**: mark jumps past liq price; `AV<0`; backstop absorbs; verify buffer/fee routing and invariant 4.
3. **Mechanical cascade**: many accounts cross MMR same tick; verify deterministic scan order, chunking limits self-slippage, overshoot handled without bad debt.
4. **Manipulated one-sided flow (JELLY/POPCAT analogue)**: illiquid market, backstop inherits losing side; Model A shard caps loss; Model B IF depletes → ADL fires; assert other shards/markets unaffected.
5. **Backstop capacity exceeded**: LP would breach IMR / IF insufficient → positions route to ADL; ranking correct (highest PnL·leverage first); no counterparty health decreases.
6. **Determinism**: replay same (state, batch, oracle) → identical post-state hash (ZK-parity).
7. **Execution starvation**: flood normal orders; liquidation path still executes each block (reserved compute).
8. **Isolated vs cross**: isolated liquidation leaves cross untouched and vice versa.

---

## 15. Implementation Order (suggested)

1. Margin accounting + health classification (§3–4) + property tests (invariants 1–2).
2. Mark-price snapshot contract (§5) with fixed per-tick immutability.
3. Zero-price + partial liquidation with IoC + chunk/cooldown (§6).
4. Backstop per §7.0 (project default): single mandated Backstop Vault (raw transfer at mark) + separate Insurance Fund (`pay`/`claim`) behind it; unwind P&L settled to IF. Keep the `backstop_can_absorb`/`absorb` interface so alternative models (§7 A/B/C) remain swappable.
5. ADL (§8) with ranking.
6. Determinism harness (§9) + replay/hash test.
7. Stress/scenario suite (§14).

---

## 16. Sources (reverse-engineering & docs)

- Lighter — Liquidations & LLP (Insurance Fund): https://docs.lighter.xyz/perpetual-futures/liquidations-and-llp-insurance-fund
- Lighter — LLP Strategies (loss isolation): https://docs.lighter.xyz/trading/liquidations-and-llp-insurance-fund/llp-strategies
- Lighter — Whitepaper: https://assets.lighter.xyz/whitepaper.pdf
- Beosin/PANews — Lighter Oct-11 2025 outage analysis: https://www.panewslab.com/en/articles/95ed5301-276e-411d-84c0-b2d63c7121bc
- Hyperliquid — Liquidations: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- Hyperliquid — Protocol vaults (HLP): https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults
- Hyperliquid — Oracle / Robust price indices: https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/oracle
- Can Bölük — Reverse Engineering Hyperliquid (binary analysis): https://blog.can.ac/2025/12/20/reverse-engineering-hyperliquid/
- Mirador — Backstop dynamics & ADL: https://www.mirador.finance/p/hyperliquid-under-pressure-backstop
- Aster — Liquidations (Pro): https://docs.asterdex.com/product/aster-perpetuals/fees-and-specs/liquidations
- Aster — Auto-Deleveraging (ADL): https://docs.asterdex.com/product/aster-perpetual-pro/fees-and-specs/auto-deleveraging
- dYdX — MegaVault (split MM/insurance model): https://docs.dydx.community/dydx-unlimited/unlimited-features/megavault
- **GTE — Perps (open-source Solidity, Code4rena)**: https://github.com/code-423n4/2025-08-gte-perps  (CLOB: https://github.com/code-423n4/2025-07-gte-clob)
- GTE — Zellic audit (CLOB Perps): https://github.com/Zellic/publications/blob/master/GTE%20Perps%20-%20Zellic%20Audit%20Report.pdf
- GTE — Docs: https://docs.gte.xyz/home/
- Market-making theory: Ho & Stoll (1981) JFE 9:47–73; Glosten & Milgrom (1985) JFE 13:71–100; Avellaneda & Stoikov (2008) Quantitative Finance 8(3):217–224.

---

## 17. Appendix — GTE Reference Implementation Map (open-source Solidity)

Real, audited code you can read/fork directly. Repo: `code-423n4/2025-08-gte-perps`, `contracts/perps/`.

### 17.1 File map (spec section → source)

| Spec section | GTE file | Role |
|---|---|---|
| Entry / routing | `PerpManager.sol`, `modules/AdminPanel.sol` | main contract; module + `StorageLib` (diamond-style storage) |
| §6 partial, §7 backstop, §8 ADL | **`modules/LiquidatorPanel.sol`** | `liquidate()`, `backstopLiquidate()`, `deleverage()`, `delistClose()` |
| §3 accounting, health | `types/ClearingHouse.sol` | `getAccountAndMargin`, `rebalanceClose`, `getProratedMargin`, `updateAccount` |
| §3 tiers/margin | `types/Market.sol`, `types/Position.sol` | market settings, `processTrade`, margin math |
| §5 mark price | `types/PriceHistory.sol`, `FundingRateEngine.sol` | mark vs index price, funding |
| §6 order book | `types/Book.sol`, `types/CLOBLib.sol` | STANDARD & BACKSTOP books, matching |
| §7A LP vault | **`GTL.sol`** | ERC4626 "GTE Liquidity Pool", queued withdrawals |
| §7B insurance fund | **`types/InsuranceFund.sol`** | `pay()` / `claim()` |
| §8 ADL bookkeeping | `types/BackstopLiquidatorDataLib.sol` | deleverage pair data |
| §4 views | `modules/ViewPort.sol` | `getAccountValue`, `getOrderbookCollateral`, `getFreeCollateralBalance` |

### 17.2 Roles (permissioning)
```
ADMIN_ROLE                — full control
LIQUIDATOR_ROLE           — liquidate(), deleverage(), delistClose()
BACKSTOP_LIQUIDATOR_ROLE  — backstopLiquidate()
```
`NOTE:` permissioned by default (cf. Hyperliquid `allowed_liquidators`). Swap for permissionless keeper + incentive if desired.

### 17.3 `liquidate()` — normal path (against STANDARD book), simplified
```
cache = _liquidate(asset, account, subaccount, BookType.STANDARD)   # fills position on standard book
fee   = liquidationFeeRate * cache.fillResult.quoteTraded / 1e18
cache.margin += cache.positionResult.rpnl - fee
(cache.margin, marginDelta) = rebalanceClose(...)
if fullClose && marginDelta < 0 && |marginDelta| < maintenanceMargin:   # closed above water
    fee -= marginDelta; marginDelta = 0
else if fullClose && cache.margin < 0:                                  # closed under water => bad debt
    fee += cache.margin; cache.margin = 0
emit Liquidation(... LIQUIDATEE ...)
if fee > 0: InsuranceFund.pay(|fee|)     else: InsuranceFund.claim(|fee|)   # symmetric routing
settleFill(account, subaccount, cache.margin, marginDelta)
updateAccount(...)
```

### 17.4 `backstopLiquidate()` — backstop path (against BACKSTOP book), simplified
```
cache = _liquidate(asset, account, subaccount, BookType.BACKSTOP)   # GTL/backstop liquidity
proratedMargin = cache.maintenanceOrProratedMargin
cache.margin  -= proratedMargin                 # retain maintenance/prorated margin as LP buffer
proratedMargin += cache.positionResult.rpnl
if proratedMargin < 0: cache.margin += proratedMargin; proratedMargin = 0
fee = _settleBackstopLiquidation(asset, proratedMargin)
if cache.margin < 0 && single position: fee += cache.margin; cache.margin = 0   # realize bad debt
emit Liquidation(... BACKSTOP_LIQUIDATEE ...)
if fee > 0: InsuranceFund.pay(|fee|)     else: InsuranceFund.claim(|fee|)
```

### 17.5 `deleverage()` (ADL) — paired forced trade at bankruptcy price, simplified
```
for pair in pairs:                       # pair = {maker (underwater), taker (profitable counterparty)}
    load maker/taker, realize funding
    validate pair (maker underwater, taker opposite side, sizes)     # _validateDeleveragePair
    base   = min(maker.size, taker.size)
    price  = _getBankruptcyPrice(maker.position, base, proratedMargin(maker))   # ADL executes @ maker bankruptcy price
    quote  = base * price / 1e18
    _deleverage(maker, base, quote, DELEVERAGE_MAKER)
    _deleverage(taker, base, quote, DELEVERAGE_TAKER)
# residual bad debt in _deleverage: InsuranceFund.claim(badDebt)
```
`NOTE:` The **caller (LIQUIDATOR_ROLE) supplies the maker↔taker pairs**; the contract validates and executes. Counterparty selection (§8.2 ranking) is done off-chain by the liquidator and *checked* on-chain — a pragmatic split of "who to pick" (off-chain, needs global sort) vs "is this pick valid/health-neutral" (on-chain, deterministic).

### 17.6 `GTL` (ERC4626 LP vault) essentials
```
totalAssets = usdc.balanceOf(this) + orderbookCollateral() + freeCollateralBalance() + totalAccountValue()
withdrawals: queueWithdrawal(shares) -> admin processWithdrawals(n)  (FIFO queue)
maxWithdraw = maxRedeem = 0            # instant redeem disabled; must queue
runs perp subaccounts (addSubaccount/removeSubaccount by PerpManager) that MM + backstop
```

### 17.7 InsuranceFund essentials
```
struct InsuranceFund { uint256 balance }
pay(amount):   balance += amount                      # liquidation fees in
claim(amount): require(balance >= amount); balance -= amount   # bad debt out (revert => escalate to ADL)
```

### 17.8 What to port vs adapt
- **Port as-is (conceptually):** the four entrypoints + symmetric fee routing + bankruptcy-price ADL + ERC4626 queued-withdraw LP + minimal insurance fund + global solvency invariant (§12.9).
- **Adapt to our chain/model:** STANDARD vs BACKSTOP as two books vs a single book with a synthetic backstop maker; permissioned vs permissionless liquidators; on-chain vs sequencer/ZK determinism (§9); mark-price oracle source (§5); whether to add Lighter-style **loss-isolated LP shards** for long-tail markets (GTE uses one GTL pool).
- **Watch-outs (audit focus areas from the contest):** generating bad debt/negative equity for net gain, ADL abuse for profit, order-book DoS (an order that can't be cleared by the ClearingHouse). Bake these into the §14 test suite.

---

## 18. Per-Market Risk Budgets & Dynamic Caps

Goal: **bound worst-case backstop loss per market by design**, so a single thin/manipulated market (JELLY/POPCAT/ARC pattern) cannot drain the shared insurance fund or the mandated backstop vault. This is the primary defense; real-time manipulation "detection" (§18.6) is only a conservative secondary trigger. Philosophy: convert "detect & react in real time" (adversarial, false-positive-prone) into "**bounded by construction + graduated auto-tightening**".

### 18.1 The four per-market caps

For each market `m` maintain:

| Cap | Symbol | Bounds | Meaning |
|---|---|---|---|
| Backstop sub-budget | `B_m` | insurance-fund allocation to `m` | max loss the IF will absorb for `m`; beyond → ADL for `m` only |
| Open-interest cap | `OI_m` | total OI notional | caps max possible backstop liability (∝ OI) |
| Warehouse cap | `W_m` | vault net inventory notional | max notional the mandated backstop vault will hold in `m` before escalating to ADL |
| Leverage tier | `L_m` | max leverage / `I_m,M_m,C_m` | margin-tier table (§3.2); thinner market ⇒ lower leverage, wider fractions |

`NOTE:` `B_m` implements Lighter-style shard isolation on top of the §7.0 insurance fund: the IF is partitioned into per-market (or per-tier) sub-budgets. Losses in `m` consume only `B_m`.

### 18.2 How caps gate the engine

- **§3 margin:** `L_m` sets the tier table; new/thin markets compress leverage hard.
- **Order placement:** reject opening orders that would push market OI above `OI_m` (reduce-only always allowed).
- **§7.0 backstop takeover:** the mandated vault absorbs up to `W_m` net inventory in `m`; a takeover that would exceed `W_m`, **or** whose bad-debt draw would exceed remaining `B_m`, is **not** absorbed → routes to ADL (§8) for `m`.
- **§7.0 loss settlement:** vault unwind losses and bad-debt draws for `m` are charged to sub-budget `B_m`; when `B_m` is exhausted → ADL. Other markets' budgets untouched (isolation invariant §12.7).

### 18.3 Dynamic cap update engine (periodic / epoch-based)

Caps are **recomputed every epoch** by a permissionless keeper calling `updateCaps(m)` at the epoch boundary. The update is a **pure function of observed, manipulation-resistant inputs** over a rolling window (deterministic, auditable). Governance sets only parameters + hard bounds and holds an emergency down-only override.

**Inputs (weighted by manipulation resistance):**
```
cex_depth_m   = median over reference CEXs of 2%-book-depth for the asset   # hardest to fake → primary driver
maturity_m    = clamp(days_listed_m / MATURITY_DAYS, 0, 1)
own_flow_m    = damp(rolling own-venue volume/OI)      # wash-tradeable → heavily damped, cannot alone raise caps
rvol_m        = realized volatility over window        # higher ⇒ lower cap (penalty)
```

**Target then asymmetric rate-limit (raise slow, cut fast):**
```
target_m = BASE[tier(m)] * maturity_m * g(cex_depth_m) * damp(own_flow_m) / vol_penalty(rvol_m)
target_m = clamp(target_m, HARD_MIN[tier], HARD_MAX[tier])          # governance hard bounds

if target_m > cap_m_prev:
    cap_m = min(target_m, cap_m_prev * (1 + UP_STEP))               # UP_STEP small (e.g. 0.10)
else:
    cap_m = max(target_m, cap_m_prev * (1 - DOWN_STEP))             # DOWN_STEP large (e.g. 0.50)  DOWN_STEP >> UP_STEP
```
Apply the same engine (with per-cap `BASE`/bounds) to `B_m`, `OI_m`, `W_m`, and `L_m`.

**Freeze (skip increases) this epoch if any stress signal is active** (down moves still allowed):
```
freeze_up(m) = utilization(m) ≥ UTIL_FREEZE            # §18.4
             OR oracle_divergence(m) ≥ DIV_CAP          # mark vs CEX median
             OR oi_concentration(m) ≥ CONC_CAP          # top-k wallets share of OI
             OR rvol_m ≥ RVOL_FREEZE
```

**Pseudocode:**
```python
def updateCaps(m, now):                       # called by keeper at each epoch boundary; pure over recorded metrics
    assert now >= last_update[m] + EPOCH
    inp = read_rolling_metrics(m)             # cex_depth, days_listed, own_flow(damped), rvol, util, divergence, concentration
    for cap in (B, OI, W, L):
        tgt = BASE[cap][tier(m)] * inp.maturity * g_cex(cap, inp.cex_depth) * damp(inp.own_flow) / vol_penalty(inp.rvol)
        tgt = clamp(tgt, HARD_MIN[cap][tier(m)], HARD_MAX[cap][tier(m)])
        prev = caps[m][cap]
        if tgt > prev and not freeze_up(m, inp):
            caps[m][cap] = min(tgt, prev * (1 + UP_STEP[cap]))
        else:
            caps[m][cap] = max(tgt, prev * (1 - DOWN_STEP[cap]))   # cuts always allowed
    last_update[m] = now
    emit CapsUpdated(m, caps[m], inp.hash)     # auditable
```

Governance / guardian:
- Governance sets `BASE`, `HARD_MIN/MAX`, `UP_STEP`, `DOWN_STEP`, `EPOCH`, freeze thresholds, reference-CEX set.
- **Guardian emergency override is DOWN-ONLY** (can cut caps immediately, never raise). Prevents a compromised keeper/oracle from inflating exposure.
- New market listing: start at `HARD_MIN[tier]` (smallest budget) + isolation; caps can only grow via the epoch engine.

### 18.4 Utilization ladder (auto-tightening between epochs)

Independent of the epoch cap recompute, respond continuously to **how full each cap is** — reacts to exposure, not intent (no false positives):
```
util(m) = used_backstop_budget(m) / B_m          # (or OI used / OI_m, inventory / W_m — take the max)
```
| `util(m)` | Action (automatic) |
|---|---|
| < 0.6 | normal |
| 0.6–0.8 | widen backstop/MM spreads in `m`; freeze cap increases |
| 0.8–0.95 | raise `M_m` (margin) / cut effective leverage; new opens reduce-only-biased |
| ≥ 0.95 | `m` opens **reduce-only only**; further backstop overflow → ADL immediately |

### 18.5 Parameters (defaults, governance-tunable)

| Param | Default | Note |
|---|---|---|
| `EPOCH` | 1 day (rolling 7-day windows) | cadence of `updateCaps` |
| `MATURITY_DAYS` | 30 | time to reach full maturity factor |
| `UP_STEP` | 0.10 / epoch | slow ratchet up |
| `DOWN_STEP` | 0.50 / epoch | fast ratchet down (`>> UP_STEP`) |
| `UTIL_FREEZE` | 0.6 | utilization that freezes cap increases |
| `DIV_CAP` | market-specific | mark vs CEX-median divergence freeze |
| `CONC_CAP` | e.g. top-5 wallets > 50% OI | concentration freeze |
| `HARD_MIN/MAX[tier]` | per tier | absolute floors/ceilings; new listings start at MIN |
| reference CEXs | Binance/OKX/Bybit/… | for `cex_depth`; median, own-book excluded |

### 18.6 Detection as *secondary* trigger (conservative)

Real-time signals (inventory non-reversion, unwind velocity ≤ 0, oracle divergence, OI concentration, VPIN/flow toxicity, IF drawdown rate) are used **only to (a) trip `freeze_up`, (b) accelerate the utilization ladder, or (c) alert a human guardian** — never to auto-seize/settle. Rationale: distinguishing manipulated from legitimately volatile flow in real time is unreliable (Glosten-Milgrom); false positives would harm honest users. Discretionary last-resort actions (delist + force-settle, cf. Hyperliquid JELLY) must be **pre-defined governance procedures with explicit triggers**, not ad hoc.

### 18.7 Additional invariants (extend §12)

10. **Per-market loss bound:** cumulative backstop + bad-debt loss charged to market `m` within an epoch ≤ `B_m` at the epoch start; any excess is realized via ADL, not by drawing another market's budget.
11. **Cap monotonic safety:** `updateCaps` can raise a cap by at most `UP_STEP`; cuts unbounded down to `HARD_MIN`. Guardian override is down-only.
12. **Manipulation-resistance:** no cap can increase driven solely by own-venue volume/OI; a strictly positive `cex_depth` contribution is required for any raise.

### 18.8 Test scenarios (extend §14)

9. **Thin-market attack contained:** open large OI in a new market (min budget) → attempt squeeze → loss capped at `B_m`; overflow → ADL in `m` only; majors' budgets untouched (assert §12.10).
10. **Cap can't be gamed up:** wash-trade own-venue volume/OI with flat CEX depth → caps do **not** rise (assert §12.12).
11. **Asymmetric response:** simulate stress → caps cut by `DOWN_STEP` immediately; recovery → caps rise only `UP_STEP`/epoch over many epochs.
12. **Freeze under divergence:** induce mark-vs-CEX divergence → `freeze_up` active → no cap increase that epoch; cuts still apply.
13. **Utilization ladder:** drive `util(m)` through 0.6/0.8/0.95 → assert spread-widen → margin-raise → reduce-only transitions fire.
```
