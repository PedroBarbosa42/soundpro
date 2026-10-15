import os
import sys
import re
import shutil
import requests
import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

def obter_ffmpeg_dir():
    """
    Localiza o executável do FFmpeg de forma confiável e sem bloqueios na inicialização.
    Prioridades:
    1. Pacote do PyInstaller (sys._MEIPASS/ffmpeg)
    2. Pasta local do projeto (./ffmpeg)
    3. FFmpeg já instalado no PATH do Windows
    4. static_ffmpeg como fallback seguro
    """
    if getattr(sys, 'frozen', False):
        meipass_ffmpeg = os.path.join(getattr(sys, '_MEIPASS', ''), 'ffmpeg')
        if os.path.exists(os.path.join(meipass_ffmpeg, 'ffmpeg.exe')):
            return meipass_ffmpeg
        exe_dir_ffmpeg = os.path.join(os.path.dirname(sys.executable), 'ffmpeg')
        if os.path.exists(os.path.join(exe_dir_ffmpeg, 'ffmpeg.exe')):
            return exe_dir_ffmpeg

    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(base_dir, 'ffmpeg')
    if os.path.exists(os.path.join(local_ffmpeg, 'ffmpeg.exe')):
        return local_ffmpeg

    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        return None

    try:
        import static_ffmpeg
        static_ffmpeg.add_paths(weak=True)
    except Exception:
        pass

    return None

FFMPEG_DIR = obter_ffmpeg_dir()
if FFMPEG_DIR and FFMPEG_DIR not in os.environ.get('PATH', ''):
    os.environ['PATH'] = FFMPEG_DIR + os.pathsep + os.environ.get('PATH', '')

def sanitizar_nome(nome: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos no sistema operacional."""
    limpo = re.sub(r'[\\/*?:"<>|]', '', str(nome or '')).strip()
    return limpo if limpo else 'Faixa'

def formatar_duracao(duration_sec) -> str:
    if not duration_sec:
        return "--:--"
    mins = int(duration_sec // 60)
    secs = int(duration_sec % 60)
    return f"{mins}:{secs:02d}"

def normalizar_entrada(entrada: str):
    """
    Identifica de forma inteligente o que o usuário inseriu:
    - URL completa (YouTube, YT Music, Shorts)
    - URL sem protocolo (ex: youtube.com/watch?v=...)
    - ID de playlist (PL...)
    - ID de vídeo (11 caracteres)
    - Termo de pesquisa (ex: 'Coldplay Yellow', 'Henrique e Juliano')
    """
    entrada = (entrada or '').strip()
    if not entrada:
        raise RuntimeError("Por favor, digite o nome de uma música ou cole um link.")

    # Se já é URL completa
    if entrada.startswith('http://') or entrada.startswith('https://'):
        return entrada, False

    # Se começa com domínios conhecidos
    for dom in ['www.youtube.com', 'youtube.com', 'music.youtube.com', 'm.youtube.com', 'youtu.be']:
        if entrada.startswith(dom):
            return f"https://{entrada}", False

    # Se contém list= nos parâmetros
    if 'list=' in entrada:
        match = re.search(r'list=([a-zA-Z0-9_-]+)', entrada)
        if match:
            return f"https://www.youtube.com/playlist?list={match.group(1)}", False

    # Se é um ID de playlist com prefixo padrão
    if re.match(r'^(PL|RD|OLAK|UU|FL|LL)[a-zA-Z0-9_-]{12,}$', entrada.split('&')[0]):
        id_limpo = entrada.split('&')[0].split('?')[0]
        return f"https://www.youtube.com/playlist?list={id_limpo}", False

    # Se é um ID de vídeo padrão (11 caracteres)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', entrada.split('&')[0]):
        id_limpo = entrada.split('&')[0].split('?')[0]
        return f"https://www.youtube.com/watch?v={id_limpo}", False

    # Caso padrão: termo de busca no YouTube (retorna os 5 melhores resultados)
    return f"ytsearch5:{entrada}", True

def listar_musicas(url_ou_busca: str):
    """Detecta automaticamente se a entrada é link, playlist ou termo de busca."""
    consulta, is_search = normalizar_entrada(url_ou_busca)

    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 15,
        'nocheckcertificate': True,
    }
    if FFMPEG_DIR:
        ydl_opts['ffmpeg_location'] = FFMPEG_DIR

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(consulta, download=False)
        except Exception as e:
            err_msg = str(e)
            if "The playlist does not exist" in err_msg:
                # Tenta como busca caso o ID tenha sido colado incompleto
                try:
                    busca_fallback = f"ytsearch5:{url_ou_busca.split('&')[0]}"
                    info = ydl.extract_info(busca_fallback, download=False)
                    is_search = True
                except Exception:
                    raise RuntimeError("A playlist não existe ou é privada no YouTube. Verifique o link e tente novamente.")
            elif "Video unavailable" in err_msg or "Private video" in err_msg:
                raise RuntimeError("Este vídeo está indisponível ou é privado no YouTube.")
            else:
                raise RuntimeError(f"Erro ao analisar link: {err_msg}")

    if not info:
        raise RuntimeError("Nenhum resultado encontrado para a pesquisa ou link informado.")

    tracks_info = []

    if '_type' in info and info['_type'] == 'playlist':
        if is_search:
            playlist_title = f"Resultados para \"{url_ou_busca}\""
        else:
            playlist_title = info.get('title') or 'Playlist do YouTube'

        entries = info.get('entries') or []

        for idx, item in enumerate(entries):
            if not item:
                continue
            video_id = item.get('id')
            if not video_id:
                continue

            title = item.get('title') or f'Faixa {idx + 1}'
            uploader = item.get('uploader') or item.get('channel') or 'Desconhecido'
            thumbnails = item.get('thumbnails') or []
            thumb_url = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            tracks_info.append({
                'index': idx + 1,
                'id': video_id,
                'title': title,
                'artist': uploader,
                'album': playlist_title,
                'duration': formatar_duracao(item.get('duration')),
                'thumbnail': thumb_url,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            })

        if not tracks_info:
            raise RuntimeError("Nenhuma música disponível encontrada nessa playlist ou busca.")

        return {
            'is_single': False,
            'title': playlist_title,
            'track_count': len(tracks_info),
            'tracks': tracks_info
        }
    else:
        video_id = info.get('id')
        title = info.get('title') or 'Música'
        uploader = info.get('uploader') or info.get('channel') or 'Desconhecido'
        thumbnails = info.get('thumbnails') or []
        thumb_url = thumbnails[-1].get('url') if thumbnails else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        tracks_info.append({
            'index': 1,
            'id': video_id,
            'title': title,
            'artist': uploader,
            'album': 'Single',
            'duration': formatar_duracao(info.get('duration')),
            'thumbnail': thumb_url,
            'url': f"https://www.youtube.com/watch?v={video_id}"
        })

        return {
            'is_single': True,
            'title': title,
            'track_count': 1,
            'tracks': tracks_info
        }

def injetar_metadados_id3(caminho_mp3: str, metadata: dict):
    """Aplica metadados ID3 e imagem de capa diretamente dentro do arquivo MP3."""
    try:
        try:
            audio = EasyID3(caminho_mp3)
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.save(caminho_mp3)
        except Exception:
            audio = None

        if audio is not None:
            if metadata.get('title'):
                audio['title'] = metadata['title']
            if metadata.get('artist'):
                audio['artist'] = metadata['artist']
            if metadata.get('album'):
                audio['album'] = metadata['album']
            audio.save()

        thumb_url = metadata.get('thumbnail')
        if thumb_url:
            resp = requests.get(thumb_url, timeout=6)
            if resp.status_code == 200:
                id3 = ID3(caminho_mp3)
                id3.delall('APIC')
                id3.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=resp.content
                    )
                )
                id3.save(v2_version=3)
    except Exception:
        pass

def baixar_midia_pro(track_data: dict, diretorio_destino: str, formato: str = 'mp3') -> str:
    """Realiza o download em áudio puro MP3 (192kbps) ou vídeo MP4."""
    os.makedirs(diretorio_destino, exist_ok=True)

    artista_limpo = sanitizar_nome(track_data.get('artist', 'Artista'))
    titulo_limpo = sanitizar_nome(track_data.get('title', 'Musica'))
    nome_base = f"{artista_limpo} - {titulo_limpo}".strip(' -')
    if not nome_base:
        nome_base = f"faixa_{track_data.get('id', 'midia')}"

    extensao = 'mp3' if formato == 'mp3' else 'mp4'
    caminho_final = os.path.join(diretorio_destino, f"{nome_base}.{extensao}")

    if os.path.exists(caminho_final):
        return caminho_final

    ydl_opts = {
        'outtmpl': os.path.join(diretorio_destino, f"{nome_base}.%(ext)s"),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android']
            }
        }
    }

    if FFMPEG_DIR:
        ydl_opts['ffmpeg_location'] = FFMPEG_DIR

    if formato == 'mp3':
        ydl_opts['format'] = 'ba/b'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([track_data['url']])

    if formato == 'mp3' and os.path.exists(caminho_final):
        injetar_metadados_id3(caminho_final, track_data)

    return caminho_final