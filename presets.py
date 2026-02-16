# Templates for Subs
def get_subs_preset(preset_name: str, video):
    presets = {
        "classic": {
            "font": "fonts/arialmt.ttf",
            "font_size": 25,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 3,
            "size": (int(video.w * 0.85), None),
            "method": "caption"
        },
        "neon_yellow": {
            "font": "fonts/calibri.ttf",
            "font_size": 25,
            "color": "#FFD400",
            "stroke_color": "black",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption"
        },
        "electric_blue": {
            "font": "fonts/arialmt.ttf",
            "font_size": 25,
            "color": "#4FC3F7",
            "stroke_color": "#0D47A1",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption"
        },
        "story_telling": {
            "font": "fonts/Roboto.ttf",
            "font_size": 25,
            "color": "#FF6F61",
            "stroke_color": "#2B2B2B",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption"
        },
        "deep_purple": {
            "font": "fonts/Roboto.ttf",
            "font_size": 25,
            "color": "#800080",
            "stroke_color": "#FFD400",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption"
        },
        "water_melon": {
            "font": "fonts/Roboto.ttf",
            "font_size": 25,
            "color": "#7CFC00",
            "stroke_color": "#DC143C",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption"
        }
    }

    if preset_name not in presets:
        raise ValueError(
            f"Неизвестный пресет: {preset_name}. Доступные: {list(presets.keys())}"
        )

    return presets[preset_name]
