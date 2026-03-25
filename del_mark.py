import subprocess

#make schema of frame
# ffmpeg -i input.mp4 -vf "drawgrid=width=100:height=100:color=red@0.3" -frames:v 1 test.png
video_name = "Pumpkin Spice Latte Lover's MELTDOWN!"

subprocess.run(["ffmpeg",
                "-i",
                f"{video_name}.mp4",
                "-vf",
                "drawgrid=width=100:height=100:color=red@0.3",
                "-frames:v",
                "1",
                "test.png"])

# make overlay video
subprocess.run(["ffmpeg",
                "-i",
                f"{video_name}.mp4",
                "-stream_loop",
                "-1",
                "-i",
                "overlay.mp4",
                "-filter_complex",
                "[1:v]scale=900:600[ovr];[0:v][ovr]overlay=(main_w-overlay_w)/2:47",
                "-shortest",
                "output.mp4"])

# #delete watermark
#delogo=x=100:y=100:w=500:h=300:enable='gte(t,7.3)'
subprocess.run(["ffmpeg", 
                "-i", 
                "output.mp4", 
                "-vf", 
                "delogo=x=75:y=646:w=140:h=55:enable='between(t,4,7.3)'",
                f"{video_name}_new.mp4"])