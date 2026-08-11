# Real-world media probe — image/video analyser on real media

Generated: 2026-08-11T13:50:28.257941+00:00 by `python -m civitas_evaluation.real_world_probe`.

This probe exercises the *real-media* vision path: citizen photos are natural
images, so the probe selects the zero-shot CLIP classifier (vision-clip-v2)
when it is available (fallback: the deterministic k-NN). This report records
what the analyser *honestly* says: verdict, confidence, out-of-distribution
ratio, uncertainty notes, and structured rejections.

## Per-file results

| file | kind | expected | usable | verdict | category | conf | ood | frames | notes |
|---|---|---|---|---|---|---|---|---|---|
| kyiv_street_pothole.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.8479 | 1.33 | - |  |
| bengaluru_road_potholes.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.7771 | 1.271 | - |  |
| montreal_villeray_pothole.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.9938 | 1.264 | - |  |
| huntington_creek_pothole.jpg | image | pothole_road_damage | True | correct | pothole_road_damage | 0.2579 | 1.84 | - | low-confidence classification: confidence 0.26 below the 0.40 floor |
| white_plains_main_break.jpg | image | water_leakage | True | correct | water_leakage | 0.4205 | 1.68 | - |  |
| peacock_street_main_break.jpg | image | water_leakage | True | correct | water_leakage | 0.5765 | 1.457 | - |  |
| water_main_break_flickr.jpg | image | water_leakage | True | correct | water_leakage | 0.6067 | 1.716 | - |  |
| burst_water_main_geograph.jpg | image | water_leakage | True | correct | water_leakage | 0.9998 | 1.209 | - |  |
| garbage_overflow_bin_2023.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.466 | 1.561 | - |  |
| hamburg_bin_overflow.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.9323 | 1.362 | - |  |
| helsinki_bin_overflow.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.955 | 1.567 | - |  |
| streetlight_night_2012.jpg | image | broken_streetlight | True | correct | broken_streetlight | 0.9998 | 1.401 | - |  |
| streetlight_amsterdam.jpg | image | broken_streetlight | True | correct | broken_streetlight | 0.9101 | 1.762 | - |  |
| farola_barcelona.jpg | image | broken_streetlight | True | correct | broken_streetlight | 0.9986 | 1.437 | - |  |
| fallen_tree_leamington.jpg | image | fallen_tree | True | correct | fallen_tree | 0.8333 | 1.404 | - |  |
| fallen_tree_1c.jpg | image | fallen_tree | True | correct | fallen_tree | 0.9937 | 1.523 | - |  |
| fallen_tree_greece.jpg | image | fallen_tree | True | correct | fallen_tree | 0.952 | 1.533 | - |  |
| himalayas_snow_lake.jpg | image | ood_control | True | OOD-FLAGGED | water_leakage | 0.7795 | 2.083 | - | out-of-distribution media: distance ratio 2.08 above the 2.0 uncertainty floor; the category is a best-effort guess, not grounded evidence |
| cat_on_snow.jpg | image | ood_control | True | OOD-FLAGGED | water_leakage | 0.6023 | 2.137 | - | out-of-distribution media: distance ratio 2.14 above the 2.0 uncertainty floor; the category is a best-effort guess, not grounded evidence |
| Real_Image1.jpg | image | other_infrastructure_damage | True | correct | other_infrastructure_damage | 0.9133 | 1.317 | - |  |
| Real_Image2.jpg | image | garbage_overflow | True | correct | garbage_overflow | 0.9622 | 1.475 | - |  |
| Real_Image3.jpg | image | water_leakage | True | correct | water_leakage | 0.7681 | 1.271 | - |  |
| Real_Image4.jpg | image | drainage_damage | True | correct | drainage_damage | 0.7736 | 1.31 | - |  |
| Real_Image5.jpg | image | drainage_damage | True | correct | drainage_damage | 0.8043 | 1.388 | - |  |
| Real_Image6.jpg | image | no_incident | True | correct | no_incident | 0.9054 | 1.481 | - |  |
| flood_on_street.webm | video | water_leakage | True | correct | water_leakage | 0.9284 | 1.59 | 4 |  |
| zhengzhou_flood_streets.webm | video | water_leakage | True | correct | water_leakage | 0.9569 | 1.676 | 4 |  |
| leaking_roof.webm | video | water_leakage | True | correct | water_leakage | 0.9254 | 1.536 | 4 |  |
| water_dripping_bucket.webm | video | water_leakage | True | correct | water_leakage | 0.4652 | 1.719 | 4 |  |
| ceiling_infiltration.webm | video | water_leakage | True | correct | water_leakage | 0.9602 | 1.331 | 4 |  |
| Real_Video1.mp4 | video | pest_infestation | True | correct | pest_infestation | 0.4894 | 1.477 | 4 |  |
| Real_Video2.mp4 | video | other_infrastructure_damage | True | misclassified | water_leakage | 0.1242 | 1.531 | 4 | low-confidence classification: confidence 0.12 below the 0.40 floor |
| Real_Video3.mp4 | video | water_leakage | True | correct | water_leakage | 0.4845 | 1.559 | 4 |  |

Totals: 33 media files — 30 correct on real-world in-domain media (model vision-clip-v2), 2 out-of-domain controls evaluated for honest flagging.

Sources and licenses: see `datasets/demo_data/manifest.json` — Wikimedia Commons
(CC0 / CC BY / CC BY-SA / public domain) plus locally provided demo media whose
license is not recorded.
