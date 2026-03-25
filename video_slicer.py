import torch
from contextlib import contextmanager

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
import whisperx
import gc

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


# Insert subs into video
def burn_subtitles_into_video(
    video_path: str, segments, output_path: str, preset_name: str
):

    video = VideoFileClip(video_path)
    target_fps = video.fps if video.fps else 24.0

    txt_clips = []

    preset_config = get_subs_preset(preset_name, video)
    for seg in segments:

        # main subs
        subs_params = preset_config.copy()
        subs_params["text"] = seg["text"]

        start = seg["start"]
        duration = seg["end"] - seg["start"]
        pos = ("center", video.h * 0.8)

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
            .with_position(("center", video.h * 0.8))
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
