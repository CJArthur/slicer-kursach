from video_slicer import extract_audio_from_video, transcribe_with_whisperx, segments_to_srt, burn_subtitles_into_video


# start
input_video = "main_input.mp4"
audio_path = "video_voice.wav"

print("VOICE FROM VIDEO")
extract_audio_from_video(input_video, audio_path)

print("WHISPERX working")
segments = transcribe_with_whisperx(audio_path)

preset_name = "electric_blue"
burn_subtitles_into_video(input_video, segments, "Final_video", preset_name)