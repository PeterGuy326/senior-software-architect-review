"""Bounded in-memory extraction. No uploads, original files or XML hit disk."""
import base64
import binascii
import io
import json
import subprocess
import sys
import threading
import zipfile
from pathlib import PurePath
from xml.etree import ElementTree as ET

from fastapi import HTTPException

MAX_FILE = 2 * 1024 * 1024
MAX_TEXT = 18000
PARSERS=threading.BoundedSemaphore(2)

class DocumentError(ValueError):
    pass


def extract_local(data, extension):
    if extension == '.txt':
        for encoding in ('utf-8-sig','gb18030'):
            try:
                text=data.decode(encoding); break
            except UnicodeDecodeError:
                continue
        else:
            raise DocumentError('请将 TXT 保存为 UTF-8 编码后上传。')
        if '\x00' in text:
            raise DocumentError('文件不是可读的文本。')
    elif extension == '.docx':
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            info=archive.infolist()
            if len(info)>500 or sum(x.file_size for x in info)>12*1024*1024:
                raise DocumentError('文档内容过大，请只保留论文正文。')
            xml=archive.read('word/document.xml')
            if len(xml)>2*1024*1024 or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
                raise DocumentError('文档格式暂不支持，请另存为普通 DOCX。')
            root=ET.fromstring(xml)
            ns='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            text='\n'.join(''.join(t.text or '' for t in p.iter(ns+'t'))
                           for p in root.iter(ns+'p'))
    elif extension == '.pdf':
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(data),strict=False)
        if reader.is_encrypted:
            raise DocumentError('请先移除 PDF 密码，再上传。')
        if len(reader.pages)>20:
            raise DocumentError('请只上传论文正文，最多 20 页。')
        parts=[]
        for page in reader.pages:
            content=page.get_contents()
            if content and len(content.get_data())>2*1024*1024:
                raise DocumentError('PDF 页面过于复杂，请改传 Word 或 TXT。')
            parts.append(page.extract_text() or '')
            if sum(map(len,parts))>MAX_TEXT:
                raise DocumentError('正文较长，请控制在 18000 字以内。')
        text='\n'.join(parts)
    else:
        raise DocumentError('请选择 DOCX、文字版 PDF 或 TXT 文件。')
    text=text.strip()
    if len(text)>MAX_TEXT:
        raise DocumentError('正文较长，请控制在 18000 字以内。')
    if len(''.join(text.split()))<100:
        raise DocumentError('可识别正文不足 100 字；扫描或图片 PDF 请改传 Word 或文字版 PDF。')
    return text


def extract_document(filename, encoded):
    extension=PurePath(filename.lower()).suffix
    if extension not in {'.docx','.pdf','.txt'}:
        raise HTTPException(422,'请选择 DOCX、文字版 PDF 或 TXT 文件。')
    try:
        data=base64.b64decode(encoded,validate=True)
    except (ValueError,binascii.Error):
        raise HTTPException(422,'文件传输不完整，请重新选择。') from None
    if not 1<=len(data)<=MAX_FILE:
        raise HTTPException(413,'请选择 2 MB 以内的论文文件。')
    # A separate process bounds PDF/ZIP decompression, malformed parsers and CPU.
    # stdin/stdout pipes carry private content; never echo parser exceptions.
    if not PARSERS.acquire(blocking=False):
        raise HTTPException(429,'当前解析的文稿较多，请稍后重试。')
    try:
        result=subprocess.run([sys.executable,'-m','apps.api.documents',extension],input=data,
                              capture_output=True,timeout=8,check=False)
        parsed=json.loads(result.stdout)
        if result.returncode or not isinstance(parsed.get('text'),str):
            raise DocumentError(parsed.get('error') or '文件无法读取，请另存为 DOCX 或 TXT 后重试。')
        return parsed['text']
    except (subprocess.TimeoutExpired,json.JSONDecodeError,ValueError) as error:
        message=str(error) if isinstance(error,ValueError) else '文档解析未完成，请改传 Word 或 TXT。'
        raise HTTPException(422,message[:160]) from None
    finally:
        PARSERS.release()


if __name__=='__main__':
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(384*1024*1024,384*1024*1024))
            resource.setrlimit(resource.RLIMIT_CPU,(8,8))
        print(json.dumps({'text':extract_local(sys.stdin.buffer.read(MAX_FILE+1),sys.argv[1])}))
    except DocumentError as error:
        print(json.dumps({'error':str(error)[:160]}));sys.exit(1)
    except Exception:
        print(json.dumps({'error':'文件无法读取，请另存为 DOCX 或 TXT 后重试。'}));sys.exit(1)

