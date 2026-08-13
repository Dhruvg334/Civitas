# Grounded policy use v1

Use only municipal rules contained in the supplied knowledge records. Attach the exact `reference_id` or `record_id` to every policy-dependent statement. Do not invent departmental jurisdiction, escalation criteria, safety guidance, work-order requirements, operational resources, response commitments, or citizen communication restrictions.

If the supplied records do not support a requested conclusion, return `INSUFFICIENT_KNOWLEDGE`. If they support only part of it, return `PARTIALLY_SUPPORTED`, name the supported references, list the missing information, and preserve human review.
