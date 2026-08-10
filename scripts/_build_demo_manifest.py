import json

FILES = {
    "images": [
        # category_expected: file -> (source title, license, thumb url)
        ("pothole_road_damage", "kyiv_street_pothole.jpg", "File:A pothole in Dilova Street in Kyiv.jpg", "CC0", "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/A_pothole_in_Dilova_Street_in_Kyiv.jpg/960px-A_pothole_in_Dilova_Street_in_Kyiv.jpg"),
        ("pothole_road_damage", "bengaluru_road_potholes.jpg", "File:Potholes in Bengaluru road.jpg", "CC0", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Potholes_in_Bengaluru_road.jpg/960px-Potholes_in_Bengaluru_road.jpg"),
        ("pothole_road_damage", "montreal_villeray_pothole.jpg", "File:Pothole in Villeray, Montréal.jpg", "Public domain", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Pothole_in_Villeray%2C_Montr%C3%A9al.jpg/960px-Pothole_in_Villeray%2C_Montr%C3%A9al.jpg"),
        ("pothole_road_damage", "huntington_creek_pothole.jpg", "File:Pothole on Huntington Creek Road.JPG", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Pothole_on_Huntington_Creek_Road.JPG/960px-Pothole_on_Huntington_Creek_Road.JPG"),
        ("water_leakage", "white_plains_main_break.jpg", "File:2020 White Plains Water Main Break 20200810 (1).jpg", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/2020_White_Plains_Water_Main_Break_20200810_%281%29.jpg/960px-2020_White_Plains_Water_Main_Break_20200810_%281%29.jpg"),
        ("water_leakage", "peacock_street_main_break.jpg", "File:Peacock Street water main break 986.jpg", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Peacock_Street_water_main_break_986.jpg/960px-Peacock_Street_water_main_break_986.jpg"),
        ("water_leakage", "water_main_break_flickr.jpg", "File:Water Main Break (17099358765).jpg", "CC BY 2.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Water_Main_Break_%2817099358765%29.jpg/960px-Water_Main_Break_%2817099358765%29.jpg"),
        ("water_leakage", "burst_water_main_geograph.jpg", "File:Burst water main (geograph 2646387).jpg", "CC BY-SA 2.0", "https://upload.wikimedia.org/wikipedia/commons/8/8f/Burst_water_main_%28geograph_2646387%29.jpg"),
        ("garbage_overflow", "garbage_overflow_bin_2023.jpg", "File:Garbage Overflow 1 2023-12-29.jpeg", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Garbage_Overflow_1_2023-12-29.jpeg/960px-Garbage_Overflow_1_2023-12-29.jpeg"),
        ("garbage_overflow", "hamburg_bin_overflow.jpg", "File:Overflowing Hamburg street garbage bin.jpg", "Public domain", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Overflowing_Hamburg_street_garbage_bin.jpg/960px-Overflowing_Hamburg_street_garbage_bin.jpg"),
        ("garbage_overflow", "helsinki_bin_overflow.jpg", "File:Overflowing garbage bin in Helsinki, Finland, 2019.jpg", "CC BY-SA 2.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Overflowing_garbage_bin_in_Helsinki%2C_Finland%2C_2019.jpg/960px-Overflowing_garbage_bin_in_Helsinki%2C_Finland%2C_2019.jpg"),
        ("broken_streetlight", "streetlight_night_2012.jpg", "File:Street light 07092012..jpg", "CC BY-SA 3.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Street_light_07092012..jpg/960px-Street_light_07092012..jpg"),
        ("broken_streetlight", "streetlight_amsterdam.jpg", "File:Street light, Amsterdam.jpg", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Street_light%2C_Amsterdam.jpg/960px-Street_light%2C_Amsterdam.jpg"),
        ("broken_streetlight", "farola_barcelona.jpg", "File:Barcelona - Farola Avenida Gaudi.jpg", "CC BY-SA 3.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Barcelona_-_Farola_Avenida_Gaudi.jpg/960px-Barcelona_-_Farola_Avenida_Gaudi.jpg"),
        ("fallen_tree", "fallen_tree_leamington.jpg", "File:Fallen Tree in Dormer Place, Leamington Spa (1).jpg", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Fallen_Tree_in_Dormer_Place%2C_Leamington_Spa_%281%29.jpg/960px-Fallen_Tree_in_Dormer_Place%2C_Leamington_Spa_%281%29.jpg"),
        ("fallen_tree", "fallen_tree_1c.jpg", "File:Fallen tree - 1C.jpg", "CC0", "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Fallen_tree_-_1C.jpg/960px-Fallen_tree_-_1C.jpg"),
        ("fallen_tree", "fallen_tree_greece.jpg", "File:Fallen tree in greece.jpg", "CC0", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Fallen_tree_in_greece.jpg/960px-Fallen_tree_in_greece.jpg"),
        ("ood_control", "himalayas_snow_lake.jpg", "File:Mountains in snow, Mountain lake, Chola Valley, Nepal, Himalayas.jpg", "CC BY 4.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Mountains_in_snow%2C_Mountain_lake%2C_Chola_Valley%2C_Nepal%2C_Himalayas.jpg/960px-Mountains_in_snow%2C_Mountain_lake%2C_Chola_Valley%2C_Nepal%2C_Himalayas.jpg"),
        ("ood_control", "cat_on_snow.jpg", "File:Felis catus-cat on snow.jpg", "CC BY-SA 3.0", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Felis_catus-cat_on_snow.jpg/960px-Felis_catus-cat_on_snow.jpg"),
    ],
    "videos": [
        ("water_leakage", "flood_on_street.webm", "File:Flood on the street.webm", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/7/77/Flood_on_the_street.webm"),
        ("water_leakage", "zhengzhou_flood_streets.webm", "File:Zhengzhou streets during the flood 2021-07-20.webm", "CC BY 3.0", "https://upload.wikimedia.org/wikipedia/commons/4/4b/Zhengzhou_streets_during_the_flood_2021-07-20.webm"),
        ("water_leakage", "leaking_roof.webm", "File:Leaking roof.webm", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/3/3d/Leaking_roof.webm"),
        ("water_leakage", "water_dripping_bucket.webm", "File:Water Dripping into a Bucket in a Derelict Apartment in Canada.webm", "CC BY 4.0", "https://upload.wikimedia.org/wikipedia/commons/4/4c/Water_Dripping_into_a_Bucket_in_a_Derelict_Apartment_in_Canada.webm"),
        ("water_leakage", "ceiling_infiltration.webm", "File:Teto de gesso com infiltração.webm", "CC BY-SA 4.0", "https://upload.wikimedia.org/wikipedia/commons/9/97/Teto_de_gesso_com_infiltra%C3%A7%C3%A3o.webm"),
    ],
}

out = {"images": [], "videos": []}
for folder, rows in (("images", FILES["images"]), ("videos", FILES["videos"])):
    for expected, fname, title, license_, url in rows:
        out[folder].append(
            {
                "file": f"datasets/demo_data/{folder}/{fname}",
                "expected_category": expected,
                "source_title": title,
                "source_page": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
                "source_url": url,
                "license": license_,
            }
        )
json.dump(out, open(r"datasets/demo_data/manifest.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("manifest entries:", sum(len(v) for v in out.values()))
