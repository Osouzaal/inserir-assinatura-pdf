#!/usr/bin/env python3
"""Aplica a imagem PNG da fono em PDFs, preservando os originais."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
from pathlib import Path
from io import BytesIO
try:
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ImportError as exc:
    raise SystemExit("Dependencias ausentes. Instale com: py -m pip install pypdf reportlab pillow") from exc

def tem_assinatura_digital(path, reader):
    try:
        for field in (reader.get_fields() or {}).values():
            if str(field.get("/FT", "")) == "/Sig" or (field.get("/V") and field["/V"].get("/ByteRange")):
                return True
    except Exception: pass
    try: return b"/ByteRange" in path.read_bytes()
    except OSError: return False

def overlay_png(png, page_w, page_h, x, y, width):
    image=ImageReader(str(png)); iw,ih=image.getSize(); height=width*ih/iw
    if min(x,y)<0 or x+width>page_w or y+height>page_h:
        raise ValueError(f"Imagem fora da pagina: x={x:.1f}, y={y:.1f}, largura={width:.1f}, altura={height:.1f} pt")
    stream=BytesIO(); c=canvas.Canvas(stream,pagesize=(page_w,page_h),pageCompression=1)
    c.drawImage(image,x,y,width=width,height=height,mask="auto",preserveAspectRatio=True); c.save(); stream.seek(0)
    return stream

def horario_brasilia():
    try:
        tz = ZoneInfo("America/Sao_Paulo") if ZoneInfo else None
    except Exception:
        tz = None
    if tz is None:
        tz = timezone(timedelta(hours=-3))
    return datetime.now(tz).strftime("%d/%m/%Y %H:%MH")

def y_linha_assinatura(page, page_width):
    """Infere a altura da linha pelo nome do paciente no rodape direito."""
    achados=[]
    def visitor(text, cm, tm, font, font_size):
        texto=" ".join((text or "").split())
        try:
            x=float(cm[4])+float(tm[4])*float(cm[0])
            y=float(cm[5])+float(tm[5])*float(cm[3])
            size=float(font_size or 0)
        except (TypeError, ValueError, IndexError):
            return
        # Nome do paciente: texto maior, lado direito, proximo ao rodape.
        if texto and size >= 12 and x > page_width*0.55 and 40 <= y <= 160:
            achados.append(y)
    page.extract_text(visitor_text=visitor)
    if not achados:
        return None
    return max(achados)

def processar(src,dst,png,cfg,marca_data):
    if dst.exists(): return "ja existe - preservado"
    reader=PdfReader(str(src))
    if reader.is_encrypted: return "ignorado - PDF protegido por senha"
    if tem_assinatura_digital(src,reader) and not cfg.get("processar_pdfs_assinados",False):
        return "ignorado - assinatura digital detectada (a edicao a invalida)"
    n=int(cfg.get("pagina",1))-1
    if not 0<=n<len(reader.pages): return f"ignorado - pagina {n+1} inexistente"
    page=reader.pages[n]; box=page.mediabox
    # Coordenadas laterais e tamanho escalam com a pagina; altura ancora no nome do paciente.
    sx=float(box.width)/594.96; sy=float(box.height)/841.92
    nome_y=y_linha_assinatura(page,float(box.width))
    imagem_y=(nome_y+float(cfg.get("distancia_nome_imagem_pt",15))*sy) if nome_y is not None else float(cfg["y_pt"])*sy
    over=PdfReader(overlay_png(png,float(box.width),float(box.height),float(cfg["x_pt"])*sx,imagem_y,float(cfg["largura_pt"])*sx)).pages[0]
    writer=PdfWriter(); writer.clone_document_from_reader(reader)
    writer.pages[n].merge_page(over)
    # Texto discreto ao lado da imagem, alinhado acima da linha da fono.
    stamp=BytesIO(); c=canvas.Canvas(stamp,pagesize=(float(box.width),float(box.height)))
    size=float(cfg.get("data_tamanho_pt",5.5))*sx; c.setFont("Helvetica",size)
    c.drawString(float(cfg.get("data_x_pt",225))*sx,imagem_y,marca_data)
    c.save(); stamp.seek(0)
    writer.pages[n].merge_page(PdfReader(stamp).pages[0])
    writer.add_metadata({"/Subject":"Copia com imagem da fono adicionada"})
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("xb") as f: writer.write(f)
    return "criado"

def main():
    ap=argparse.ArgumentParser(description="Cria copias de PDFs com imagem PNG aplicada.")
    ap.add_argument("--config",default=str(Path(__file__).with_name("config.json")))
    args=ap.parse_args()
    try:
        cfg=json.loads(Path(args.config).expanduser().read_text(encoding="utf-8"))
        src,out,png=(Path(cfg[k]).expanduser() for k in ("pasta_pdfs","pasta_saida","imagem_png"))
        if not src.is_dir(): raise ValueError(f"Pasta de PDFs nao encontrada: {src}")
        if not png.is_file(): raise ValueError(f"Imagem PNG nao encontrada: {png}")
        out.mkdir(parents=True,exist_ok=True); pattern="**/*.pdf" if cfg.get("varrer_subpastas",False) else "*.pdf"
        files=sorted(p for p in src.glob(pattern) if p.is_file())
        if not files: print("Nenhum PDF encontrado."); return 0
        marca_data=horario_brasilia()
        print(f"Data/hora aplicada (Brasilia): {marca_data}")
        for pdf in files:
            rel=pdf.relative_to(src); dst=out/rel
            try: status=processar(pdf,dst,png,cfg,marca_data)
            except FileExistsError: status="ja existe - preservado"
            except Exception as e: status=f"ERRO - {e}"
            print(f"{status}: {rel}")
        return 0
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as e:
        print(f"Erro de configuracao: {e}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
