-- 0001_demo_landmarks: deterministic demo-city landmarks (Phase 2 seed).
-- Mirrors DEMO_LANDMARKS in geospatial/src/civitas_geo/landmarks.py so the
-- offline LandmarkIndex and the PostGIS landmark table stay in agreement.
-- Idempotent: safe to re-run.

INSERT INTO landmarks (landmark_id, name, kind, radius_m, geom) VALUES
    ('lm-school-01', 'Sunrise Public School', 'school', 200, ST_SetSRID(ST_MakePoint(77.2090, 28.6139), 4326)),
    ('lm-school-02', 'City Model High School', 'school', 200, ST_SetSRID(ST_MakePoint(77.2190, 28.6200), 4326)),
    ('lm-hosp-01',   'Central District Hospital', 'hospital', 300, ST_SetSRID(ST_MakePoint(77.2050, 28.6100), 4326)),
    ('lm-hosp-02',   'Mother Teresa Clinic', 'hospital', 150, ST_SetSRID(ST_MakePoint(77.2150, 28.6250), 4326)),
    ('lm-junction-01', 'Kingsway Junction', 'junction', 80, ST_SetSRID(ST_MakePoint(77.2130, 28.6160), 4326)),
    ('lm-junction-02', 'Riverside Cross', 'junction', 80, ST_SetSRID(ST_MakePoint(77.2100, 28.6090), 4326)),
    ('lm-market-01', 'Old Bazaar Market', 'market', 150, ST_SetSRID(ST_MakePoint(77.2180, 28.6120), 4326)),
    ('lm-park-01',   'Municipal Park', 'park', 250, ST_SetSRID(ST_MakePoint(77.2070, 28.6180), 4326)),
    ('lm-water-01',  'Yamuna Floodplain', 'waterbody', 400, ST_SetSRID(ST_MakePoint(77.2300, 28.6050), 4326)),
    ('lm-metro-01',  'Civic Centre Metro', 'metro_station', 120, ST_SetSRID(ST_MakePoint(77.2165, 28.6190), 4326)),
    ('lm-path-01',   'School Access Pathway', 'pathway', 60, ST_SetSRID(ST_MakePoint(77.2098, 28.6143), 4326))
ON CONFLICT (landmark_id) DO NOTHING;
