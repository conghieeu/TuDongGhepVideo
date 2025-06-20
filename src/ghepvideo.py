from moviepy import VideoFileClip, concatenate_videoclips

def merge_videos(link1, link2, output_link):
    clip1 = VideoFileClip(link1)
    clip2 = VideoFileClip(link2)
    final_clip = concatenate_videoclips([clip1, clip2])
    final_clip.write_videofile(output_link, codec="libx264")
    clip1.close()
    clip2.close()
    final_clip.close()