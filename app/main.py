from __future__ import annotations

import os
from pathlib import Path
from tkinter import messagebox

from services.video_slicer import (
    burn_subtitles_into_video,
    extract_audio_from_video,
    split_video_ffmpeg,
    transcribe_with_whisperx,
)
from services.window import AppWindow


PRESETS = [
    "Классический",
    "Неоновый желтый",
    "Электрический синий",
    "Сказочный",
    "Глубокий фиолетовый",
    "Арбузный",
]


def main() -> None:
    window: AppWindow

    def on_start(state) -> None:
        try:
            input_video = state["input_video"]
            output_folder = state["output_folder"]
            preset_name = state["preset_name"]

            base_name = os.path.splitext(os.path.basename(input_video))[0]
            out_dir = Path(output_folder)
            out_dir.mkdir(parents=True, exist_ok=True)

            output_video = str(out_dir / f"{base_name}_subtitled.mp4")
            audio_path = str(Path("temp_files") / f"{base_name}_extr_audio.wav")

            window.log("Загружается видео (извлекаем аудио)...")
            audio_file = extract_audio_from_video(input_video, audio_path)

            window.log("Переходим к транскрибации...")
            segments = transcribe_with_whisperx(
                audio_file,
                language="ru",
                model_name="large-v3",
                device="cpu",
                compute_type="int8",
                batch_size=4,
            )

            window.log("Накладываем субтитры...")
            burn_subtitles_into_video(input_video, segments, output_video, preset_name)

            if state["split_enabled"] and state["split_parts"]:
                parts_dir = out_dir / f"{base_name}_parts"
                window.log(f"Нарезаем на {state['split_parts']} частей (ffmpeg)...")
                split_video_ffmpeg(
                    input_video=output_video,
                    output_dir=str(parts_dir),
                    parts=state["split_parts"],
                    filename_prefix=base_name,
                    reencode=False,
                )

            window.log("Готово!")
            messagebox.showinfo("Готово", "Видео обработано!")
        except Exception as e:
            window.log(f"Произошла ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))

    window = AppWindow(presets=PRESETS, on_start=on_start)
    window.run()


if __name__ == "__main__":
    main()