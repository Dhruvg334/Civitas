-- 0002_golden_scenario.sql
-- Pre-populated dataset matching ref/07_GOLDEN_SCENARIO_SPECIFICATION.md.
-- Three reports describing one water-leak incident near a school gate.
-- All seeded with deterministic IDs so the integration test can rely on them.
--
-- Owner: Utkarsh (backend)
-- Pre-requisites: 0001, 0002, 0003, 0004, 0005 applied.
-- Idempotent: ON CONFLICT DO NOTHING everywhere.

BEGIN;

-- ---------------------------------------------------------------------------
-- Report A: vague, no category selected
-- ---------------------------------------------------------------------------

INSERT INTO incidents (
    incident_id, category, reported_at, duplicates_seen, description,
    location_geom,
    source, status, status_updated_at, last_assessment_model,
    assigned_department, assigned_work_order_id, resolution_class
) VALUES (
    'inc-golden-A', 'water_leakage', '2026-08-07T08:42:00Z', 1,
    'Water is leaking near the school road.',
    ST_SetSRID(ST_MakePoint(85.82450, 20.29610), 4326),
    'citizen', 'submitted', '2026-08-07T08:42:00Z', NULL,
    NULL, NULL, NULL
) ON CONFLICT (incident_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Report B: close image, traffic risk
-- ---------------------------------------------------------------------------

INSERT INTO incidents (
    incident_id, category, reported_at, duplicates_seen, description,
    location_geom,
    source, status, status_updated_at, last_assessment_model,
    assigned_department, assigned_work_order_id, resolution_class
) VALUES (
    'inc-golden-B', 'water_leakage', '2026-08-07T10:11:00Z', 1,
    'Road flooding opposite the school gate. Bikes are slipping while crossing.',
    ST_SetSRID(ST_MakePoint(85.82468, 20.29635), 4326),
    'citizen', 'submitted', '2026-08-07T10:11:00Z', NULL,
    NULL, NULL, NULL
) ON CONFLICT (incident_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Report C: wrong category (citizen said pothole)
-- ---------------------------------------------------------------------------

INSERT INTO incidents (
    incident_id, category, reported_at, duplicates_seen, description,
    location_geom,
    source, status, status_updated_at, last_assessment_model,
    assigned_department, assigned_work_order_id, resolution_class
) VALUES (
    'inc-golden-C', 'pothole_road_damage', '2026-08-07T11:06:00Z', 1,
    'Large road problem near school. Please repair quickly.',
    ST_SetSRID(ST_MakePoint(85.82461, 20.29622), 4326),
    'citizen', 'submitted', '2026-08-07T11:06:00Z', NULL,
    NULL, NULL, NULL
) ON CONFLICT (incident_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Cluster: A → B with high confidence (B is the close-up "canonical")
-- Then the whole incident cluster points at A.
-- ---------------------------------------------------------------------------

UPDATE incidents SET status = 'clustered', status_updated_at = '2026-08-07T10:11:00Z'
WHERE incident_id = 'inc-golden-B';

INSERT INTO incident_links (
    link_id, incident_id, report_id, source, confidence, basis,
    created_at, created_by
) VALUES (
    'lnk-golden-A-B', 'inc-golden-A', 'inc-golden-B', 'duplicate_detector',
    0.91, '{"reason": "near_duplicate", "distance_m": 4, "time_diff_min": 89}',
    '2026-08-07T10:11:00Z', 'pavit-duplicate-v1'
) ON CONFLICT (incident_id, report_id) DO NOTHING;

INSERT INTO incident_links (
    link_id, incident_id, report_id, source, confidence, basis,
    created_at, created_by
) VALUES (
    'lnk-golden-A-C', 'inc-golden-A', 'inc-golden-C', 'duplicate_detector',
    0.78, '{"reason": "near_duplicate", "distance_m": 2, "time_diff_min": 144, "category_correction": "pothole->water_leakage"}',
    '2026-08-07T11:06:00Z', 'pavit-duplicate-v1'
) ON CONFLICT (incident_id, report_id) DO NOTHING;

UPDATE incidents SET status = 'clustered', status_updated_at = '2026-08-07T11:06:00Z'
WHERE incident_id = 'inc-golden-C';

UPDATE incidents SET duplicates_seen = 3, status = 'awaiting_review',
    status_updated_at = '2026-08-07T11:10:00Z'
WHERE incident_id = 'inc-golden-A';

-- ---------------------------------------------------------------------------
-- Severity + priority assessment (golden §8)
-- ---------------------------------------------------------------------------

INSERT INTO incident_assessments (
    assessment_id, incident_id,
    severity_score, severity_level, severity_factors,
    priority_score, priority_level, priority_factors,
    uncertainties, review_required, model_version,
    assessed_at, assessed_by
) VALUES (
    'ase-golden-A-01', 'inc-golden-A',
    78, 'high',
    '[{"name":"slip_hazard","contribution":24},{"name":"active_road_flooding","contribution":21},{"name":"school_proximity","contribution":18}]'::jsonb,
    91, 'critical',
    '[{"name":"school_proximity","contribution":18},{"name":"multiple_reports","contribution":12},{"name":"traffic_exposure","contribution":22}]'::jsonb,
    '["live department workload unavailable"]'::jsonb,
    true, 'risk-v1',
    '2026-08-07T11:15:00Z', 'pavit-risk-v1'
) ON CONFLICT (assessment_id) DO NOTHING;

UPDATE incidents SET last_assessment_model = 'risk-v1'
WHERE incident_id = 'inc-golden-A';

-- ---------------------------------------------------------------------------
-- Routing decision (golden §9)
-- ---------------------------------------------------------------------------

INSERT INTO routing_decisions (
    routing_id, incident_id, primary_department, secondary_departments,
    escalation_required, policy_references, decision_basis,
    review_required, workflow_version, routed_at, routed_by
) VALUES (
    'rte-golden-A-01', 'inc-golden-A', 'water_supply',
    ARRAY['traffic_coordination'], true,
    ARRAY['PLAY-WATER-01', 'POL-GEN-02'],
    '["active water discharge on public road","traffic safety risk near school"]'::jsonb,
    true, 'routing-v1', '2026-08-07T11:20:00Z', 'druv-routing-v1'
) ON CONFLICT (routing_id) DO NOTHING;

UPDATE incidents SET assigned_department = 'water_supply'
WHERE incident_id = 'inc-golden-A';

-- ---------------------------------------------------------------------------
-- Work order (golden §10)
-- ---------------------------------------------------------------------------

INSERT INTO work_orders (
    work_order_id, incident_id, summary, required_actions,
    suggested_resources, safety_notes,
    estimated_window_min_hours, estimated_window_max_hours, non_binding,
    status, primary_department, secondary_departments, escalation_required,
    policy_references, created_at, created_by
) VALUES (
    'wo-golden-A-01', 'inc-golden-A',
    'Inspect and stop active water leakage affecting the road near the school gate.',
    '["secure the affected road section","identify and isolate the leak source","coordinate traffic control if obstruction increases","inspect drainage after stopping the flow","upload after-evidence"]'::jsonb,
    '["water maintenance crew","road safety barriers"]'::jsonb,
    '["assess slip risk before entering the affected section"]'::jsonb,
    8, 14, true,
    'awaiting_review', 'water_supply', ARRAY['traffic_coordination'], true,
    ARRAY['PLAY-WATER-01'],
    '2026-08-07T11:25:00Z', 'druv-routing-v1'
) ON CONFLICT (work_order_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Clarification (golden §6)
-- ---------------------------------------------------------------------------

INSERT INTO clarifications (
    clarification_id, incident_id, question_id, question_text,
    decision_impact, required, asked_at, answered_at, answer_text, answered_by
) VALUES (
    'cla-golden-A-01', 'inc-golden-A', 'q-electrical-01',
    'Is the water touching any electrical pole, wire, or open electrical box?',
    ARRAY['severity','priority','routing'], false,
    '2026-08-07T09:05:00Z', '2026-08-07T09:18:00Z',
    'No electrical equipment is visible near the water.',
    'citizen-of-report-A'
) ON CONFLICT (clarification_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Agent trace (audit trail — minimal seed showing the workflow order)
-- ---------------------------------------------------------------------------

INSERT INTO agent_traces (
    trace_id, incident_id, node, model_version,
    input, output, validation_outcome, created_at
) VALUES
    ('trc-golden-A-01', 'inc-golden-A', 'duplicate_detector', 'duplicate-v1',
     '{"incident_id":"inc-golden-B"}'::jsonb,
     '{"matched_incident_id":"inc-golden-A","score":0.91}'::jsonb,
     'ok', '2026-08-07T10:11:00Z'),
    ('trc-golden-A-02', 'inc-golden-A', 'duplicate_detector', 'duplicate-v1',
     '{"incident_id":"inc-golden-C"}'::jsonb,
     '{"matched_incident_id":"inc-golden-A","score":0.78,"category_corrected":true}'::jsonb,
     'ok', '2026-08-07T11:06:00Z'),
    ('trc-golden-A-03', 'inc-golden-A', 'risk', 'risk-v1',
     '{"incident_id":"inc-golden-A"}'::jsonb,
     '{"severity":{"score":78,"level":"high"},"priority":{"score":91,"level":"critical"},"review_required":true}'::jsonb,
     'ok', '2026-08-07T11:15:00Z'),
    ('trc-golden-A-04', 'inc-golden-A', 'route', 'routing-v1',
     '{"incident_id":"inc-golden-A"}'::jsonb,
     '{"primary_department":"water_supply","secondary":["traffic_coordination"]}'::jsonb,
     'ok', '2026-08-07T11:20:00Z')
ON CONFLICT (trace_id) DO NOTHING;

COMMIT;