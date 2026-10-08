import json
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image

MAX_FILE = 20 * 1024 * 1024
MAX_TEXT = 120000
MAX_IMAGES = 40
ALLOWED = {'.docx','.txt','.png','.jpg','.jpeg','.webp','.wav','.mp3','.m4a','.ogg','.oga','.flac'}
AUDIO = {'.wav','.mp3','.m4a','.ogg','.oga','.flac'}


def verify_upload(path):
    path=Path(path)
    if path.suffix.lower() not in ALLOWED:
        raise ValueError('Hỗ trợ DOCX, TXT, PNG/JPG/WebP hoặc audio; không nhận DOC cũ, PDF, ZIP hay link Docs.')
    if path.stat().st_size>MAX_FILE:
        raise ValueError('Mỗi file cần nhỏ hơn hoặc bằng 20 MB.')


def image_to_png(source,target):
    with Image.open(source) as img:
        img.load()
        img.convert('RGB').save(target,'PNG')


def extract_docx(path,folder):
    """Read data only: no macros, links, embedded scripts or external resource fetches."""
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    text=[]; images=[]
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        if sum(i.file_size for i in entries)>100*1024*1024 or len(entries)>2500:
            raise ValueError('DOCX giải nén quá lớn. Chia bài thành tài liệu nhỏ hơn.')
        media=[i for i in entries if i.filename.startswith('word/media/') and not i.is_dir()]
        if any(i.filename.startswith('word/embeddings/') for i in entries):
            raise ValueError('DOCX có file nhúng/OLE. Chuyển phần đó thành chữ/ảnh PNG trước để chấm đủ.')
        if len(media)>MAX_IMAGES:
            raise ValueError(f'DOCX có hơn {MAX_IMAGES} ảnh. Chia thành nhiều bài; không cắt bỏ ảnh âm thầm.')
        for entry in entries:
            name=entry.filename
            if name.startswith('word/') and (name=='word/document.xml' or any(name.startswith('word/'+p) for p in ('header','footer','footnotes','endnotes'))):
                raw_xml=archive.read(entry)
                if b'<!DOCTYPE' in raw_xml.upper(): raise ValueError('DOCX chứa khai báo XML không được hỗ trợ.')
                root=ET.fromstring(raw_xml)
                for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    parts=[]
                    for node in p.iter():
                        if node.tag.endswith('}t') and node.text: parts.append(node.text)
                        elif node.tag.endswith('}tab'): parts.append('\t')
                        elif node.tag.endswith('}br'): parts.append('\n')
                    if parts: text.append(''.join(parts))
        for i,entry in enumerate(media,1):
            ext=Path(entry.filename).suffix.lower()
            if ext not in {'.png','.jpg','.jpeg','.gif','.bmp','.tif','.tiff','.webp'}:
                raise ValueError('DOCX chứa ảnh '+ext+' chưa đọc được. Đổi ảnh sang PNG/JPG rồi gửi lại.')
            raw=folder/f'embedded-{i}{ext}'
            raw.write_bytes(archive.read(entry))
            target=folder/f'image-{i:03d}.png'
            image_to_png(raw,target)
            images.append(str(target))
    value='\n'.join(text)
    if len(value)>MAX_TEXT:
        raise ValueError('Tài liệu quá dài (hơn 120.000 ký tự). Chia nhỏ để chấm đầy đủ.')
    if not value.strip() and not images:
        raise ValueError('DOCX không có chữ hoặc ảnh đọc được.')
    return value,images


def transcribe(path,python,model,cache):
    script=Path(__file__).with_name('speech.py')
    try:
        result=subprocess.run([python or sys.executable,str(script),str(path),model,str(cache)],
            capture_output=True,text=True,encoding='utf-8',timeout=600,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except (OSError,subprocess.TimeoutExpired):
        raise ValueError('Không chạy được bộ chép lời audio; kiểm tra Cài đặt giọng nói.') from None
    if result.returncode:
        raise ValueError('Chưa chép được audio. Cài bộ nhận giọng nói bằng INSTALL-SPEECH.ps1, hoặc thêm transcript và nộp lại; phát âm vẫn cần người nghe xác minh.')
    try:
        return json.loads(result.stdout)
    except ValueError:
        raise ValueError('Bộ chép lời audio trả dữ liệu không hợp lệ.') from None


def synthesize(text,path):
    """Render actual English listening audio with installed Windows SAPI voices."""
    path=Path(path)
    source=path.with_suffix('.speech.txt'); source.write_text(text,encoding='utf-8-sig')
    script=path.with_suffix('.speech.ps1')
    script.write_text('''param([string]$TextPath,[string]$WavePath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
$english = $voice.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'en-*' } | Select-Object -First 1
if (-not $english) { throw 'Windows chưa cài giọng đọc tiếng Anh.' }
$voice.SelectVoice($english.VoiceInfo.Name)
$voice.Rate = 0
$voice.SetOutputToWaveFile($WavePath)
$voice.Speak([System.IO.File]::ReadAllText($TextPath))
$voice.Dispose()
''',encoding='utf-8-sig')
    result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),
        '-TextPath',str(source),'-WavePath',str(path)],capture_output=True,timeout=180,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode or not path.exists() or path.stat().st_size<1000:
        raise RuntimeError('Chưa tạo được audio Listening. Cài giọng tiếng Anh trong Windows rồi thử lại.')
    return str(path)
