import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import patch, MagicMock
from src.VideoMerger import VideoMerger
from moviepy import VideoFileClip, concatenate_videoclips

@pytest.fixture
def merger(tmp_path):
    return VideoMerger(str(tmp_path))

@patch("src.VideoMerger.os.path.exists", return_value=True)
@patch("src.VideoMerger.VideoFileClip")
def test_get_video_details_success(mock_vfc, mock_exists, merger):
    mock_clip = MagicMock()
    mock_clip.size = (1280, 720)
    mock_clip.fps = 30
    mock_clip.duration = 10
    mock_vfc.return_value.__enter__.return_value = mock_clip
    size, fps, duration = merger.get_video_details("abc.mp4")
    assert size == (1280, 720)
    assert fps == 30
    assert duration == 10

def test_get_video_details_file_not_exist(merger):
    size, fps, duration = merger.get_video_details("notfound.mp4")
    assert size is None and fps is None and duration is None

@patch("src.VideoMerger.VideoFileClip")
def test_get_video_details_exception(mock_vfc, merger):
    mock_vfc.side_effect = Exception("fail")
    size, fps, duration = merger.get_video_details(__file__)
    assert size is None and fps is None and duration is None

@patch("src.VideoMerger.VideoFileClip")
@patch("src.VideoMerger.CatGhepCoBan")
def test_merge_with_audio_swap_at_start_long_audio(mock_cg, mock_vfc, merger):
    # audio dài hơn video
    merger.CG = mock_cg()
    merger.get_video_details = MagicMock(side_effect=[
        (None, None, 20),  # audio_source_path duration
        ((1280, 720), 30, 10)  # video_target_path duration
    ])
    merger.CG.mix_audio_with_video.return_value = "out.mp4"
    out = merger.merge_with_audio_swap_at_start("audio.mp3", "video.mp4")
    assert out == "out.mp4"
    merger.CG.mix_audio_with_video.assert_called_once()

@patch("src.VideoMerger.VideoFileClip")
@patch("src.VideoMerger.CatGhepCoBan")
def test_merge_with_audio_swap_at_start_short_audio(mock_cg, mock_vfc, merger):
    # audio ngắn hơn video
    merger.CG = mock_cg()
    merger.get_video_details = MagicMock(side_effect=[
        (None, None, 5),  # audio_source_path duration
        ((1280, 720), 30, 10)  # video_target_path duration
    ])
    merger.CG.extract_audio.return_value = "audio.mp3"
    merger.CG.split_video_by_time.return_value = ("part1.mp4", "part2.mp4")
    merger.CG.mix_audio_with_video.return_value = "part1_with_audio.mp4"
    mock_clip1 = MagicMock()
    mock_clip2 = MagicMock()
    mock_final = MagicMock()
    mock_vfc.side_effect = [mock_clip1, mock_clip2]
    with patch("src.VideoMerger.concatenate_videoclips", return_value=mock_final):
        out = merger.merge_with_audio_swap_at_start("audio.mp3", "video.mp4")
    assert mock_final.write_videofile.called
    assert out is not None

@patch("src.VideoMerger.CatGhepCoBan")
def test_merge_with_audio_swap_at_start_fail(mock_cg, merger):
    merger.CG = mock_cg()
    merger.get_video_details = MagicMock(return_value=(None, None, None))
    out = merger.merge_with_audio_swap_at_start("audio.mp3", "video.mp4")
    assert out is None

def test_stats_logs_created_files(merger, caplog):
    merger.created_files = ["a.mp4", "b.mp4"]
    with caplog.at_level("INFO"):
        merger.stats()
    assert "Tổng số video đã tạo: 2" in caplog.text
    assert "- a.mp4" in caplog.text
    assert "- b.mp4" in caplog.text