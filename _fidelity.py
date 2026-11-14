# -*- coding: utf-8 -*-
"""MOTOR SADAKAT KANITI: bizim motor == orijinal v2.1.1, yalnız 3 dosyada yerelleştirme.

Çıktı: dosya bazında durum + değişen satırlar. Fark, izin verilen desenlerin
dışındaysa rc=1 (o zaman derleme yapılmaz).
"""
import difflib, pathlib, re, sys

UP = pathlib.Path(r"C:\Users\DenizliGaraj-Asus\AppData\Local\Temp\conti_v211\mqb_contitool-2.1.1\src\contitool")
OUR = pathlib.Path(r"C:\Users\DenizliGaraj-Asus\AppData\Local\Temp\conti_v211\stage_211\src\contitool")

ALLOWED = {
    "i18n.py": [
        r'^\+    if val in \("tr", "tur", "turkish"',
        r'^\+        return "tr"$',
        r'^\+    if _LANG == "tr":$',
        r'^\+        from contitool\.i18n_tr import TR_CATALOG$',
        r'^\+$',
        r'^\+        return TR_CATALOG\.get\(en, en\)$',
        r'^-    if norm not in \("ru", "en"\):$',
        r'^\+    if norm not in \("ru", "en", "tr"\):$',
        r'^[-+]?\s*raise ValueError.*$',
        r'^[-+]?"""(Set active language|Return the string in).*$',
        r'^[-+]?.*`tr`.*$',
    ],
    "cli/main.py": [
        r'^[-+].*choices=\("ru", "en"(, "tr")?\).*$',
        r'^[-+].*Язык: ru / en.*$',
    ],
    "gui/main_window.py": [
        r'^[-+].*\(\(\s*"(?:ru|tr)", "left"\), \("en", "right"\)\).*$',
    ],
}

extra = {"i18n_tr.py"}  # yeni dosya (Türkçe katalog)

up_files = {p.relative_to(UP).as_posix(): p for p in UP.rglob("*") if p.is_file()}
our_files = {p.relative_to(OUR).as_posix(): p for p in OUR.rglob("*") if p.is_file()}

only_ours = sorted(set(our_files) - set(up_files))
only_up = sorted(set(up_files) - set(our_files))
print(f"dosya: orijinal {len(up_files)} · bizim {len(our_files)}")
print("sadece bizde:", only_ours or "—")
print("sadece orijinalde:", only_up or "—")
if set(only_ours) - extra:
    print("HATA: beklenmeyen fazladan dosya")
if only_up:
    print("HATA: eksik dosya var")

changed, violations = [], []
for rel in sorted(set(up_files) & set(our_files)):
    a = up_files[rel].read_bytes()
    b = our_files[rel].read_bytes()
    if a == b:
        continue
    changed.append(rel)
    if rel not in ALLOWED:
        violations.append((rel, "izin listesinde olmayan dosya değişmiş"))
        continue
    alines = up_files[rel].read_text(encoding="utf-8").splitlines()
    blines = our_files[rel].read_text(encoding="utf-8").splitlines()
    for line in difflib.unified_diff(alines, blines, lineterm="", n=0):
        if line.startswith(("---", "+++", "@@")):
            continue
        if not any(re.match(p, line) for p in ALLOWED[rel]):
            violations.append((rel, line[:120]))

print(f"\ndeğişen dosya: {len(changed)} → {changed}")
if violations:
    print("\nİZİN VERİLMEYEN FARKLAR:")
    for rel, v in violations[:20]:
        print(f"  {rel}: {v}")
    sys.exit(1)

# yasak: ağ erişimi / telemetri eklenmiş mi?
net_hits = []
for p in OUR.rglob("*.py"):
    txt = p.read_text(encoding="utf-8", errors="replace")
    for pat in ("requests.", "urllib.request.urlopen", "socket.socket(", "http://", "https://api."):
        if pat in txt and p.name != "update_check.py":  # update_check orijinalde de var
            net_hits.append((p.relative_to(OUR).as_posix(), pat))
print("\nağ erişimi izi (güncelleme denetimi hariç):", net_hits or "yok")

print("\nSONUÇ: motor orijinalle aynı; farklar yalnızca yerelleştirme katmanı.")
print("İzin verilen 3 dosya:", ", ".join(sorted(ALLOWED)))
