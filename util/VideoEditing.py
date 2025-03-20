import moviepy
from moviepy.video.tools.subtitles import SubtitlesClip
from pathlib import Path
from numbers import Number
from warnings import warn
import argparse

import util.WavFiles as wv
import util.AudioOfVideoFiles as av
import util.Correlation as corr
from util.VideoAudioAligningOrganization import get_tmp_dir_path, create_tmp_dir, delete_tmp_dir



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
    audio_fps = list(text_dir.glob("*" + audio_ext))
    if len(audio_fps) != 1:
        zero = len(audio_fps) == 0
        error_str = f"there should be exactly one audio file ({audio_ext}) in the directory, but found " + ("none" if zero else f"the following {len(audio_fps)}:")
        for fp in audio_fps:
            error_str += str(fp) + "\n"
        raise Exception(error_str)
    video_fps = list(text_dir.glob("*" + video_ext))
    if len(video_fps) != 1:
        zero = len(video_fps) == 0
        error_str = f"there should be exactly one video file ({video_ext}) in the directory, but found " + ("none" if zero else f"the following {len(video_fps)}:")
        for fp in video_fps:
            error_str += str(fp) + "\n"
        raise Exception(error_str)

    audio_fp ,= audio_fps
    video_fp ,= video_fps

    if not audio_fp.is_absolute():
        warn("audio fp is not absolute")
    if not video_fp.is_absolute():
        warn("video fp is not absolute")

    # if audio is stereo, make mono tmp file (for computing correlations)
    # if audio is stereo, use the stereo not mono file for new video

    audio_from_video_fp = av.get_tmp_fp_for_audio_from_video(video_fp)
    av.write_audio_from_video_to_new_audio_file(video_fp, audio_from_video_fp)

    if wv.audio_fp_is_stereo(audio_fp):
        assert audio_fp.parent == text_dir, audio_fp.parent
        audio_mono_output_fp = wv.get_tmp_fp_for_mono_audio(audio_fp, maintain_parent=False)
        assert audio_mono_output_fp.parent == tmp_dir_path, audio_mono_output_fp.parent
        wv.stereo_wav_to_mono(audio_fp, audio_mono_output_fp)
        audio_fp_to_correlate = audio_mono_output_fp
    else:
        audio_fp_to_correlate = audio_fp
    
    if wv.audio_fp_is_stereo(audio_from_video_fp):
        assert audio_from_video_fp.parent == tmp_dir_path, audio_from_video_fp.parent
        video_audio_mono_output_fp = wv.get_tmp_fp_for_mono_audio(audio_from_video_fp, maintain_parent=True)
        assert video_audio_mono_output_fp.parent == tmp_dir_path, video_audio_mono_output_fp.parent
        wv.stereo_wav_to_mono(audio_from_video_fp, video_audio_mono_output_fp)
        video_audio_fp_to_correlate = video_audio_mono_output_fp
    else:
        video_audio_fp_to_correlate = audio_from_video_fp

    print(f"will correlate these two audio files:\n{audio_fp_to_correlate}\n{video_audio_fp_to_correlate}")

    corr_fp = corr.get_correlation_fp(tmp_dir_path)

    if corr_fp.exists():
        print(f"all correlations already computed")
    else:
        rms_window_seconds = 0.2
        rms_window_samples = int(round(rms_window_seconds * wv.RATE))
        corr.make_correlation_file(video_audio_fp_to_correlate, audio_fp_to_correlate, rms_window_samples, corr_fp)

    best_offset_samples = corr.get_max_correlation_position(corr_fp)
    print(f"{best_offset_samples = }")

    extension_to_write = ".MTS"
    # extension_to_write = ".mp4"
    new_video_path = text_dir / (video_fp.name + "_Aligned" + extension_to_write)
    if new_video_path.exists():
        raise FileExistsError(new_video_path)

    offset_s = best_offset_samples / wv.RATE
    new_video = av.replace_audio_in_video_clip(video_fp, audio_fp, offset_s)
    # new_video = add_subtitle_to_video_clip(new_video, subtitles_path, offset_s)
    write_video_clip_to_file(new_video, new_video_path)

    # once done with everything, give user option to delete the tmp files or keep them to run script again faster next time
    delete_tmp_dir(tmp_dir_path)
