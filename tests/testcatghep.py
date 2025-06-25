import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import MagicMock, patch
from src.CatGhepCoBan import CatGhepCoBan

@pytest.fixture
def cg(tmp_path):
    # Use a temp folder for file outputs
    return CatGhepCoBan(temp_folder=str(tmp_path))

def test_clear_temp_folder(cg, tmp_path):
    # Setup: create dummy files
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("x")
    file2.write_text("y")
    with patch("os.remove") as mock_remove:
        cg.clear_temp_folder()
        # Should call remove for each file
        assert mock_remove.call_count == 2

@patch("src.CatGhepCoBan.concatenate_videoclips")
@patch("src.CatGhepCoBan.VideoFileClip")
def test_merge_videos(mock_vfc, mock_concat, cg):
    mock_clip1 = MagicMock()
    mock_clip2 = MagicMock()
    mock_out = MagicMock()
    mock_vfc.side_effect = [mock_clip1, mock_clip2]
    mock_concat.return_value = mock_out
    out_path = cg.merge_videos("video1.mp4", "video2.mp4")
    mock_vfc.assert_any_call("video1.mp4")
    mock_vfc.assert_any_call("video2.mp4")
    mock_concat.assert_called_once()
    mock_out.write_videofile.assert_called_once()
    assert out_path.endswith(".mp4")

@patch("src.CatGhepCoBan.VideoFileClip")
def test_extract_audio_with_audio(mock_vfc, cg):
    mock_audio = MagicMock()
    mock_clip = MagicMock()
    mock_clip.audio = mock_audio
    mock_vfc.return_value.__enter__.return_value = mock_clip
    out = cg.extract_audio("video1.mp4")
    mock_audio.write_audiofile.assert_called_once()
    assert out.endswith(".mp3")

@patch("src.CatGhepCoBan.VideoFileClip")
def test_extract_audio_no_audio(mock_vfc, cg):
    mock_clip = MagicMock()
    mock_clip.audio = None
    mock_vfc.return_value.__enter__.return_value = mock_clip
    out = cg.extract_audio("video1.mp4")
    assert out is None

@patch("src.CatGhepCoBan.AudioFileClip")
@patch("src.CatGhepCoBan.VideoFileClip")
def test_set_audio_video(mock_vfc, mock_afc, cg):
    mock_video = MagicMock()
    mock_audio = MagicMock()
    mock_video.duration = 10
    mock_audio.duration = 15
    mock_vfc.return_value = mock_video
    mock_afc.return_value = mock_audio
    mock_video.set_audio.return_value = mock_video
    out = cg.set_audio_video("video1.mp4", "video2.mp4")
    # Sửa dòng này:
    mock_video.set_audio.assert_called_once_with(mock_audio.subclip.return_value)
    mock_video.write_videofile.assert_called_once()
    assert out.endswith(".mp4")

@patch("src.CatGhepCoBan.VideoFileClip")
def test_split_video_by_time(mock_vfc, cg):
    mock_clip = MagicMock()
    mock_clip.duration = 20
    mock_clip.subclip.side_effect = [MagicMock(), MagicMock()]
    mock_vfc.return_value.__enter__.return_value = mock_clip
    out1, out2 = cg.split_video_by_time("video1.mp4", 10)
    assert mock_clip.subclip.call_count == 2
    assert out1.endswith("part1.mp4")
    assert out2.endswith("part2.mp4")

@patch("src.CatGhepCoBan.CompositeAudioClip")
@patch("src.CatGhepCoBan.AudioFileClip")
def test_mix_two_audios(mock_afc, mock_cac, cg):
    mock_audio1 = MagicMock()
    mock_audio2 = MagicMock()
    mock_audio1.duration = 5
    mock_audio2.duration = 10
    mock_afc.side_effect = [mock_audio1, mock_audio2]
    mock_combined = MagicMock()
    mock_cac.return_value = mock_combined
    out = cg.mix_two_audios("video1.mp4", "video2.mp4", duration_limit=6)
    mock_cac.assert_called_once()
    mock_combined.write_audiofile.assert_called_once()
    assert out.endswith("_mixed.mp3")

@patch("src.CatGhepCoBan.CompositeAudioClip")
@patch("src.CatGhepCoBan.AudioFileClip")
@patch("src.CatGhepCoBan.VideoFileClip")
def test_mix_audio_with_video_has_audio(mock_vfc, mock_afc, mock_cac, cg):
    mock_video = MagicMock()
    mock_audio = MagicMock()
    mock_video.audio = MagicMock()
    mock_video.duration = 10
    mock_audio.duration = 8
    mock_vfc.return_value = mock_video
    mock_afc.return_value = mock_audio
    mock_final_audio = MagicMock()
    mock_cac.return_value = mock_final_audio
    mock_video.set_audio.return_value = mock_video
    out = cg.mix_audio_with_video("video1.mp4", "video2.mp4")
    mock_cac.assert_called_once_with([mock_video.audio, mock_audio])
    mock_video.set_audio.assert_called_once_with(mock_final_audio)
    mock_video.write_videofile.assert_called_once()
    assert out.endswith("_da_tron_am_thanh.mp4")

@patch("src.CatGhepCoBan.AudioFileClip")
@patch("src.CatGhepCoBan.VideoFileClip")
def test_mix_audio_with_video_no_audio(mock_vfc, mock_afc, cg):
    mock_video = MagicMock()
    mock_audio = MagicMock()
    mock_video.audio = None
    mock_video.duration = 10
    mock_audio.duration = 8
    mock_vfc.return_value = mock_video
    mock_afc.return_value = mock_audio
    mock_video.set_audio.return_value = mock_video
    out = cg.mix_audio_with_video("video1.mp4", "video2.mp4")
    mock_video.set_audio.assert_called_once_with(mock_audio)
    mock_video.write_videofile.assert_called_once()
    assert out.endswith("_da_tron_am_thanh.mp4")