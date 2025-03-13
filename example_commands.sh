cd langdoc-script-collection
python video_audio_aligning.py example_files/MAMBU/
python video_audio_aligning.py example_files/ASER/
python video_audio_aligning.py example_files/MAMBU/ --action=video
python video_audio_aligning.py example_files/MAMBU/ --action=eaf
python video_audio_aligning.py example_files/MAMBU/ --action=txt
python video_audio_aligning.py example_files/MAMBU/ --action=srt

python -m pip install -r requirements.txt
python -m venv ~/.venvs/video-audio-aligning
source ~/.venvs/video-audio-aligning/bin/activate

