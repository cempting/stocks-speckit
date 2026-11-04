# Feature Specification: Market Structure Service and Persistent Observation Cache

**Feature Branch**: Unchanged; no feature branch created

**Feature Directory**: `specs/013-market-structure-service`

**Created**: 2026-11-03

**Status**: Draft

**Input**: A separate application named `market-structure` supplies sectors, industries,
stocks, and news sources. The stock app keeps an ongoing snapshot of recently fetched
stock, ETF, and index observations, creates that cache when absent, and uses the supplied
structure to organize fast navigation, incremental acquisition, and reuse.

**Decisions confirmed on 2026-11-03**:

- Deliver `market-structure` as a separately runnable and deployable application in this
  repository, not merely another library within the stock app.
- On an empty observation cache, create it automatically and fetch the active view's
  required observations first. Grow it on demand, not by prefetching the universe.
- During a structure-service outage, permit read-only browsing of previously validated
  structure and cached observations with a visible offline/stale warning. Do not extend
  expired source permissions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse a market organized by an independent authority (Priority: P1)

As a stock researcher, I want sectors, industries, stock identities, representations,
and available news sources to come from `market-structure`, so that their maintenance
is independent of the stock app and every view uses the same reviewed organization.

**Why this priority**: Without an explicit structure authority, separate applications
can disagree about membership, identity, or which sources are permitted.

**Independent Test**: Run the structure application without the stock app or a live-data
provider. Supply a controlled reviewed revision, connect a consumer, and verify its
hierarchy, memberships, identities, source metadata, and revision as one coherent result.

**Acceptance Scenarios**:

1. **Given** a reviewed structure revision, **When** the stock app connects, **Then** it
   obtains and validates that revision and shows its sectors, industries, and stocks
   without reading the service's underlying storage or inventing a local roster.
2. **Given** nested industries and one stock belonging to several industries, **When**
   users browse those industries or their common ancestors, **Then** memberships remain
   accurate and each instrument appears once in an ancestor rollup.
3. **Given** reviewed stock, ETF, and index listings, **When** a representation or benchmark
   is selected, **Then** the app uses the explicitly supplied identity and listing mapping,
   not a ticker inferred from a name or an unrelated parent representation.
4. **Given** registered news sources with different permissions, **When** the app reads
   their metadata, **Then** it preserves source identity, role, provenance, review state,
   applicable scope, and permission dates without treating registration as acquisition
   or display approval.
5. **Given** an incompatible or internally inconsistent revision, **When** it is offered
   to the app, **Then** the app rejects it with an actionable diagnostic and does not
   replace its last validated revision.

---

### User Story 2 - Open the stock app with no local observations (Priority: P1)

As a user starting with an empty cache, I want the app to create its observation store
and load the data needed by my current view, without a manual import or a wait for the
entire stock universe to download.

**Why this priority**: A clean installation must be usable without synthetic seeding or
an operational warm-up procedure.

**Independent Test**: Start with empty app-owned storage, a controlled structure service,
and a recording market-data source. Open one market view and inspect the created cache
and the exact acquisition set.

**Acceptance Scenarios**:

1. **Given** no observation cache and valid structure, **When** the initial view opens,
   **Then** the app creates its cache and requests only that view's required price,
   benchmark, and representation observations.
2. **Given** stock financials or company research have not been explicitly requested,
   **When** the initial view loads, **Then** creating the cache does not trigger those
   acquisitions or prefetch unrelated stocks.
3. **Given** a failed acquisition or an unwritable cache directory, **When** initialization
   is attempted, **Then** the app shows the affected operation and a retry or corrective
   action; it does not report an empty successful dataset or seed fixture data.
4. **Given** some required listings return valid data and others fail, **When** results
   arrive, **Then** valid observations can be retained while missing or failed coverage
   remains individually visible rather than marking the entire view complete.

---

### User Story 3 - Reuse and extend the same observations across views (Priority: P1)

As a frequent user, I want fetched stock, ETF, and index histories to survive restarts
and be reusable across industries, so that browsing is fast and new data does not require
downloading or rebuilding everything already held.

**Why this priority**: Repeated full-request downloads and classification-dependent
copies would defeat the requested performance and ongoing-snapshot behavior.

**Independent Test**: Use a recording provider and a persistent controlled cache. Browse
industry A, then overlapping industry B, return to A, restart the app, and advance the
requested date. Verify exact acquisition counts, retained observations, and rendered results.

**Acceptance Scenarios**:

1. **Given** valid cached observations for a stock, **When** the same stock is reached
   through another industry or a changed batch of symbols, **Then** its reusable coverage
   is read locally instead of fetched again merely because the navigation/request changed.
2. **Given** cached coverage for part of a requested period, **When** users request a
   longer period, **Then** the app fetches only missing or stale coverage, allowing any
   explicitly documented minimal overlap required to reconcile source revisions.
3. **Given** a successful incremental update, **When** it is retained, **Then** the app
   preserves unaffected history and does not create duplicate observations for the same
   identity, observation kind, period, and source context.
4. **Given** a restart with valid durable coverage, **When** the same view opens, **Then**
   it uses that coverage without an observation-source call.
5. **Given** concurrent sessions requesting the same missing coverage, **When** their
   loads overlap, **Then** they share the in-progress acquisition and see a coherent
   retained result rather than duplicate upstream work or partially written data.
6. **Given** a failed or interrupted update, **When** users read previously valid coverage,
   **Then** it remains intact and the update failure is distinguishable from a successful
   fresh snapshot.

---

### User Story 4 - Apply a structure change without misattributing observations (Priority: P2)

As a user, I want a reviewed structure update to reorganize existing observations without
losing their ownership or history, so that classification changes do not force refetching
and ticker reuse does not attach a predecessor's data to a new stock.

**Why this priority**: Ongoing local observations are safe only if their identity is
independent of the current hierarchy.

**Independent Test**: Publish revisions that move a stock, add an overlapping membership,
change a provider symbol, and reuse a ticker for a different issuer. Verify navigation,
cache reuse, observation eligibility, and unchanged provenance separately.

**Acceptance Scenarios**:

1. **Given** retained history and a reviewed membership move, **When** the next structure
   revision is accepted, **Then** the stock appears under its new applicable industry
   while its still-eligible observations are reused without copying or refetching them.
2. **Given** a stock removed from active membership, **When** structure updates, **Then**
   it disappears from current member lists without erasing permitted retained history
   or presenting that history as evidence of current membership.
3. **Given** a ticker reused by a different issuer or listing continuity that cannot
   be verified, **When** cached history is considered, **Then** predecessor or unverifiable
   periods are excluded and explained, not assigned by ticker alone.
4. **Given** an update while a view is being assembled, **When** the view completes,
   **Then** its hierarchy, member set, source permissions, and derived results refer to
   one accepted structure revision, never a mixture of revisions.

---

### User Story 5 - Continue honestly during a structure-service outage (Priority: P2)

As a user, I want to inspect retained data during a temporary service outage without
mistaking it for current structure or fresh market observations.

**Why this priority**: Outage resilience must not hide stale evidence or bypass source rights.

**Independent Test**: Disconnect a controlled service both with and without a validated
local structure snapshot. Verify read-only behavior, permission expiry, visible status,
and explicit recovery.

**Acceptance Scenarios**:

1. **Given** an unavailable service and a previously validated local structure snapshot,
   **When** the app opens, **Then** it permits read-only browsing of retained data and
   prominently identifies the structure revision, last successful check, and offline state.
2. **Given** neither a reachable service nor a validated structure snapshot, **When**
   the app opens, **Then** it shows a blocked setup/retry state and does not invent a
   hierarchy, read legacy administration storage, or launch whole-universe acquisition.
3. **Given** cached observations with expired display permission, **When** browsing
   offline, **Then** the app withholds restricted content and explains why; cached
   possession does not renew permission.
4. **Given** offline read-only mode, **When** users browse or attempt refresh, **Then**
   no new observation acquisition or structure mutation occurs.
5. **Given** service recovery, **When** the user retries, **Then** the app validates the
   offered revision before leaving offline mode and retains valid observations.

### Edge Cases

- Valid empty industries differ from missing, incomplete, or failed structure responses.
- Malformed, cyclic, cross-scope, incomplete, or unsupported structure revisions cannot
  replace a validated snapshot; partial downloads cannot become active.
- Multiple listings, trading currencies, provider aliases, and reused tickers cannot
  collapse into one observation identity.
- The same instrument in several industries is deduplicated without merging distinct
  tradable listings or attaching unverified company evidence.
- Delisted instruments and historical membership changes retain their effective dates;
  observation continuity is not limited to industry-membership dates.
- Expired observations, legitimate no-data periods, failed requests, and never-requested
  coverage remain distinguishable; failures are not retained as successful coverage.
- Source corrections may revise existing periods through a validated update; they must
  not append duplicate rows, mix return bases, or silently change attribution.
- Concurrent writers, process interruption, incompatible local cache versions, insufficient
  disk space, and lost connectivity preserve the last valid readable data where possible
  and surface actionable status.
- Permission revocations received from the service apply to retained data as well as future
  requests. Offline mode cannot know an unpublished change and must not imply live verification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `market-structure` MUST run and be deployable independently of the stock app
  within this repository. It MUST NOT require the stock UI, an observation cache, or a
  live observation provider to serve reviewed structure.
- **FR-002**: The service MUST be the authoritative supplier of reviewed market regions,
  sector/industry hierarchy, instrument and listing identities, dated memberships,
  ETF/index representations and benchmarks, and news-source metadata used by the app.
- **FR-003**: The service MUST supply coherent, identifiable, versioned structure snapshots
  with completeness and provenance information sufficient for independent consumer validation.
  An unchanged revision MUST be recognizable without retransferring its full contents.
- **FR-004**: The stock app MUST consume the service through an explicit versioned contract,
  not shared storage access or imports of service implementation/administration internals.
  Service maintenance MUST remain outside stock-app runtime workflows.
- **FR-005**: Both applications MUST enforce compatible identity, hierarchy, membership,
  representation, source-review, and permission rules. Unknown incompatible versions,
  broken references, and invalid candidates MUST fail visibly before activation.
- **FR-006**: The app MUST retain a validated local structure snapshot for restart and outage
  use. Replacement MUST be all-or-nothing, and every rendered view and derived result MUST
  identify the single structure revision and applicable date that supplied its context.
- **FR-007**: News-source metadata MUST include stable identity, location, role, applicable
  scope, provenance, review state, and explicitly bounded permissions. Registration alone
  MUST NOT authorize collection, retention, or display. Credentials MUST NOT be published
  in structure snapshots or cached observation values.
- **FR-008**: The stock app MUST own acquisition and durable local retention of permitted
  stock, ETF, and index observations from its one selected approved observation provider.
  The structure service MUST NOT become a price/financial-data proxy or change provider selection.
- **FR-009**: When no local observation store exists, the app MUST create it automatically
  on first required acquisition. It MUST request only the active view's necessary coverage,
  preserve explicit financial/research load actions, and never seed synthetic observations.
- **FR-010**: Observation reuse MUST be keyed by stable instrument/listing or verified issuer
  identity as appropriate, provider/source, observation kind, frequency, currency, return
  basis, applicable continuity, and covered period. Ticker, industry path, and symbol-batch
  identity alone MUST NOT establish ownership or determine reuse.
- **FR-011**: The app MUST retain successful, permitted observations across ordinary reruns
  and process restarts and MUST reuse them across overlapping memberships and different
  request batches when their identities, coverage, freshness, and permissions remain valid.
- **FR-012**: For partial coverage, the app MUST acquire missing or stale intervals rather
  than redownload all held history. Any minimal reconciliation overlap MUST be documented
  and tested; unaffected coverage MUST remain unchanged.
- **FR-013**: Repeated acquisition of identical observations MUST be idempotent. Validated
  source corrections MUST replace affected values coherently with updated provenance,
  without duplicating periods or rewriting unrelated listings.
- **FR-014**: Each retained observation set MUST expose source, retrieval time, observation
  period, identity context, coverage, and freshness state. Freshness limits and retention
  limits MUST be explicit per observation kind and compatible with reviewed source rights.
- **FR-015**: Refresh MUST target the selected view's relevant coverage, respect rate limits
  and bounded retry behavior, and avoid repeated automatic retries on ordinary reruns.
  Failed or incomplete acquisitions MUST NOT masquerade as fresh complete snapshots.
- **FR-016**: Concurrent sessions MUST share reusable observations and equivalent in-progress
  acquisitions without sharing user selections or credentials. Interrupted updates MUST
  preserve the last committed valid coverage and report the failed operation.
- **FR-017**: Local reads MUST resolve the requested sector/industry membership to the
  relevant observations without scanning or rebuilding the entire held observation universe.
  A membership-only change MUST NOT require duplicating or reacquiring unchanged eligible data.
- **FR-018**: An unavailable structure service MUST put the app into explicitly marked
  read-only cached browsing when a validated local structure snapshot exists. It MUST
  block new acquisition and mutation in that mode, enforce known permission dates, and
  display structure-check and observation freshness separately.
- **FR-019**: Without either validated structure or a valid service response, the app MUST
  block dependent market views with setup/retry guidance rather than use embedded lists,
  fixture providers, or legacy databases.
- **FR-020**: Changing the delivery boundary MUST preserve existing overlapping/nested
  membership, issuer verification, historical continuity, navigation, score formulas, and
  representation safeguards. Structure changes MUST NOT manufacture or transfer approvals.
- **FR-021**: Deployment and migration guidance MUST distinguish service-owned reviewed
  data from app-owned structure replicas and observation caches. Any incompatible stored
  data change MUST have an explicit versioned migration or rebuild path that does not
  silently discard still-valid observations or alter production approvals.
- **FR-022**: The applications MUST demonstrate their compatibility using controlled
  end-to-end structure delivery, cold-start, incremental reuse, reclassification, restart,
  concurrent-load, invalid-revision, and outage scenarios without live external services.

### Key Entities

- **Structure Snapshot**: A complete reviewed revision, its contract version, publication
  identity, coverage, provenance, applicable dates, and validation status.
- **Classification Node and Membership**: A stable sector or nested industry and dated,
  scoped stock associations; overlapping memberships do not duplicate instrument identity.
- **Instrument, Listing, and Issuer Association**: Distinct identities for a stock, ETF,
  or index, its tradable/provider-specific listing where applicable, and independently
  verified issuer continuity where company evidence is involved.
- **Representation and Benchmark Mapping**: An explicitly reviewed association between
  a classification/market purpose and its permitted ETF, index, or stock-basket evidence.
- **News Source Registration**: Source identity and location, intended role and scope,
  review provenance, and effective collection/retention/display permissions; not article content.
- **Observation Coverage**: App-owned retained observations with identity/source context,
  covered periods, retrieval times, freshness, and known gaps.
- **Local Read Context**: One accepted structure revision and applicable date combined
  with eligible observation coverage, without storing user navigation as shared data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A controlled structure revision can be served and consumed while the other
  application's process is stopped; neither serving structure nor browsing warm retained
  observations requires a live observation-source connection.
- **SC-002**: On a clean installation, the first active view creates its cache and becomes
  usable within 5 seconds excluding external transfer/wait time, with zero acquisitions
  for instruments or financial/research evidence unrelated to that view's required data.
- **SC-003**: In an A-to-B-to-A browse across overlapping industries followed by a restart,
  valid unchanged observation coverage causes zero additional observation-source calls,
  regardless of how symbols are grouped in each request.
- **SC-004**: Extending a controlled 252-session history by five available sessions requests
  only missing/stale sessions plus any declared reconciliation overlap; unaffected retained
  observations are unchanged and duplicate observation count remains zero.
- **SC-005**: With 10,000 retained instruments and at least 252 daily observations per
  instrument, 95% of 20 warm navigation actions selecting up to 100 stocks display their
  retained view within 1 second, with no external acquisition. Measurement conditions
  and dataset shape are recorded so the result is reproducible.
- **SC-006**: Adding a controlled batch of 500 observations for already known listings
  becomes locally readable within 2 seconds after validation, excluding external-source
  wait, without rebuilding unrelated instruments' history.
- **SC-007**: All controlled reclassification, duplicate-membership, reused-ticker,
  interrupted-update, incompatible-revision, and outage scenarios preserve the expected
  identities and last valid data; none produces a mixed-revision view or false fresh success.
- **SC-008**: Two simultaneous requests for identical missing coverage cause one upstream
  acquisition and one coherent retained outcome; all affected users receive explicit failure
  status if that acquisition fails.
- **SC-009**: Every offline view identifies cached/offline status, the structure revision
  and last successful check, and observation freshness; zero offline refresh attempts
  trigger new observation-source calls or extend known permissions.

## Assumptions

- This feature changes the delivery and cache-ownership boundary, not the existing two-tab
  UI, scoring formulas, choice of live provider, or allowed classification semantics.
- The service initially supplies the same reviewed universe and permissions already
  supported by the catalog contracts. Complete global coverage and automatic classification
  are not implied by the service name.
- News sources means a reviewed source directory and permission metadata. Article ingestion,
  scraping, sentiment analysis, news aggregation, and additional research collectors are
  outside this feature.
- Existing reviewed publication/maintenance workflows remain the service's authoring inputs.
  Creating an administrative UI or automatically migrating production releases is out of scope.
- Observations remain app-owned and separate from authoritative structure. A locally retained
  structure snapshot is a consumer replica, not an independently editable authority.
- A service connection is needed for first-time structure bootstrap. Losing the service
  with no validated structure does not justify a guessed or embedded fallback universe.
- Retention means reuse within explicit freshness, permission, and retention limits, not
  unlimited licensed storage or a guarantee of current data while offline.
- The performance workload in SC-005 is a minimum controlled acceptance benchmark, not a
  commitment to fetch 10,000 instruments on startup.
- [010](../010-manifest-csv-catalogs/spec.md) retains reviewed release integrity and
  publication rules; this feature revises delivery to the stock app, not authoring file
  semantics. [012](../012-stock-industry-memberships/spec.md) retains identity, membership,
  rollup, and listing-history continuity rules; its unfinished implementation stays separate.
  [011](../011-company-risk-evidence/spec.md) retains issuer evidence and source-rights
  safeguards. [004](../004-sector-stock-explorer/spec.md) and
  [006](../006-stock-table-columns/spec.md) retain navigation, display, and explicit-load behavior.
