#!/usr/bin/env python3
"""本地预览服务器：SPA fallback + 视频 Range。"""
import os,re
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
WWW=ROOT/'docs'
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        from urllib.parse import urlparse,unquote
        p=unquote(urlparse(path).path).lstrip('/')
        target=(WWW/p).resolve()
        if not str(target).startswith(str(WWW)): return str(WWW/'index.html')
        if target.is_file() or target.is_dir(): return str(target)
        return str(WWW/'index.html')
    def send_head(self):
        path=self.translate_path(self.path)
        if os.path.isdir(path): path=os.path.join(path,'index.html')
        try:f=open(path,'rb')
        except OSError:return self.send_error(404,'File not found')
        fs=os.fstat(f.fileno());size=fs.st_size;ctype=self.guess_type(path);rng=self.headers.get('Range')
        if rng:
            m=re.match(r'bytes=(\d*)-(\d*)',rng)
            if m:
                start=int(m.group(1) or 0);end=int(m.group(2) or size-1);end=min(end,size-1)
                if start<=end:
                    self.send_response(206);self.send_header('Content-type',ctype);self.send_header('Accept-Ranges','bytes');self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Content-Length',str(end-start+1));self.end_headers();f.seek(start);self._range=(end-start+1);return f
        self.send_response(200);self.send_header('Content-type',ctype);self.send_header('Content-Length',str(size));self.send_header('Accept-Ranges','bytes');self.end_headers();self._range=None;return f
    def copyfile(self,source,outputfile):
        remain=getattr(self,'_range',None)
        if remain is None:return super().copyfile(source,outputfile)
        while remain>0:
            buf=source.read(min(64*1024,remain))
            if not buf:break
            outputfile.write(buf);remain-=len(buf)
if __name__=='__main__':
    os.chdir(ROOT);print('本地预览：http://127.0.0.1:8899');ThreadingHTTPServer(('127.0.0.1',8899),Handler).serve_forever()
