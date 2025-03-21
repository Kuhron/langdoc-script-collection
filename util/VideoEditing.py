import moviepy
from moviepy.video.tools.subtitles import SubtitlesClip
from pathlib import Path
from numbers import Number
from warnings import warn
from typing import Tuple
import argparse

import util.WavFiles as wv
import util.AudioOfVideoFiles as av
import util.Correlation as corr
from util.VideoAudioAligningOrganization import get_tmp_dir_path, create_tmp_dir, delete_tmp_dir, get_single_audio_and_video_fps_from_text_dir
from util.FileTypeDetection import DEFAULT_AUDIO_EXTENSION, DEFAULT_VIDEO_EXTENSION
from util.SoundFileStatistics import DEFAULT_RMS_WINDOW_SECONDS, seconds_to_samples



def add_subtitle_to_video_clip(video:moviepy.VideoFileClip, subtitles_path:Path, offset_s:Number) -> moviepy.VideoFileClip:
    # this adds the subtitles to the actual video, not just text subtitles that can be turned on/off, it will actually be on the video images
    # TODO at some point, can move the subtitles into a better position and give text black background, but for now I'll just use YouTube .srt functionality

    font_path = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
    generator = lambda txt: moviepy.TextClip(text=txt, font=font_path, font_size=24, color="white")
    subtitles = SubtitlesClip(subtitles_path, make_textclip=generator)
    subtitles = subtitles.with_start(offset_s)
    new_video = moviepy.CompositeVideoClip([video, subtitles])  # without specifying subtitle position, it's just in the upper left corner
    return new_video


def write_video_clip_to_file(video:moviepy.VideoFileClip, video_path:Path) -> None:
    codec = {
        ".MTS": "h264",
    }.get(video_path.suffix)

    video.write_videofile(video_path, codec=codec)
    print(f"wrote new video to {video_path}")


def create_new_video_file_with_aligned_audio(text_dir: Path, tmp_dir_path: Path, audio_ext: str, video_ext: str):
    audio_fp, video_fp = get_single_audio_and_video_fps_from_text_dir(text_dir, audio_ext, video_ext)
    corr.make_correlation_file_from_text_dir(text_dir)
    corr_fp = corr.get_correlation_fp(tmp_dir_path)
    
    best_offset_samples = corr.get_max_correlation_position(corr_fp)
    print(f"{best_offset_samples = }")

    extension_to_write = DEFAULT_VIDEO_EXTENSION
    new_video_path = text_dir / (video_fp.name + "_Aligned" + extension_to_write)
    if new_video_path.exists():
        raise FileExistsError(new_video_path)

    offset_s = best_offset_samples / wv.RATE
    new_video = av.replace_audio_in_video_clip(video_fp, audio_fp, offset_s)
    # new_video = add_subtitle_to_video_clip(new_video, subtitles_path, offset_s)
    write_video_clip_to_file(new_video, new_video_path)

    # once done with everything, give user option to delete the tmp files or keep them to run script again faster next time
    delete_tmp_dir(tmp_dir_path)
