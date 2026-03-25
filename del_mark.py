import subprocess

#make schema of frame
# ffmpeg -i input.mp4 -vf "drawgrid=width=100:height=100:color=red@0.3" -frames:v 1 test.png
subprocess.run(["ffmpeg",
                "-i",
                "Police Interrogation_ The Lois Case - Smoking Gun Found!.mp4",
                "-vf",
                "drawgrid=width=100:height=100:color=red@0.3",
                "-frames:v",
                "1",
                "test.png"])

# make overlay video
subprocess.run(["ffmpeg",
                "-i",
                "Police Interrogation_ The Lois Case - Smoking Gun Found!.mp4",
                "-stream_loop",
                "-1",
                "-i",
                "overlay.mp4",
                "-filter_complex",
                "[1:v]scale=900:650[ovr];[0:v][ovr]overlay=(main_w-overlay_w)/2:5",
                "-shortest",
                "output.mp4"])

# #delete watermark
#delogo=x=100:y=100:w=500:h=300:enable='gte(t,7.3)'
subprocess.run(["ffmpeg", 
                "-i", 
                "output.mp4", 
                "-vf", 
                "delogo=x=70:y=654:w=150:h=46:enable='between(t,4,7.3)'",
                "output_new.mp4"])