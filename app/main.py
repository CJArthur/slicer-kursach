import os
from pathlib import Path

from services.video_slicer import (
    burn_subtitles_into_video,
    extract_audio_from_video,
    split_video_ffmpeg,
    transcribe_with_whisperx,
)
from services.window import create_app


PRESETS = [
    "Классический",
    "Неоновый желтый",
    "Электрический синий",
    "Сказочный",
    "Глубокий фиолетовый",
    "Арбузный",
]

# Положение субтитров
SUBS_POSITION = ["Сверху", "Снизу", "По середине"]


def start_processing(state, log):
    # Берём параметры, которые пользователь ввёл в UI
    input_video = state["input_video"]
    output_folder = state["output_folder"]
    preset_name = state["preset_name"]
    subs_position = state.get("subs_position", "Снизу")

    # base_name — это имя файла без расширения (нужно для имён выходных файлов)
    base_name = os.path.splitext(os.path.basename(input_video))[0]

    # out_dir — это папка, которую выбрал пользователь
    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Имя итогового видео с субтитрами
    output_video = str(out_dir / f"{base_name}_subtitled.mp4")

    # Временный wav для whisperx
    audio_path = str(Path("temp_files") / f"{base_name}_extr_audio.wav")

    log("Загружается видео (извлекаем аудио)...")
    audio_file = extract_audio_from_video(input_video, audio_path)

    log("Переходим к транскрибации...")
    segments = transcribe_with_whisperx(
        audio_file,
        language="ru",
        model_name="large-v3",
        device="cpu",
        compute_type="int8",
        batch_size=4,
    )

    log("Накладываем субтитры...")
    burn_subtitles_into_video(
        input_video, segments, output_video, preset_name, subs_position=subs_position
    )

    # Если включена галочка, то режем уже готовое видео с субтитрами
    if state["split_enabled"] and state["split_parts"]:
        # Папка для кусочков: "<выходная папка>/<base_name>_parts"
        parts_dir = out_dir / f"{base_name}_parts"
        log(f"Нарезаем на {state['split_parts']} частей (ffmpeg)...")
        split_video_ffmpeg(
            input_video=output_video,
            output_dir=str(parts_dir),
            parts=state["split_parts"],
            filename_prefix=base_name,
            reencode=False,
        )

    log("Готово!")


def main() -> None:
    # UI создаётся отдельно, а обработка живёт в start_processing()
    root = create_app(PRESETS, SUBS_POSITION, start_processing)
    root.mainloop()


if __name__ == "__main__":
    main()