#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ContiTR — Continental J533 (3Q0 907 530) · ContiTool'un Türkçe sürümü.

Bu program **ContiTool'un ta kendisidir**: aynı arayüz, aynı ekranlar, aynı
komutlar, aynı motor. Tek fark: arayüz metinleri Türkçedir (871 metnin
tamamı çevrildi) ve dil düğmesi TR/EN'dir.

Motor: ContiTool — PerkTheFox · github.com/perkthefox/mqb_contitool
       (ücretsiz topluluk aracı · ticari satışı yasak)
Türkçe yerelleştirme: Denizli Garaj.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = bool(getattr(sys, "frozen", False))
MEIPASS = Path(getattr(sys, "_MEIPASS", HERE))
MOTOR = MEIPASS / "motor"
if str(MOTOR) not in sys.path:
    sys.path.insert(0, str(MOTOR))
ASSETS = MEIPASS / "assets"

APP_VERSION = "2.0"


def _early_lang(argv: list[str]) -> str:
    """--lang / CONTI_CP_LANG / varsayılan tr."""
    for i, tok in enumerate(argv):
        if tok in ("-l", "--lang") and i + 1 < len(argv):
            return argv[i + 1]
        if tok.startswith("--lang="):
            return tok.split("=", 1)[1]
    return os.environ.get("CONTI_CP_LANG", "tr")


def selftest(out_dir: Path) -> int:
    """Frozen doğrulama: motor, çeviri kataloğu ve Qt arayüzü sağlam mı?"""
    out_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    rc = 0

    from contitool import __version__ as engine_version
    from contitool.i18n import get_lang, set_lang, tr
    from contitool.i18n_tr import TR_CATALOG

    lines.append(f"motor_surum={engine_version}")
    lines.append(f"katalog_metin={len(TR_CATALOG)}")

    set_lang("tr")
    lines.append(f"dil={get_lang()}")
    probe_ru = "Проверка"
    probe_en = "Driver Alert System (MKE)"
    got = tr(probe_ru, probe_en)
    lines.append(f"ceviri_ornek={got}")
    if got != "Sürücü Uyarı Sistemi (MKE)":
        lines.append("HATA: ceviri_ornek beklenen değil")
        rc = 1

    set_lang("en")
    if tr(probe_ru, probe_en) != probe_en:
        lines.append("HATA: EN modu bozuk")
        rc = 1
    set_lang("ru")
    if tr(probe_ru, probe_en) != probe_ru:
        lines.append("HATA: RU modu bozuk")
        rc = 1
    set_lang("tr")
    lines.append("dil_gecisleri=OK")

    # Qt: arayüz kurulabiliyor mu (offscreen)
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from contitool.gui.app import create_window

        app, win = create_window()
        lines.append(f"pencere_basligi={win.windowTitle()[:60]}")
        lines.append(f"menu_sayisi={len(win.menuBar().actions())}")
        lines.append(f"lang_dugmesi={','.join(sorted(win._lang_buttons))}")
        win.close()
        app.processEvents()
        lines.append("qt_arayuz=OK")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"HATA qt: {type(exc).__name__}: {exc}")
        rc = 1

    if len(TR_CATALOG) < 800:
        lines.append("HATA: katalog eksik")
        rc = 1
    lines.append(f"rc={rc}")
    text = "\n".join(lines)
    (out_dir / "selftest.txt").write_text(text, encoding="utf-8")
    print(text)
    return rc


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        i = argv.index("--selftest")
        target = Path(argv[i + 1]) if i + 1 < len(argv) else Path.cwd()
        return selftest(target)

    from contitool.i18n import set_lang

    try:
        set_lang(_early_lang(sys.argv))
    except ValueError:
        set_lang("tr")

    from contitool.gui.app import run_gui

    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
