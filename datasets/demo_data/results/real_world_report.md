# Real-world media probe — image/video analyser on open-licensed media

Generated: 2026-08-10T19:39:47.632376+00:00 by `python -m civitas_evaluation.real_world_probe`.

This probe exercises the *real-media* vision path: citizen photos are natural
images, so the probe selects the zero-shot CLIP classifier (vision-clip-v1)
when it is available (fallback: the deterministic k-NN). This report records
what the analyser *honestly* says: verdict, confidence, out-of-distribution
ratio, uncertainty notes, and structured rejections.

## Per-file results

| file | kind | expected | usable | verdict | category | conf | ood | frames | notes |
|---|---|---|---|---|---|---|---|---|---|
| datasets\demo_data\images\kyiv_street_pothole.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.997 | 1.33 | - |  |
| datasets\demo_data\images\bengaluru_road_potholes.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.9763 | 1.271 | - |  |
| datasets\demo_data\images\montreal_villeray_pothole.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.9993 | 1.264 | - |  |
| datasets\demo_data\images\huntington_creek_pothole.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.3491 | 1.84 | - | low-confidence classification: confidence 0.35 below the 0.40 floor |
| datasets\demo_data\images\white_plains_main_break.jpg | image | water_leakage | True | correct | water_leakage | 0.4737 | 1.68 | - |  |
| datasets\demo_data\images\peacock_street_main_break.jpg | image | water_leakage | True | correct | water_leakage | 0.5948 | 1.457 | - |  |
| datasets\demo_data\images\water_main_break_flickr.jpg | image | water_leakage | True | correct | water_leakage | 0.9814 | 1.716 | - |  |
| datasets\demo_data\images\burst_water_main_geograph.jpg | image | water_leakage | True | correct | water_leakage | 0.9998 | 1.209 | - |  |
| datasets\demo_data\images\garbage_overflow_bin_2023.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.6174 | 1.561 | - |  |
| datasets\demo_data\images\hamburg_bin_overflow.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.9994 | 1.362 | - |  |
| datasets\demo_data\images\helsinki_bin_overflow.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.9995 | 1.567 | - |  |
| datasets\demo_data\images\streetlight_night_2012.jpg | image | broken_streetlight | True | correct | broken_streetlight | 0.9999 | 1.401 | - |  |
| datasets\demo_data\images\streetlight_amsterdam.jpg | image | broken_streetlight | True | correct | broken_streetlight | 0.9131 | 1.762 | - |  |
| datasets\demo_data\images\farola_barcelona.jpg | image | broken_streetlight | True | correct | broken_streetlight | 0.9996 | 1.437 | - |  |
| datasets\demo_data\images\fallen_tree_leamington.jpg | image | fallen_tree | True | correct | fallen_tree | 0.8488 | 1.404 | - |  |
| datasets\demo_data\images\fallen_tree_1c.jpg | image | fallen_tree | True | correct | fallen_tree | 0.9952 | 1.523 | - |  |
| datasets\demo_data\images\fallen_tree_greece.jpg | image | fallen_tree | True | correct | fallen_tree | 0.9655 | 1.533 | - |  |
| datasets\demo_data\images\himalayas_snow_lake.jpg | image | ood_control | True | OOD-FLAGGED | water_leakage | 0.8684 | 2.083 | - | out-of-distribution media: distance ratio 2.08 above the 2.0 uncertainty floor; the category is a best-effort guess, not grounded evidence |
| datasets\demo_data\images\cat_on_snow.jpg | image | ood_control | True | OOD-FLAGGED | water_leakage | 0.7896 | 2.137 | - | out-of-distribution media: distance ratio 2.14 above the 2.0 uncertainty floor; the category is a best-effort guess, not grounded evidence |
| datasets\demo_data\videos\flood_on_street.webm | video | water_leakage | True | correct | water_leakage | 0.9418 | 1.598 | 4 |  |
| datasets\demo_data\videos\zhengzhou_flood_streets.webm | video | water_leakage | True | correct | water_leakage | 0.9716 | 1.705 | 4 |  |
| datasets\demo_data\videos\leaking_roof.webm | video | water_leakage | True | correct | water_leakage | 0.6677 | 1.759 | 4 |  |
| datasets\demo_data\videos\water_dripping_bucket.webm | video | water_leakage | True | correct | water_leakage | 0.7222 | 1.59 | 4 |  |
| datasets\demo_data\videos\ceiling_infiltration.webm | video | water_leakage | False | REJECTED | - | 0.0 | - | 0 | no usable frames after quality checks (blur/exposure) |

Totals: 24 media files — 21 correct on real-world in-domain media (model vision-clip-v1), 2 out-of-domain controls evaluated for honest flagging.

Sources and licenses: see `datasets/demo_data/manifest.json` (Wikimedia Commons, CC0 / CC BY / CC BY-SA / public domain).
