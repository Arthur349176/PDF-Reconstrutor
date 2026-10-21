"""PDF Reconstruction Studio (interface gráfica).  Uso:  python run_gui.py
(A linha de comando continua em:  python main.py documento.pdf)

Este arquivo só usa a biblioteca padrão até entrar no try: se QUALQUER coisa falhar ao iniciar
(PySide6 ausente, DLL do Qt, erro de importação...), o erro é gravado em logs/startup_error.log
e mostrado numa janela do Windows — nada falha em silêncio.
"""
import faulthandler
import sys
import time
import traceback
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))            # True dentro do .exe (PyInstaller)
if FROZEN:                                              # a pasta do programa pode ser somente leitura
    import os
    ROOT = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share") / "PDFReconstructionStudio"
else:
    ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"
_fault_file = None  # mantém o arquivo aberto durante toda a execução (faulthandler)


def _fatal(details: str) -> None:
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with open(LOGS / "startup_error.log", "a", encoding="utf-8") as f:
            f.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n{details}\n")
    except OSError:
        pass
    last = details.strip().splitlines()[-1] if details.strip() else "erro desconhecido"
    msg = (f"Não foi possível iniciar o PDF Reconstruction Studio.\n\n{last}\n\n"
           f"Detalhes completos em:\n{LOGS / 'startup_error.log'}\n\n"
           "Se a mensagem citar PySide6 ou 'No module named', rode:\n"
           "    pip install -r requirements.txt")
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "PDF Reconstruction Studio", 0x10)   # Windows
    except Exception:
        try:
            print(msg, file=sys.stderr)
        except Exception:
            pass


def selftest() -> int:
    """`--selftest`: sem janela. Confere se tudo foi empacotado e se o motor converte um PDF de teste."""
    import tempfile
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / "selftest.log"
    try:
        import docx
        import pymupdf
        import gui.ui.main_window  # noqa: F401  (importa toda a interface)
        from gui.services.engine_adapter import EngineReconstructionService
        from gui.services.reconstruction_service import ReconstructionSettings
        tmp = Path(tempfile.mkdtemp())
        pdf = tmp / "teste.pdf"
        d = pymupdf.open()
        d.new_page().insert_text((72, 100), "Teste do PDF Reconstruction Studio", fontsize=12)
        d.save(str(pdf))
        r = EngineReconstructionService().reconstruct(str(pdf), str(tmp / "saida.docx"), ReconstructionSettings(quality="fast"))
        text = " ".join(p.text for p in docx.Document(str(tmp / "saida.docx")).paragraphs)
        assert r.success and "Teste do PDF Reconstruction Studio" in text, text
        from gui.utils.i18n import available_languages, set_language, tr
        assert len(available_languages()) >= 6, available_languages()       # catálogos de idioma empacotados
        set_language("de")
        assert tr("Cancelar") == "Abbrechen", tr("Cancelar")
        set_language("pt_BR")
        log.write_text("OK\n", encoding="utf-8")
        return 0
    except Exception:
        log.write_text("FALHA\n" + traceback.format_exc(), encoding="utf-8")
        return 1


def main() -> int:
    global _fault_file
    if "--selftest" in sys.argv:
        return selftest()
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        _fault_file = open(LOGS / "crash.log", "a", encoding="utf-8")
        faulthandler.enable(_fault_file)           # falhas fatais do Qt/C++ também deixam rastro

        from PySide6.QtWidgets import QApplication

        from gui.utils.logger import setup_logging
        setup_logging()

        if sys.platform.startswith("win"):                  # ícone próprio na barra de tarefas (não o do Python)
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PDFReconstructionStudio.App")
            except Exception:
                pass
        app = QApplication(sys.argv)
        from PySide6.QtGui import QIcon
        from gui.utils.resources import resource_path
        app.setWindowIcon(QIcon(str(resource_path("gui/ui/resources/app.png"))))
        app.setOrganizationName("PDFReconstructionStudio")
        app.setApplicationName("PDF Reconstruction Studio")

        from gui.services import create_service
        from gui.services.history_service import HistoryService
        from gui.services.settings_service import SettingsService
        from gui.ui.main_window import MainWindow
        from gui.ui.theme import apply_theme

        from gui.utils.i18n import set_language

        settings = SettingsService()
        set_language(settings.language)                 # "auto" = idioma do Windows (inglês se não houver tradução)
        apply_theme(app, settings.theme)
        window = MainWindow(create_service(), settings, HistoryService())
        window.show()
        window.raise_()
        window.activateWindow()
        return app.exec()
    except Exception:
        _fatal(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
