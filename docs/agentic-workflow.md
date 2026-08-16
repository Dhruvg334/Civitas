# Agentic Workflow

Civitas uses LangGraph to coordinate a typed, checkpointed civic decision workflow. Specialized LLM stages are combined with deterministic context loading, ML tools, policy retrieval, persistence, and human review.

## Graph

```text
START
  ↓
load_context
  ↓
structure_evidence
  ↓
clarification_check
  ├─ waiting_for_clarification → interrupt
  └─ continue
  ↓
ml_intelligence
  ↓
knowledge_grounding
  ↓
routing_agent
  ↓
operational_planning
  ↓
critic
  ├─ revise_routing → routing_agent
  ├─ revise_plan → operational_planning
  ├─ human_review_required
  └─ pass
  ↓
human_review → interrupt
  ↓
citizen_communication
  ↓
END
```

## Typed workflow state

The graph state carries only the information required for downstream decisions: report/incident identifiers, structured evidence, clarification state, ML outputs, knowledge references, routing, operational plan, critic result, human-review result, citizen communication, warnings, errors, and workflow status.

Large arbitrary dictionaries are not used as the workflow contract.

## Nodes

### Context loader

Deterministically loads the stored report, media metadata, coordinates, description, selected category, incident linkage, clarification answers, and persisted analysis state.

### Evidence structuring

Combines citizen text, visual analysis, and location context into a schema that distinguishes observed evidence, reported claims, retrieved facts, inference, hazards, contradictions, and missing information.

### Clarification planner

Requests a small number of questions only when the answer can materially change an operational decision. If clarification is required, LangGraph checkpoints the state and the API exposes `WAITING_FOR_CLARIFICATION`.

### ML intelligence

Consumes the unified ML result for duplicate candidates, cluster outcome, severity, priority, model metadata, basis factors, uncertainty, and warnings. It is tool-driven rather than language-model recalculation.

### Knowledge grounding

Retrieves policy/playbook records with provenance and validates policy identifiers used by later agents.

### Routing agent

Produces primary/supporting departments, escalation requirements, policy references, rationale, uncertainty, and review requirements. Unsupported policy IDs are rejected before the routing result is accepted.

### Operational planning

Produces a structured work-order recommendation with actions, resources, safety notes, dependencies, supported time-range information, and explicit missing operational information.

### Critic

Checks evidence/inference boundaries, unsupported policy claims, routing consistency, severity/priority contradictions, duplicate implications, work-order completeness, unsupported resource/timeline claims, and review conditions. Revision loops are bounded.

### Human review

The graph checkpoints before operational approval. Authorized reviewers can approve, edit typed work-order fields, reroute through a narrow override contract, reject, or request more evidence. Resume occurs on the same `thread_id`.

### Citizen communication

Produces plain-language status communication after the workflow reaches an allowed reviewed state. It does not expose internal scores unnecessarily, hidden reasoning, or unsupported response-time promises.

## LLM provider layer

All language-model calls use the provider-neutral `LLMClient` interface. `GroqLLMClient` is the production provider implementation and `FakeLLMClient` supplies deterministic offline test/evaluation behavior. Structured results include model, latency, usage, trace ID, retry count, warnings, and provider metadata.

## Checkpointing and idempotency

Production composition uses the LangGraph PostgreSQL saver. Application workflow metadata is stored separately in `workflow_runs`; checkpoint state remains owned by LangGraph.

The runtime reuses active/completed workflow records for repeated start calls and uses replay-safe persistence for traces and business outputs. Clarification and review submissions are accepted only when the workflow is in the matching interrupt state.

## Operational boundaries

The graph makes recommendations within the evidence and policy available to the system. Jurisdiction-specific claims are returned only when the knowledge corpus contains matching jurisdiction evidence. Multi-report evidence can be represented through the incident/cluster context while each source report remains separately traceable.
