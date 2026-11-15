# -*- coding: utf-8 -*-
"""ContiTR motorunu upstream sürümüne yükselt (yedekli, idempotent).

Kullanım: yeni upstream ağacını STAGE sabitine göre hazırla, sonra bu betiği çalıştır.
STAGE = <indirilen kaynak>/src/contitool (yerelleştirme yamaları uygulanmış olmalı).
Kontroller geçmezse betik durur ve motora dokunmaz.
"""
import shutil, pathlib, sys, filecmp

PROJ = pathlib.Path(r"C:\Users\DenizliGaraj-Asus\Documents\HermesVault\araclar\j533-contitr")
STAGE = pathlib.Path(r"C:\Users\DenizliGaraj-Asus\AppData\Local\Temp\conti_v211\stage_211\src\contitool")
MOTOR = PROJ / "motor" / "contitool"
BACKUP = PROJ / "motor_v201"

if not STAGE.is_dir():
    sys.exit("HATA: stage yok")

if not BACKUP.exists() and MOTOR.exists():
    shutil.copytree(MOTOR, BACKUP)
    print("yedek alındı: motor_v201")
else:
    print("yedek zaten var (motor_v201) — korunuyor")

shutil.rmtree(MOTOR)
shutil.copytree(STAGE, MOTOR)
for p in MOTOR.rglob("__pycache__"):
    shutil.rmtree(p, ignore_errors=True)

n_py = len(list(MOTOR.rglob("*.py")))
print(f"motor güncellendi: {n_py} dosya")
print("i18n_tr var:", (MOTOR / "i18n_tr.py").is_file())

# yerelleştirme yamaları gerçekten yerinde mi?
i18n = (MOTOR / "i18n.py").read_text(encoding="utf-8")
cli = (MOTOR / "cli" / "main.py").read_text(encoding="utf-8")
gui = (MOTOR / "gui" / "main_window.py").read_text(encoding="utf-8")
checks = {
    "i18n tr normalizasyonu": '"tr", "tur", "turkish"' in i18n,
    "i18n tr() katalog": "TR_CATALOG.get(en, en)" in i18n,
    "i18n set_lang tr": 'if norm not in ("ru", "en", "tr")' in i18n,
    "cli --lang tr": 'choices=("ru", "en", "tr")' in cli,
    "theme mid stili": 'SegBtn[pos="mid"]' in (MOTOR / "gui" / "theme.py").read_text(encoding="utf-8"),
    "gui dil düğmeleri (RU|TR|EN)": '("tr", "mid")' in gui and '("ru", "left")' in gui,
}
for k, v in checks.items():
    print(("  OK   " if v else "  HATA ") + k)
if not all(checks.values()):
    sys.exit("HATA: yamalar eksik")

# sürüm etiketi
p = PROJ / "contitr.py"
s = p.read_text(encoding="utf-8")
s = s.replace('APP_VERSION = "2.0"', 'APP_VERSION = "2.1.1"')
p.write_text(s, encoding="utf-8")
print("contitr.py APP_VERSION = 2.1.1")
