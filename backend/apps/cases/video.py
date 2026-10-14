import re
import subprocess
import tempfile
from pathlib import Path

import gdown
from ninja.errors import HttpError

# cobre os formatos comuns de link do Drive: /file/d/<id>/..., ?id=<id>, /open?id=<id>
_DRIVE_ID_RE = re.compile(r'/file/d/([\w-]+)|[?&]id=([\w-]+)')


def extract_drive_id(url: str) -> str | None:
    m = _DRIVE_ID_RE.search(url)
    if not m:
        return None
    return m.group(1) or m.group(2)


def fetch_as_mp4(video_url: str, dest_dir: Path) -> Path:
    """Baixa o vídeo do Drive e devolve um .mp4 (remux sem perda; recodifica só se precisar).

    WhatsApp manda .mov como documento e .mp4 como vídeo — daqui vem o requisito.
    """
    file_id = extract_drive_id(video_url)
    if not file_id:
        raise HttpError(422, 'link não é do Google Drive')

    src = dest_dir / 'src'
    try:
        gdown.download(id=file_id, output=str(src), quiet=True)
    except Exception as exc:
        raise HttpError(502, 'não consegui baixar o vídeo do Drive') from exc

    if not src.exists():
        raise HttpError(502, 'não consegui baixar o vídeo do Drive')

    dst = dest_dir / 'out.mp4'
    # -c copy: só reempacota o container (segundos). Cai pra recodificar só
    # quando o codec de origem não cabe num mp4 (ex.: vídeos mais antigos).
    remux = subprocess.run(
        ['ffmpeg', '-y', '-i', str(src), '-c', 'copy', '-movflags', '+faststart', str(dst)],
        capture_output=True,
    )
    if remux.returncode != 0:
        encode = subprocess.run(
            [
                'ffmpeg', '-y', '-i', str(src),
                '-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac',
                '-movflags', '+faststart', str(dst),
            ],
            capture_output=True,
        )
        if encode.returncode != 0:
            raise HttpError(500, 'conversão do vídeo falhou')

    return dst
