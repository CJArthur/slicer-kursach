# Templates for Subs
def get_subs_preset(preset_name: str, video):
    presets = {
        "Классический": {
            "font": "app/fonts/arialmt.ttf",
            "font_size": 30,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": 3,
            "size": (int(video.w * 0.85), None),
            "method": "caption",
        },
        "Неоновый желтый": {
            "font": "app/fonts/calibri.ttf",
            "font_size": 30,
            "color": "#FFD400",
            "stroke_color": "black",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption",
        },
        "Электрический синий": {
            "font": "app/fonts/arialmt.ttf",
            "font_size": 30,
            "color": "#4FC3F7",
            "stroke_color": "#0D47A1",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption",
        },
        "Сказочный": {
            "font": "app/fonts/Roboto.ttf",
            "font_size": 30,
            "color": "#FF6F61",
            "stroke_color": "#2B2B2B",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption",
        },
        "Глубокий фиолетовый": {
            "font": "app/fonts/Roboto.ttf",
            "font_size": 30,
            "color": "#800080",
            "stroke_color": "#FFFFFF",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption",
        },
        "Арбузный": {
            "font": "app/fonts/Roboto.ttf",
            "font_size": 30,
            "color": "#7CFC00",
            "stroke_color": "#DC143C",
            "stroke_width": 2,
            "size": (int(video.w * 0.85), None),
            "method": "caption",
        },
    }

    if preset_name not in presets:
        raise ValueError(f"Неизвестный пресет: {preset_name}. Доступные: {list(presets.keys())}")

    return presets[preset_name]
