"""릴스 영상 제작: 카드 이미지(1080×1350)를 세로 영상(1080×1920, 9:16)으로 이어 붙인다.
음악은 API로 넣을 수 없어 무음 트랙(AAC)을 넣는다. ffmpeg 필요."""
import shutil
import subprocess
from pathlib import Path


def _ffmpeg() -> str:
    """시스템 ffmpeg 가 없으면 pip 패키지(imageio-ffmpeg)에 들어 있는 실행파일을 쓴다."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def make_reel(images: list[Path], out: Path, sec: float = 2.5, bg: str = "0xE3F5FF") -> Path:
    images = sorted(images)
    d = images[0].parent
    total = len(images) * sec
    cmd = [_ffmpeg(), "-y", "-loglevel", "error",
           "-framerate", f"1/{sec}", "-start_number", "1", "-i", str(d / "card_%02d.jpg"),
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-vf", f"scale=1080:1350,pad=1080:1920:0:285:color={bg},format=yuv420p,fps=30",
           "-t", str(total), "-c:v", "libx264", "-profile:v", "high", "-crf", "23",
           "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", "-shortest", str(out)]
    subprocess.run(cmd, check=True)
    return out


if __name__ == "__main__":
    import sys
    d = Path(sys.argv[1])
    print(make_reel(list(d.glob("card_*.jpg")), Path(sys.argv[2])))
