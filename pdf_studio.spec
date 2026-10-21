# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: gera a pasta  dist/PDF Reconstruction Studio/  com o "PDF Reconstruction Studio.exe"
import importlib.util
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

APP_NAME = "PDF Reconstruction Studio"
datas = [("gui/ui/resources", "gui/ui/resources"), ("gui/i18n", "gui/i18n")] + collect_data_files("docx")      # modelo .docx base do python-docx
hiddenimports = collect_submodules("skimage.metrics") + collect_submodules("app")
if importlib.util.find_spec("docx2pdf"):                    # opcional: validação usando o Microsoft Word
    hiddenimports += ["docx2pdf"]

a = Analysis(
    ["run_gui.py"],
    pathex=["."],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "matplotlib", "IPython", "pytest", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia", "PySide6.QtCharts"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,                                          # sem janela preta
    icon="gui/ui/resources/app.ico" if sys.platform == "win32" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name=APP_NAME)
