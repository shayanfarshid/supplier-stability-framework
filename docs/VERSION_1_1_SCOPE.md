# Supplier Stability Framework, Version 1.1 Scope

## What this framework is for

Supplier performance rarely breaks because one number was wrong. The harder problem is when a supplier looks healthy on a summary scorecard while commitment dates are drifting, late orders are still open, and the planning team is losing room to recover.

The Supplier Stability Framework makes that friction easier to see. It uses purchase-order history to turn a few practical delivery signals into a clearer supplier conversation.

The current Friction Index brings together four signals:

1. Late-arrival frequency
2. Open-late exposure
3. Commitment integrity
4. Delay severity

The public demonstration dashboard is available at https://supplier-stability-metrics.streamlit.app/.

## Intended use

The framework is intended for purchasing, procurement, and supplier-management teams, including lean manufacturing teams that need a practical way to review supplier delivery patterns using normal purchase-order data.

It is designed to sit next to normal OTD reporting, not replace it. A Friction Index result is most useful when it is reviewed with the underlying order lines, current business impact, and the people who know the supplier relationship.

A high score identifies a pattern that deserves review. It does not prove that the supplier caused every late or disrupted line. PO-date maintenance, internal specification or engineering changes, receiving delays, project-priority changes, and other internal workflow conditions can affect the signal.

A high score can help bring the right supplier relationship into a governance or category discussion. A critical project issue may still need immediate attention based on project impact, even if the current score looks calm.

## Current boundaries

The public dashboard uses synthetic demonstration data. It shows the workflow, fields, and logic without exposing company or supplier information.

Component criticality is still experimental in the current release. The dashboard displays component criticality, project, category, and quantity data so teams can filter and review relevant order lines. Future work will explore transparent approaches for incorporating criticality and partial-shipment quantity more directly into prioritization.

Material Discrepancy data can be reviewed alongside delivery friction to help teams see whether a supplier relationship also carries quality-event or recovery-time pressure.

## Data and review

The framework works best when purchase-order dates, receipt dates, and open-order status are maintained with care. Good data makes the discussion more useful. Human review keeps the result connected to what is actually happening in the business.

Future development will add clearer data-confidence guidance, more support for partial fulfillment, and stronger review workflows for different manufacturing environments.
