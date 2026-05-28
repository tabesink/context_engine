# Study Notes: “Don’t Confuse State with Status”

## Core idea

In domain modeling, **state** and **status** are not the same thing. **State** represents the entity’s main lifecycle phase and usually controls business logic. **Status** represents contextual details, observations, outcomes, or side effects that describe what is happening inside or around that lifecycle phase. ([Medium][1])

---

## 1. State

**State = lifecycle phase / control flow**

A state answers:

> Where is this entity in its lifecycle?

Examples:

```text
Draft
PendingPayment
Paid
Issued
Cancelled
```

A good state is:

| Property         | Meaning                                     |
| ---------------- | ------------------------------------------- |
| Exclusive        | Only one state should be active at a time   |
| Deterministic    | Used to decide what the system can do next  |
| Domain-critical  | Represents a meaningful business phase      |
| Transition-based | Changes through valid lifecycle transitions |

Example:

```csharp
if (order.State == OrderState.Paid)
{
    IssuePolicy(order);
}
```

Here, `Paid` controls whether the policy can be issued. That makes it a **state**, not just a label. ([Medium][1])

---

## 2. Status

**Status = contextual detail / observation / outcome**

A status answers:

> What exactly is happening, or what has happened, inside this lifecycle step?

Examples:

```text
GatewayRedirected
PaymentTimeout
SMSConfirmationSent
ValidationWarning
UserCancelled
```

A status is often:

| Property           | Meaning                                          |
| ------------------ | ------------------------------------------------ |
| Contextual         | Adds detail about what is happening              |
| Operational        | Useful for UI, logs, support, or monitoring      |
| Non-exclusive      | Multiple statuses can exist at once              |
| Secondary to state | Usually does not define the core lifecycle phase |

Example:

```json
{
  "state": "PendingPayment",
  "statuses": ["GatewayRedirected", "SMSConfirmationSent"]
}
```

This means the order is still in the payment phase, but extra things have happened inside that phase. ([Medium][1])

---

## 3. Key distinction

| Question                                                  | Use State or Status? |
| --------------------------------------------------------- | -------------------- |
| Does this determine what operations are allowed next?     | **State**            |
| Is this the main business lifecycle phase?                | **State**            |
| Can there only be one value at a time?                    | **State**            |
| Is this just extra context, an outcome, or a side effect? | **Status**           |
| Can multiple values apply at once?                        | **Status**           |
| Is this mostly for UI, logs, analytics, or support?       | **Status**           |

The article’s main rule is: **one entity has one state, but it can have many statuses at the same time.** ([Medium][1])

---

## 4. Example: Travel insurance order

### State model

```csharp
public enum OrderState
{
    Draft,
    PendingPayment,
    Paid,
    Issued,
    Cancelled
}
```

These are the main lifecycle stages.

### Status model

```csharp
public enum OrderStatus
{
    GatewayRedirected,
    PaymentFailed,
    PaymentSuccess,
    Timeout,
    CancelledByUser
}
```

These describe what happened during the process.

Better model:

```csharp
public class InsuranceOrder
{
    public Guid Id { get; set; }
    public OrderState State { get; set; }
    public List<OrderStatus> Statuses { get; set; } = new();
}
```

Example:

```json
{
  "state": "PendingPayment",
  "statuses": ["GatewayRedirected", "Timeout"]
}
```

Meaning:

```text
The order is still waiting for payment.
The user was redirected to the gateway.
The payment process timed out.
```

The state tells the system where the order is. The statuses explain what happened within that phase. ([Medium][1])

---

## 5. Common mistake: overloaded state enums

Bad design:

```csharp
public enum OrderState
{
    PaymentPending_GatewayRedirected,
    PaymentPending_CancelledByUser,
    PaymentPending_GatewayTimeout,
    PaymentPending_SMSConfirmationSent
}
```

Problem: this mixes lifecycle phase and contextual details into one enum.

Why this is bad:

```text
State explosion
Harder testing
Brittle business logic
Confusing transitions
Poor maintainability
Difficult UI/reporting behavior
```

Better design:

```json
{
  "state": "PendingPayment",
  "statuses": [
    "GatewayRedirected",
    "SMSConfirmationSent"
  ]
}
```

This separates the core lifecycle from supporting details. ([Medium][1])

---

## 6. Testing implication

When state and status are separated, tests become cleaner.

Example:

```csharp
[Test]
public void Should_Issue_Policy_When_State_Is_Paid()
{
    var order = new InsuranceOrder 
    { 
        State = OrderState.Paid 
    };

    Assert.True(CanIssuePolicy(order));
}
```

The test does not need to care whether the status was `PaymentSuccess`, `SMSConfirmationSent`, or something else. The business rule depends on the **state**. Status can be tested separately for logging, UI, support workflows, or integration behavior. ([Medium][1])

---

## 7. State/Status Segregation Pattern

The article names this idea the **State/Status Segregation Pattern**.

The pattern says:

```text
Use State for:
- business lifecycle
- allowed operations
- transition rules
- domain invariants

Use Status for:
- contextual metadata
- operational observations
- external outcomes
- UI messages
- logs, analytics, support diagnostics
```

This helps avoid bloated enums and keeps the model easier to extend. ([Medium][1])

---

## 8. Practical checklist

When modeling a field, ask:

```text
1. Does this value define the entity’s main lifecycle phase?
   Yes → State

2. Does this value decide what actions are allowed?
   Yes → State

3. Can the entity only have one of these at a time?
   Probably State

4. Is this just describing something that happened?
   Probably Status

5. Can multiple values apply at once?
   Probably Status

6. Is this mainly for UI, logs, analytics, or troubleshooting?
   Probably Status
```

---

## 9. Simple rule to remember

```text
State controls behavior.
Status describes context.
```

Or:

```text
State = where the entity is.
Status = what is happening around it.
```

For your own backend/domain modeling work, this distinction is especially useful for things like document ingestion, LightRAG domain lifecycle, job processing, upload progress, and retrieval workflows. For example, a document might have one lifecycle state such as `Uploaded`, `Processing`, `Indexed`, or `Failed`, while also having statuses such as `TextExtracted`, `ImagesExtracted`, `TablesExtracted`, `EmbeddingQueued`, or `RetryScheduled`.

[1]: https://masoudbahrami.medium.com/dont-confuse-state-with-status-when-modeling-domain-601bc91f326a "Don’t Confuse State with Status: Lifecycle vs. Context in Domain Modeling | by Masoud Bahrami | Medium"
