-- 0005_seed_policies.sql
-- Seeds the policies + playbooks derived from
-- ref/08_MUNICIPAL_POLICIES_AND_PLAYBOOKS_V1.md. Idempotent: safe to re-run.
--
-- Owner: Utkarsh (backend)
-- Pre-requisite: 0004_workflow_core.sql applied

-- ---------------------------------------------------------------------------
-- General policies (apply across categories)
-- ---------------------------------------------------------------------------

INSERT INTO policies
    (policy_id, code, kind, title, body, categories, departments,
     severity_factors, priority_factors, required_actions, suggested_resources)
VALUES
    ('pol-gen-01', 'POL-GEN-01', 'policy',
     'Routing must use observable evidence and category',
     'Routing decisions must be grounded in observable evidence (report text, visual analysis, geospatial context) and the incident category. When the cause is uncertain, route by the visible public-service responsibility and mark the uncertainty.',
     ARRAY[]::text[], ARRAY[]::text[],
     '[]'::jsonb, '[]'::jsonb,
     ARRAY[]::text[], ARRAY[]::text[]),

    ('pol-gen-02', 'POL-GEN-02', 'policy',
     'Electrical exposure escalates routing',
     'When water contacts electrical infrastructure (poles, wires, boxes), the routing must include electrical review as either primary, secondary, or explicit escalation.',
     ARRAY[]::text[], ARRAY['electric'],
     '[]'::jsonb, '[]'::jsonb,
     ARRAY[]::text[], ARRAY[]::text[]),

    ('pol-gen-03', 'POL-GEN-03', 'policy',
     'School/hospital/transit proximity affects priority only',
     'Proximity to schools, hospitals, transit, and high-traffic areas informs priority but does not automatically transfer department ownership.',
     ARRAY[]::text[], ARRAY[]::text[],
     '[]'::jsonb, '[]'::jsonb,
     ARRAY[]::text[], ARRAY[]::text[]),

    ('pol-gen-04', 'POL-GEN-04', 'policy',
     'Work orders must not promise exact completion time',
     'Work orders must use non-binding resolution windows. Promising a specific completion time to citizens is forbidden.',
     ARRAY[]::text[], ARRAY[]::text[],
     '[]'::jsonb, '[]'::jsonb,
     ARRAY[]::text[], ARRAY[]::text[]),

    ('pol-gen-05', 'POL-GEN-05', 'policy',
     'Critical or uncertain incidents require human approval',
     'Incidents flagged as critical (severity or priority = critical) or carrying any uncertainty must not advance past awaiting_review without reviewer sign-off.',
     ARRAY[]::text[], ARRAY[]::text[],
     '[]'::jsonb, '[]'::jsonb,
     ARRAY[]::text[], ARRAY[]::text[]),

    ('pol-gen-06', 'POL-GEN-06', 'policy',
     'Unverifiable or conflicting resolution evidence requires reviewer action',
     'Resolution submissions with classification unverifiable or conflicting_evidence cannot close the incident without reviewer intervention.',
     ARRAY[]::text[], ARRAY[]::text[],
     '[]'::jsonb, '[]'::jsonb,
     ARRAY[]::text[], ARRAY[]::text[])

ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Playbooks (category-specific)
-- ---------------------------------------------------------------------------

INSERT INTO policies
    (policy_id, code, kind, title, body, categories, departments,
     severity_factors, priority_factors, required_actions, suggested_resources)
VALUES
    ('ply-pothole-01', 'PLAY-POTHOLE-01', 'playbook',
     'Pothole playbook',
     'Primary ROAD; secondary TRAFFIC when lane obstruction or major traffic risk. Required work-order fields: location and lane, approximate visible dimensions, traffic exposure, temporary safety action, inspection and repair action.',
     ARRAY['pothole', 'pothole_road_damage'], ARRAY['road'],
     '[{"name":"depth_or_structural_damage"},{"name":"lane_coverage"},{"name":"vehicle_pedestrian_exposure"},{"name":"standing_water_hiding_damage"}]'::jsonb,
     '[{"name":"school_hospital_proximity"},{"name":"major_road_or_transport"},{"name":"repeated_reports"},{"name":"time_unresolved"}]'::jsonb,
     ARRAY['inspect damage', 'set temporary safety markers', 'schedule repair'],
     ARRAY['road maintenance crew', 'cold patch', 'safety cones']),

    ('ply-water-01', 'PLAY-WATER-01', 'playbook',
     'Water leakage and road flooding playbook',
     'Primary WATER when active public water leakage is visible or strongly supported. Secondary DRAIN for persistent standing water or drainage blockage. Secondary TRAFFIC for road obstruction or slip risk. Escalate ELECTRIC if water contacts electrical infrastructure.',
     ARRAY['water_leakage', 'road_flooding'], ARRAY['water','drain','traffic','electric'],
     '[{"name":"active_flow"},{"name":"road_coverage"},{"name":"slip_risk"},{"name":"electrical_exposure"},{"name":"property_public_health_impact"}]'::jsonb,
     '[{"name":"school_hospital_proximity"},{"name":"traffic_exposure"},{"name":"multiple_reports"},{"name":"increasing_spread"},{"name":"water_service_disruption"}]'::jsonb,
     ARRAY['secure affected road section', 'isolate leak source', 'coordinate traffic control if obstruction increases', 'inspect drainage after stopping flow', 'upload after-evidence'],
     ARRAY['water maintenance crew', 'isolation tools', 'road barriers', 'drainage support']),

    ('ply-waste-01', 'PLAY-WASTE-01', 'playbook',
     'Garbage overflow playbook',
     'Primary WASTE; secondary TRAFFIC if the road is obstructed.',
     ARRAY['garbage_overflow'], ARRAY['waste','traffic'],
     '[{"name":"road_footpath_blockage"},{"name":"sharp_or_hazardous_waste"},{"name":"animal_access"},{"name":"visible_leakage_or_burning"}]'::jsonb,
     '[{"name":"school_hospital_market_proximity"},{"name":"repeated_reports"},{"name":"time_unresolved"},{"name":"pedestrian_accessibility_impact"}]'::jsonb,
     ARRAY['secure hazardous area if necessary', 'remove accumulated waste', 'inspect container or pickup failure', 'clean affected public surface', 'upload after-evidence'],
     ARRAY['waste collection crew', 'cleaning supplies', 'hazard tape']),

    ('ply-light-01', 'PLAY-LIGHT-01', 'playbook',
     'Broken streetlight playbook',
     'Primary LIGHT; secondary ELECTRIC when exposed wiring or damaged electrical boxes are visible.',
     ARRAY['broken_streetlight'], ARRAY['light','electric'],
     '[{"name":"exposed_wires"},{"name":"damaged_pole"},{"name":"electrical_sparks"},{"name":"total_darkness_at_hazardous_crossing"}]'::jsonb,
     '[{"name":"school_route"},{"name":"pedestrian_crossing"},{"name":"transit_stop"},{"name":"repeated_reports"}]'::jsonb,
     ARRAY['inspect power and fixture', 'secure exposed electrical area', 'repair or replace component', 'confirm light operation through after-evidence'],
     ARRAY['electrical maintenance crew', 'replacement bulb/fixture']),

    ('ply-tree-01', 'PLAY-TREE-01', 'playbook',
     'Fallen tree playbook',
     'Primary PARKS; secondary ROAD or TRAFFIC when road movement is affected. Escalate ELECTRIC when wires or electrical infrastructure are involved.',
     ARRAY['fallen_tree'], ARRAY['parks','road','traffic','electric'],
     '[{"name":"complete_road_blockage"},{"name":"unstable_branches"},{"name":"vehicle_pedestrian_entrapment"},{"name":"electrical_contact"}]'::jsonb,
     '[{"name":"emergency_access_route"},{"name":"school_hospital_proximity"},{"name":"major_road"},{"name":"worsening_weather"},{"name":"multiple_reports"}]'::jsonb,
     ARRAY['secure area', 'assess electrical involvement', 'remove or stabilize tree', 'clear road or footpath', 'inspect remaining branches', 'upload after-evidence'],
     ARRAY['parks crew', 'chain saw', 'chipping equipment', 'traffic cones'])
ON CONFLICT (code) DO NOTHING;