import os
import sys
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from datetime import datetime
import tempfile
import io

SYSTEM = platform.system()
VALIDATION_URL = "https://assinatura.e-notariado.org.br/validate"

# Dimensões da etiqueta física
LABEL_W = 9.0 * cm
LABEL_H = 5.8 * cm
# Área útil de texto (centralizada na etiqueta)
TEXT_W = 8.0 * cm
TEXT_H = 3.5 * cm
MARGIN_X = (LABEL_W - TEXT_W) / 2
MARGIN_Y = (LABEL_H - TEXT_H) / 2

try:
    import qrcode as qrlib
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def resource_path(filename):
    """Retorna caminho absoluto do arquivo, compatível com PyInstaller."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def make_qr_pil(size_px):
    """Gera QR Code como imagem PIL."""
    if not QR_AVAILABLE:
        return None
    qr = qrlib.QRCode(version=1, box_size=4, border=1,
                      error_correction=qrlib.constants.ERROR_CORRECT_M)
    qr.add_data(VALIDATION_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return img.resize((size_px, size_px), Image.LANCZOS)


def make_qr_buffer():
    """Gera QR Code como buffer de bytes (para ReportLab)."""
    if not QR_AVAILABLE:
        return None
    qr = qrlib.QRCode(version=1, box_size=10, border=1,
                      error_correction=qrlib.constants.ERROR_CORRECT_M)
    qr.add_data(VALIDATION_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def text_width_pil(draw, text, font):
    """Largura de texto em pixels (compatível com versões antigas do Pillow)."""
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]
        except AttributeError:
            return len(text) * 6


def get_printers():
    if SYSTEM == "Windows":
        try:
            import win32print  # type: ignore[import]
            return [p[2] for p in win32print.EnumPrinters(2)] or ["(Nenhuma impressora encontrada)"]
        except ImportError:
            return ["(win32print não instalado — execute: pip install pywin32)"]
    elif SYSTEM in ("Linux", "Darwin"):
        try:
            import subprocess
            cmd = ["lpstat", "-a"] if SYSTEM == "Linux" else ["lpstat", "-p"]
            out = subprocess.check_output(cmd, universal_newlines=True)
            idx = 0 if SYSTEM == "Linux" else 1
            printers = [l.split()[idx] for l in out.splitlines() if l]
            return printers or ["(Nenhuma impressora encontrada)"]
        except Exception:
            return ["(Nenhuma impressora encontrada)"]
    return ["(Sistema não suportado)"]


def print_file(printer_name, file_path):
    if SYSTEM == "Windows":
        abs_path = os.path.abspath(file_path)
        work_dir = os.path.dirname(abs_path)

        # Tentativa 1: ShellExecute "printto" (passa impressora diretamente)
        try:
            import win32api  # type: ignore[import]
            win32api.ShellExecute(0, "printto", abs_path, printer_name, work_dir, 0)
            return True
        except ImportError:
            messagebox.showerror("Erro", "Módulo win32print não encontrado.\nInstale com: pip install pywin32")
            return False
        except Exception:
            pass

        # Tentativa 2: define impressora padrão + ShellExecute "print"
        try:
            import win32print  # type: ignore[import]
            import win32api  # type: ignore[import]
            win32print.SetDefaultPrinter(printer_name)
            win32api.ShellExecute(0, "print", abs_path, None, work_dir, 0)
            return True
        except Exception:
            pass

        # Fallback: abre o PDF e orienta o usuário a imprimir manualmente
        try:
            os.startfile(abs_path)
        except Exception:
            pass
        messagebox.showinfo(
            "Imprimir manualmente",
            f"Impressão automática não disponível neste computador.\n\n"
            f"O PDF foi aberto — pressione Ctrl+P e selecione a impressora:\n{printer_name}"
        )
        return True
    elif SYSTEM in ("Linux", "Darwin"):
        try:
            import subprocess
            subprocess.run(["lp", "-d", printer_name, file_path], check=True)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao imprimir: {e}")
            return False
    return False


# ---------------------------------------------------------------------------
# Aplicação principal
# ---------------------------------------------------------------------------

class EtiquetaApp:
    # Tamanho do preview: proporção da etiqueta a ~143 DPI (2× 72pt)
    PREV_W = 512
    PREV_H = 330
    PREV_DPI = round(PREV_W / (9.0 / 2.54))  # ≈ 144 DPI

    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de Etiquetas E-notariado")
        self.root.geometry("740x710")
        self.root.minsize(640, 580)
        self.root.resizable(True, True)

        logo_file = resource_path("LOGO E-NOTARIADO.png")
        self.logo_path = logo_file if os.path.exists(logo_file) else None

        # Variáveis dos campos
        self.codigo_var = tk.StringVar()
        self.mne_var    = tk.StringVar()
        self.cpf_var    = tk.StringVar()
        self.nome_var   = tk.StringVar()
        self.data_var   = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.hora_var   = tk.StringVar(value=datetime.now().strftime("%H:%M"))

        self._preview_job = None
        for v in (self.codigo_var, self.mne_var, self.cpf_var,
                  self.nome_var, self.data_var, self.hora_var):
            v.trace_add("write", self._schedule_preview)

        self._build_ui()
        self.update_printer_list()
        self.update_preview()

    def _schedule_preview(self, *_):
        if self._preview_job:
            self.root.after_cancel(self._preview_job)
        self._preview_job = self.root.after(350, self.update_preview)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Formulário ---
        form = ttk.LabelFrame(main, text="Dados da Etiqueta", padding=10)
        form.pack(fill=tk.X, padx=4, pady=4)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=2)

        fields = [
            ("Código de Validação:", self.codigo_var, "MNE do documento:", self.mne_var),
            ("CPF:",                  self.cpf_var,   "Nome:",             self.nome_var),
            ("Data (dd/mm/aaaa):",    self.data_var,  "Horário (hh:mm):",  self.hora_var),
        ]
        for r, (l1, v1, l2, v2) in enumerate(fields):
            ttk.Label(form, text=l1).grid(row=r, column=0, sticky=tk.W, padx=5, pady=4)
            ttk.Entry(form, textvariable=v1).grid(row=r, column=1, sticky=tk.EW, padx=5, pady=4)
            ttk.Label(form, text=l2).grid(row=r, column=2, sticky=tk.W, padx=5, pady=4)
            ttk.Entry(form, textvariable=v2).grid(row=r, column=3, sticky=tk.EW, padx=5, pady=4)

        warn_row = 3
        if not QR_AVAILABLE:
            ttk.Label(form,
                      text="Aviso: instale 'qrcode[pil]' para gerar QR Code automático  (pip install qrcode[pil])",
                      foreground="#b06000").grid(row=warn_row, column=0, columnspan=4, sticky=tk.W, padx=5, pady=2)
            warn_row += 1
        if not self.logo_path:
            ttk.Label(form,
                      text="Aviso: 'LOGO E-NOTARIADO.png' não encontrado — coloque-o na mesma pasta do programa",
                      foreground="red").grid(row=warn_row, column=0, columnspan=4, sticky=tk.W, padx=5, pady=2)

        # --- Preview ---
        prev_lf = ttk.LabelFrame(main, text="Pré-visualização da etiqueta (9,0 × 5,8 cm)", padding=8)
        prev_lf.pack(fill=tk.X, padx=4, pady=4)

        self.canvas = tk.Canvas(prev_lf, width=self.PREV_W, height=self.PREV_H,
                                bg="white", bd=1, relief=tk.SOLID)
        self.canvas.pack()

        # --- Impressão ---
        pf = ttk.LabelFrame(main, text="Impressão", padding=8)
        pf.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(pf, text="Impressora:").grid(row=0, column=0, padx=5, pady=4, sticky=tk.W)
        self.printer_combo = ttk.Combobox(pf, width=52, state="readonly")
        self.printer_combo.grid(row=0, column=1, padx=5, pady=4, sticky=tk.W)

        # --- Botões ---
        bf = ttk.Frame(main)
        bf.pack(fill=tk.X, padx=4, pady=8)
        ttk.Button(bf, text="Salvar PDF", command=self.save_label).pack(side=tk.LEFT, padx=4)
        ttk.Button(bf, text="Imprimir Etiqueta", command=self.print_label).pack(side=tk.RIGHT, padx=4)

    def update_printer_list(self):
        printers = get_printers()
        self.printer_combo['values'] = printers
        if printers:
            self.printer_combo.current(0)

    def _data(self):
        return {
            'codigo': self.codigo_var.get().strip(),
            'mne':    self.mne_var.get().strip(),
            'cpf':    self.cpf_var.get().strip(),
            'nome':   self.nome_var.get().strip(),
            'data':   self.data_var.get().strip(),
            'hora':   self.hora_var.get().strip(),
        }

    def validate_inputs(self):
        d = self._data()
        labels = {
            'codigo': 'Código de Validação', 'mne': 'MNE do documento',
            'cpf': 'CPF', 'nome': 'Nome', 'data': 'Data', 'hora': 'Horário',
        }
        missing = [labels[k] for k, v in d.items() if not v]
        if missing:
            messagebox.showwarning("Campos obrigatórios",
                                   "Por favor, preencha:\n• " + "\n• ".join(missing))
            return False
        return True

    # -----------------------------------------------------------------------
    # Geração do PDF (ReportLab — saída final)
    # -----------------------------------------------------------------------

    def generate_pdf(self, output_path):
        d = self._data()
        qr_buf = make_qr_buffer()

        c = rl_canvas.Canvas(output_path, pagesize=(LABEL_W, LABEL_H))

        # Fundo branco
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, LABEL_W, LABEL_H, fill=1, stroke=0)

        x0    = MARGIN_X
        y_top = MARGIN_Y + TEXT_H  # topo da área útil (ReportLab: y=0 embaixo)

        LOGO_SZ = 1.15 * cm
        QR_SZ   = 1.15 * cm
        LINE_H  = 2.9 * mm

        # Logo (canto superior esquerdo da área útil)
        if self.logo_path:
            c.drawImage(self.logo_path, x0, y_top - LOGO_SZ,
                        width=LOGO_SZ, height=LOGO_SZ,
                        preserveAspectRatio=True, mask='auto')

        # QR Code (canto superior direito da área útil)
        if qr_buf:
            c.drawImage(ImageReader(qr_buf),
                        x0 + TEXT_W - QR_SZ, y_top - QR_SZ,
                        width=QR_SZ, height=QR_SZ)

        # Separador vertical após logo
        sep_x = x0 + LOGO_SZ + 2.0 * mm
        c.setStrokeColorRGB(0.55, 0.55, 0.55)
        c.setLineWidth(0.4)
        c.line(sep_x - 1.2 * mm, y_top - 0.8 * mm,
               sep_x - 1.2 * mm, y_top - LOGO_SZ + 0.8 * mm)

        title_x = sep_x

        # "Manifesto de assinatura"
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(title_x, y_top - 3.8 * mm, "Manifesto de assinatura")

        # "CÓDIGO DE VALIDAÇÃO"
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(title_x, y_top - 7.5 * mm, "CÓDIGO DE VALIDAÇÃO")

        # Valor do código
        c.setFont("Helvetica", 6.5)
        c.drawString(title_x, y_top - 11.0 * mm, d['codigo'])

        # Linha divisória abaixo do cabeçalho
        div_y = y_top - LOGO_SZ - 1.5 * mm
        c.setStrokeColorRGB(0.78, 0.78, 0.78)
        c.setLineWidth(0.4)
        c.line(x0, div_y, x0 + TEXT_W, div_y)

        # --- Corpo do texto ---
        by = div_y - 2.8 * mm
        c.setFillColorRGB(0, 0, 0)

        # MNE do documento
        c.setFont("Helvetica", 6.2)
        c.drawString(x0, by, f"MNE do documento: {d['mne']}")
        by -= LINE_H

        # "Documento assinado digitalmente por:"
        c.drawString(x0, by, "Documento assinado digitalmente por:")
        by -= LINE_H

        # Check mark desenhado manualmente (✓)
        def draw_check(cx, cy):
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.65)
            c.line(cx,              cy + 0.9 * mm, cx + 0.9 * mm, cy)
            c.line(cx + 0.9 * mm,  cy,            cx + 2.3 * mm, cy + 1.8 * mm)

        draw_check(x0 + 0.5 * mm, by + 0.6 * mm)

        txt_x   = x0 + 4.2 * mm
        avail_w = TEXT_W - 4.2 * mm - QR_SZ - 1 * mm

        full_line = f"CPF {d['cpf']} | {d['nome']} em {d['data']} {d['hora']}"
        c.setFont("Helvetica", 6.2)

        if c.stringWidth(full_line, "Helvetica", 6.2) <= avail_w:
            c.drawString(txt_x, by, full_line)
            by -= LINE_H
        else:
            # Linha 1: CPF | Nome — reduz fonte se necessário
            line1 = f"CPF {d['cpf']} | {d['nome']}"
            line2 = f"em {d['data']} {d['hora']}"
            fs = 6.2
            while c.stringWidth(line1, "Helvetica", fs) > avail_w and fs > 4.2:
                fs -= 0.15
            c.setFont("Helvetica", fs)
            c.drawString(txt_x, by, line1)
            by -= LINE_H
            c.setFont("Helvetica", 6.2)
            c.drawString(txt_x, by, line2)
            by -= LINE_H

        # "Para verificar as assinaturas..."
        c.setFont("Helvetica", 5.5)
        c.drawString(x0, by,
                     "Para verificar as assinaturas leia o QR code acima ou acesse")
        by -= LINE_H * 0.88

        # URL sublinhada
        c.setFillColorRGB(0.0, 0.0, 0.7)
        c.setFont("Helvetica", 5.5)
        url_w = c.stringWidth(VALIDATION_URL, "Helvetica", 5.5)
        c.drawString(x0, by, VALIDATION_URL)
        c.setStrokeColorRGB(0.0, 0.0, 0.7)
        c.setLineWidth(0.3)
        c.line(x0, by - 0.3 * mm, x0 + url_w, by - 0.3 * mm)

        c.save()

    # -----------------------------------------------------------------------
    # Preview (Pillow — exibição em tempo real)
    # -----------------------------------------------------------------------

    def update_preview(self):
        self._preview_job = None
        self.canvas.delete("all")
        d = self._data()

        W, H  = self.PREV_W, self.PREV_H
        DPI   = self.PREV_DPI
        CPX   = DPI / 2.54   # cm → pixels
        MM_PX = CPX / 10.0   # mm → pixels

        img  = Image.new('RGB', (W, H), 'white')
        draw = ImageDraw.Draw(img)

        # Margens em pixels
        mx = round(0.5 * CPX)    # 0,5 cm
        my = round(1.15 * CPX)   # 1,15 cm
        tw = round(8.0 * CPX)    # largura da área útil

        x0, y0 = mx, my          # canto superior esquerdo da área útil

        def load_font(pt, bold=False):
            try:
                if SYSTEM == "Windows":
                    name = "arialbd.ttf" if bold else "arial.ttf"
                    path = os.path.join("C:\\Windows\\Fonts", name)
                elif SYSTEM == "Darwin":
                    path = ("/Library/Fonts/Arial Bold.ttf" if bold
                            else "/Library/Fonts/Arial.ttf")
                else:
                    sfx  = "-Bold" if bold else ""
                    path = f"/usr/share/fonts/truetype/dejavu/DejaVuSans{sfx}.ttf"
                px = max(1, round(pt * DPI / 72))
                return ImageFont.truetype(path, px)
            except Exception:
                return ImageFont.load_default()

        LOGO_SZ = round(1.15 * CPX)
        QR_SZ   = LOGO_SZ
        LINE_PX = round(2.9 * MM_PX)

        # Logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image.open(self.logo_path).convert('RGBA')
                logo = logo.resize((LOGO_SZ, LOGO_SZ), Image.LANCZOS)
                img.paste(logo, (x0, y0), logo)
            except Exception:
                pass

        # QR Code
        qr_img = make_qr_pil(QR_SZ)
        if qr_img:
            img.paste(qr_img, (x0 + tw - QR_SZ, y0))
        else:
            draw.rectangle([x0 + tw - QR_SZ, y0, x0 + tw, y0 + QR_SZ],
                           outline=(180, 180, 180))
            draw.text((x0 + tw - QR_SZ + 4, y0 + LOGO_SZ // 2 - 5),
                      "QR", fill=(180, 180, 180))

        # Separador vertical
        sep_x = x0 + LOGO_SZ + round(2.0 * MM_PX)
        draw.line([(sep_x - round(1.2 * MM_PX), y0 + 3),
                   (sep_x - round(1.2 * MM_PX), y0 + LOGO_SZ - 3)],
                  fill=(150, 150, 150), width=1)

        title_x = sep_x

        f_title = load_font(8,   bold=True)
        f_label = load_font(6.5, bold=True)
        f_code  = load_font(6.5)
        f_body  = load_font(6.2)
        f_small = load_font(5.5)

        pt_to_px = lambda pt: max(1, round(pt * DPI / 72))

        # Textos do cabeçalho
        draw.text((title_x, y0 + 2),
                  "Manifesto de assinatura", font=f_title, fill=(0, 0, 0))
        draw.text((title_x, y0 + pt_to_px(8) + 4),
                  "CÓDIGO DE VALIDAÇÃO",    font=f_label, fill=(0, 0, 0))
        draw.text((title_x, y0 + pt_to_px(8) + pt_to_px(6.5) + 8),
                  d['codigo'] or "XXXXX-XXXXX-XXXXX-XXXXX",
                  font=f_code, fill=(0, 0, 0))

        # Linha divisória
        div_y = y0 + LOGO_SZ + round(1.5 * MM_PX)
        draw.line([(x0, div_y), (x0 + tw, div_y)], fill=(190, 190, 190), width=1)

        by = div_y + round(2.8 * MM_PX)

        # MNE
        draw.text((x0, by), f"MNE do documento: {d['mne'] or '...'}", font=f_body, fill=(0, 0, 0))
        by += LINE_PX

        # "Documento assinado..."
        draw.text((x0, by), "Documento assinado digitalmente por:", font=f_body, fill=(0, 0, 0))
        by += LINE_PX

        # Check mark
        ck_x, ck_y = x0 + 2, by + pt_to_px(6.2) // 2
        draw.line([(ck_x, ck_y), (ck_x + 4, ck_y + 5)], fill=(0, 0, 0), width=1)
        draw.line([(ck_x + 4, ck_y + 5), (ck_x + 11, ck_y - 3)], fill=(0, 0, 0), width=1)

        txt_x   = x0 + round(4.2 * MM_PX)
        avail_px = tw - round(4.2 * MM_PX) - QR_SZ - round(1 * MM_PX)

        full_line = f"CPF {d['cpf']} | {d['nome']} em {d['data']} {d['hora']}"
        line_w = text_width_pil(draw, full_line, f_body)

        if line_w <= avail_px:
            draw.text((txt_x, by), full_line, font=f_body, fill=(0, 0, 0))
            by += LINE_PX
        else:
            line1 = f"CPF {d['cpf']} | {d['nome']}"
            line2 = f"em {d['data']} {d['hora']}"
            f_line1 = f_body
            pt = 6.2
            while text_width_pil(draw, line1, f_line1) > avail_px and pt > 4.2:
                pt -= 0.15
                f_line1 = load_font(pt)
            draw.text((txt_x, by), line1, font=f_line1, fill=(0, 0, 0))
            by += LINE_PX
            draw.text((txt_x, by), line2, font=f_body, fill=(0, 0, 0))
            by += LINE_PX

        draw.text((x0, by),
                  "Para verificar as assinaturas leia o QR code acima ou acesse",
                  font=f_small, fill=(0, 0, 0))
        by += round(LINE_PX * 0.88)
        draw.text((x0, by), VALIDATION_URL, font=f_small, fill=(0, 0, 180))

        # Borda da etiqueta
        draw.rectangle([(0, 0), (W - 1, H - 1)], outline=(200, 200, 200), width=1)

        # Linhas tracejadas mostrando as margens (área útil)
        for i in range(0, tw, 6):
            draw.line([(x0 + i, my - 1), (x0 + i + 3, my - 1)], fill=(210, 210, 210))
            draw.line([(x0 + i, H - my), (x0 + i + 3, H - my)], fill=(210, 210, 210))
        for i in range(0, H - 2 * my, 6):
            draw.line([(x0 - 1, my + i), (x0 - 1, my + i + 3)], fill=(210, 210, 210))
            draw.line([(x0 + tw, my + i), (x0 + tw, my + i + 3)], fill=(210, 210, 210))

        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self._tk_img)

    # -----------------------------------------------------------------------
    # Salvar / Imprimir
    # -----------------------------------------------------------------------

    def save_label(self):
        if not self.validate_inputs():
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Salvar Etiqueta como PDF",
            initialfile=f"etiqueta_{self._data()['nome'][:20].replace(' ', '_')}.pdf"
        )
        if not path:
            return
        try:
            self.generate_pdf(path)
            messagebox.showinfo("Sucesso", f"Etiqueta salva em:\n{path}")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def print_label(self):
        if not self.validate_inputs():
            return
        printer = self.printer_combo.get()
        if not printer or any(x in printer for x in
                              ("Nenhuma", "não instalado", "não encontrado", "não suportado")):
            messagebox.showwarning("Impressora", "Selecione uma impressora válida.")
            return
        tmp = os.path.join(tempfile.gettempdir(), "etiqueta_enotariado_tmp.pdf")
        try:
            self.generate_pdf(tmp)
            success = print_file(printer, tmp)
            if success:
                messagebox.showinfo("Sucesso", "Etiqueta enviada para impressão!")
        except Exception as e:
            messagebox.showerror("Erro ao imprimir", str(e))
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass


# ---------------------------------------------------------------------------

def main():
    root = tk.Tk()
    EtiquetaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
