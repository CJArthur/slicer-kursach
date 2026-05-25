import gc
import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

import torch
import whisperx
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip

from presets import get_subs_preset


# Need to load Whisper model
@contextmanager
def torch_load_without_weights_only():
    original_load = torch.load

    def patched_load(*args, **kwargs):
        kwargs["weights_only"] = False
        return original_load(*args, **kwargs)

    torch.load = patched_load
    try:
        yield
    finally:
        torch.load = original_load


# Extract Audio from video
def extract_audio_from_video(video_path: str, audio_path: str):
    # Достаём аудио из видео в wav (для whisperx)
    os.makedirs(os.path.dirname(audio_path) or ".", exist_ok=True)
    video = VideoFileClip(video_path)
    try:
        video.audio.write_audiofile(audio_path, codec="pcm_s16le", fps=16000)
        return audio_path
    finally:
        video.close()


# Speech to text
def transcribe_with_whisperx(
    audio_path: str,
    language: str = "ru",
    model_name: str = "large-v3",
    device: str = "cpu",
    compute_type: str = "int8",
    batch_size: int = 4
):
    # Транскрипция + выравнивание по словам (whisperx)

    with torch_load_without_weights_only():
        model = whisperx.load_model(
            model_name,
            device,
            compute_type=compute_type,
            language=language,
        )

    # Transcribe
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, batch_size=batch_size, language=language)

    # Alignment of timestamps
    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"], device=device
    )

    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio,
        device,
        return_char_alignments=True,
    )

    word_segments = []

    for seg in result["segments"]:
        for w in seg["words"]:
            if w["start"] is None or w["end"] is None:
                continue

            word_segments.append(
                {"start": w["start"], "end": w["end"], "text": w["word"]}
            )

    del model_a
    gc.collect()

    return word_segments 


# Convert text to srt
def segments_to_srt(segments, srt_path: str):
    def format_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        ms = int((s - int(s)) * 1000)
        s = int(s)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")


# Расположение субтитров на видео
def _subs_vertical_anchor(subs_position: str, video_height: int):
    # Доля высоты кадра: где держать строку (по вертикали, по центру по горизонтали)
    if subs_position == "Сверху":
        frac = 0.12
    elif subs_position == "По середине":
        frac = 0.5
    else:
        # "Снизу" и всё неизвестное — как раньше, у нижней кромки
        frac = 0.8
    y = video_height * frac
    return ("center", y)


# Insert subs into video
def burn_subtitles_into_video(
    video_path: str,
    segments,
    output_path: str,
    preset_name: str,
    subs_position: str = "Снизу",
):
    # Накладываем субтитры на видео (moviepy)
    video = VideoFileClip(video_path)
    target_fps = video.fps if video.fps else 24.0

    txt_clips = []
    pos = _subs_vertical_anchor(subs_position, video.h)

    preset_config = get_subs_preset(preset_name, video)
    for seg in segments:

        # main subs
        subs_params = preset_config.copy()
        subs_params["text"] = seg["text"]

        start = seg["start"]
        duration = seg["end"] - seg["start"]

        # shadow
        shadow_params = subs_params.copy()
        shadow_params.update(
            {
                "color": subs_params["color"],
                "stroke_color": subs_params["stroke_color"],
                "stroke_width": subs_params["stroke_width"] - 1,
            }
        )

        shadow = (
            TextClip(**shadow_params)
            .with_position((pos[0], pos[1] + 4))
            .with_start(start)
            .with_duration(duration)
        )

        txt_clip = (
            TextClip(**subs_params)
            .with_position(pos)
            .with_start(seg["start"])
            .with_duration(seg["end"] - seg["start"])
        )

        txt_clips.extend([shadow, txt_clip])

    final = CompositeVideoClip([video] + txt_clips)
    final.write_videofile(
        output_path,
        codec="libx264",
        fps=target_fps,
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        threads=4,  # boost on cpu(cores count)
        bitrate="4000k",
    )

    # Close all
    final.close()
    video.close()
    del final, video
    gc.collect()


def _probe_duration_seconds(video_path: str) -> float:
    # Берём длительность видео через ffprobe (нужно для нарезки)
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    dur = float(data["format"]["duration"])
    if dur <= 0:
        raise ValueError("Не удалось определить длительность видео (ffprobe).")
    return dur


def split_video_ffmpeg(
    *,
    input_video: str,
    output_dir: str,
    parts: int,
    filename_prefix: str = "part",
    reencode: bool = False,
) -> list[str]:
    # Режем на parts кусков через ffmpeg.
    # reencode=False = быстро, но резка зависит от keyframe'ов.
    if parts < 2:
        raise ValueError("parts must be >= 2")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    duration = _probe_duration_seconds(input_video)
    piece = duration / parts

    outputs: list[str] = []
    for i in range(parts):
        start = piece * i
        seg_dur = piece if i < parts - 1 else max(0.0, duration - start)

        # Имя куска: "<prefix>_01.mp4", "<prefix>_02.mp4" и т.д.
        out_path = out_dir / f"{filename_prefix}_{i+1:02}.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-i",
            input_video,
            "-t",
            f"{seg_dur:.3f}",
        ]

        if reencode:
            cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac"]
        else:
            cmd += ["-c", "copy"]

        cmd += ["-movflags", "+faststart", str(out_path)]
        subprocess.run(cmd, check=True)
        outputs.append(str(out_path))

    return outputs