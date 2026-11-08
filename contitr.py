#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ContiTR — Continental J533 (3Q0 907 530) Türkçe Kontrol Paneli.

Bu arayüz, **ContiTool** motorunu (PerkTheFox) hiç değiştirmeden kullanır:
her komut, motorun kendi `build_arg_parser()` tanımından okunur ve aynı
argümanlarla çalıştırılır. Böylece motorun **tüm fonksiyonları** Türkçe
arayüzden erişilebilir; çıktı da motorun kendi ürettiği çıktıdır.

Kaynak: https://github.com/perkthefox/mqb_contitool  (ücretsiz · satışı yasak)
Arayüz: Denizli Garaj.
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

HERE = Path(__file__).resolve().parent
FROZEN = bool(getattr(sys, "frozen", False))
MEIPASS = Path(getattr(sys, "_MEIPASS", HERE))
MOTOR = MEIPASS / "motor"
if str(MOTOR) not in sys.path:
    sys.path.insert(0, str(MOTOR))
ASSET_DIR = MEIPASS / "assets"
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else HERE
STATE_FILE = APP_DIR / "contitr_ayarlar.json"

from contitool import i18n  # noqa: E402
from contitool.cli.main import build_arg_parser  # noqa: E402

i18n.set_lang("en")

APP_TITLE = "ContiTR — J533 Türkçe Kontrol Paneli"
APP_SUB = "Continental 3Q0 907 530 · CP (KSCHUTZ) · Engineering · RSA-1024 / SWaP · ZDC parametre · CAN tezgâh"
APP_VERSION = "1.0"
CREDIT = "Motor: ContiTool — PerkTheFox · github.com/perkthefox/mqb_contitool  ·  Türkçe arayüz: Denizli Garaj"

# komut → (Türkçe ad, grup, açıklama)
COMMANDS: dict[str, tuple[str, str, str]] = {
    "inspect": ("Dump İncele", "1 · Dump",
                "CodeFlash / DataFlash / Uflash dump'larını okur: 12 CP bankası, SWaP anahtarı, FSC slotları, CRC durumları."),
    "banks": ("12 CP Bankası Tablosu", "1 · Dump",
              "Tüm MQB CP bankalarının ECU adresi, DataFlash offseti, NvM ID, 95640 maske biti, UDS ve CAN ID'leri."),
    "guide": ("Tezgâh Rehberi", "1 · Dump",
              "64 KB programlayıcı kuralı, T20 kablolama ve IKA anahtarı notları."),
    "bind-cp": ("CP Bağla (turnkey)", "2 · Bileşen Koruması",
                "CodeFlash'a hibrit KSCHUTZ trampoline kurar + DataFlash'a 16 baytlık IKA anahtarlarını yazar."),
    "patch-cflash": ("CP Yaması (CodeFlash)", "2 · Bileşen Koruması",
                     "Yalnız CodeFlash'a hibrit CP yaması uygular, App CRC-16'yı yeniden hesaplar."),
    "set-cp-key": ("CP Anahtarı Yaz", "2 · Bileşen Koruması",
                   "DataFlash'taki banka(lar)a 16 baytlık düz IKA anahtarı yazar."),
    "clear-cp-key": ("CP Bankasını Sil", "2 · Bileşen Koruması",
                     "Seçili CP bankalarını FF..FF yapar (bağı kopar)."),
    "patch-engineering": ("Engineering Mode", "3 · Engineering",
                          "Uflash'ta RSA'sız FBL yaması ve/veya CodeFlash'ta Feature 0x80/81/83 + CCP kara listesi kaldırma."),
    "activate-swap": ("SWaP FeC Aktive Et", "4 · RSA & SWaP",
                      "DataFlash'ta FeC listesini doğrudan açar/kapatır, istenirse ZDC parametresini de eşitler."),
    "parameterize": ("Parametre Düzenle (ZDC)", "5 · Parametre",
                     "ZDC #1 MKE, #2 Start-Stop, #4 FPA profilleri/tuşlar, #6 BEM alternatör ve pasaport."),
    "gen-rsa-key": ("RSA Anahtar Üret", "4 · RSA & SWaP",
                    "RSA-1024 (e=3) anahtar çifti üretir: .json + OpenSSL .pem."),
    "set-rsa-key": ("RSA Modulus Göm", "4 · RSA & SWaP",
                    "Public modulus'ü CodeFlash ve/veya DataFlash NvM 0x7C'ye yazar, CRC'leri günceller."),
    "sign-fsc": ("FSC İmzala (171 B)", "4 · RSA & SWaP",
                 "SWaP FSC v2 sertifikası imzalar (RIPEMD-160 + RSA-1024)."),
    "sign-odx": ("ODX İmzala", "4 · RSA & SWaP",
                 "CodeFlash/FD_0DATA için <FW-SIGNATURE> üretir."),
    "can": ("CAN İşlemleri", "6 · CAN",
            "Diagnosis CAN (500 kbit/s) üzerinden okuma/yazma: ports, identify, backup, read-mem, write-*, turnkey."),
    "gui": ("ContiTool Qt Arayüzü", "7 · Diğer", "Orijinal PySide6 arayüzü (bu pakette gömülü değil)."),
    "wizard": ("ContiTool Sihirbazı", "7 · Diğer", "Orijinal arayüz kısayolu (gömülü değil)."),
}

ARG_TR: dict[str, str] = {
    # ortak
    "input": "Girdi dosyası", "output": "Çıktı dosyası", "output_dir": "Çıktı klasörü", "out_file": "Dosyaya yaz",
    # dump
    "cflash": "CodeFlash.bin", "dflash": "DataFlash.bin", "uflash": "Uflash.bin",
    # cp
    "cflash_in": "CodeFlash girdi", "cflash_out": "CodeFlash çıktı",
    "dflash_in": "DataFlash girdi", "dflash_out": "DataFlash çıktı",
    "bank": "Banka (1..12 veya ECU)", "key": "IKA anahtarı (32 hex)",
    "set_pairs": "BANKA=ANAHTAR çiftleri", "banks": "Bankalar (örn. 5F 17)",
    "bypass_eeprom_mask": "95640 EEPROM maske atlaması", "force_master": "Master (19) zorla",
    "allow_suspicious_key": "Şüpheli anahtara izin ver", "ignore_input_crc": "Girdi CRC hatasını yok say",
    "global_plain": "Tüm bankalar düz anahtar", "restore_stock": "Fabrika stoğuna dön",
    "cave_vaddr": "Trampoline adresi (0x…)",
    # engineering
    "uflash_in": "Uflash girdi", "uflash_out": "Uflash çıktı",
    # swap
    "enable_fecs": "Açılacak FeC'ler", "disable_fecs": "Kapatılacak FeC'ler", "all_supported": "Desteklenen tümü",
    "all_gateway": "Gateway FeC'lerinin tümü", "replace": "Üzerine yaz", "vin": "VIN (17 karakter)",
    "no_vin": "VIN bağlama (00..00)", "timestamp": "Zaman damgası (unix)",
    "auto_parameterize": "ZDC'yi otomatik eşle", "fpa_preset": "FPA profili",
    "button_mode": "Tuş modu", "mfl_key": "MFL tuş kodu (0x…)", "kl15_memory": "Kl.15'te hatırla",
    # parameterize
    "fpa_schema": "FPA şeması", "enable_fpa_slots": "FPA slot aç", "disable_fpa_slots": "FPA slot kapat",
    "mfl_long_press": "MFL uzun basış", "console_ring": "Konsol halkası", "mfl_ring": "MFL halkası",
    "kl15_profiles": "Kl.15 profil davranışı", "kl15_powertrain": "Kl.15 güç aktarma davranışı",
    "mke_preset": "MKE ön ayarı", "mke_speed_on": "MKE giriş hızı", "mke_speed_off_high": "MKE üst hız",
    "ssa_preset": "Start-Stop ön ayarı", "ssa_bap_mode": "BAP modu (0-3)",
    "bem_preset": "BEM ön ayarı", "bem_slot": "BEM slotu",
    "dataset_pn": "Dataset numarası (F1A0)", "dataset_ver": "Dataset sürümü (F1A1)", "dataset_equip": "Donanım kodu",
    "export_block": "Blok dışa aktar (idx)", "import_block": "Blok içe aktar (idx=dosya)",
    # rsa
    "generate_key": "Anahtar üret (dosya)", "target": "Hedef (swap/fbl/both)",
    "fec": "FeC kodu (örn. 10000100)", "vcrn": "VCRN (10 hex)",
    # can
    "can_action": "CAN işlemi", "port": "Port", "interface": "Arayüz",
    "address": "Adres (0x…)", "length": "Uzunluk", "raw_image": "Ham imaj",
    "full_rewrite": "Tam yeniden yaz", "allow_icus_tail": "ICUSB kuyruğuna izin", "raw_faci": "Salt FACI",
    "overwrite_selfid": "SELFID üzerine yaz", "clear_dtc": "DTC temizle", "no_cp_patch": "CP yaması yapma",
    "no_engineering_patch": "Engineering yaması yapma", "yes": "Onayla (soru sorma)",
    "allow_dpdu_driver": "D-PDU sürücüsüne izin", "lang": "Dil", "no_color": "Renksiz çıktı",
}
PATH_HINTS = ("_in", "_out", "input", "output", "dflash", "cflash", "uflash", "file", "key", "out_file", "generate_key")


class QueueWriter:
    """Motorun stdout/stderr'ini kuyruğa aktarır."""

    def __init__(self, q: "queue.Queue[tuple[str, str]]"):
        self.q = q

    def write(self, text: str) -> int:
        if text:
            self.q.put(("out", text))
        return len(text)

    def flush(self) -> None:
        return None

    def isatty(self) -> bool:
        return False


class FormField:
    def __init__(self, spec: dict, widget: tk.Widget, var: tk.Variable, kind: str):
        self.spec = spec
        self.widget = widget
        self.var = var
        self.kind = kind  # flag | choice | text | list


class ContiTR(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=8)
        self.master = master
        self.q: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.busy = False
        self.fields: dict[str, FormField] = {}
        self.current: str | None = None
        self.cmd_specs = self._load_specs()
        self.state = self._load_state()
        self._build()
        self.after(80, self._drain)

    # ------------------------------------------------------------ altyapı
    @staticmethod
    def _load_specs() -> dict[str, dict]:
        parser = build_arg_parser()
        subs = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)][0]
        specs: dict[str, dict] = {}
        for name, sp in subs.choices.items():
            args = []
            for a in sp._actions:
                if isinstance(a, argparse._HelpAction):
                    continue
                if a.dest in ("lang", "no_color"):
                    continue
                args.append({
                    "dest": a.dest,
                    "opts": list(a.option_strings),
                    "required": bool(getattr(a, "required", False)),
                    "nargs": a.nargs,
                    "choices": list(a.choices) if a.choices else None,
                    "default": None if a.default is None else str(a.default),
                    "flag": type(a).__name__ == "_StoreTrueAction",
                    "append": type(a).__name__ == "_AppendAction",
                    "help": (a.help or ""),
                })
            specs[name] = {"args": args}
        return specs

    def _load_state(self) -> dict:
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}

    def _save_state(self) -> None:
        try:
            STATE_FILE.write_text(json.dumps(self.state, ensure_ascii=False, indent=1), encoding="utf-8")
        except OSError:
            pass

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        self.columnconfigure(0, weight=0, minsize=270)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        head = ttk.Frame(self)
        head.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        head.columnconfigure(1, weight=1)
        try:
            self._logo = tk.PhotoImage(file=str(ASSET_DIR / "logo.png"))
            ttk.Label(head, image=self._logo).grid(row=0, column=0, rowspan=2, padx=(0, 10))
        except tk.TclError:
            self._logo = None
        ttk.Label(head, text=APP_TITLE, font=("Segoe UI", 14, "bold"), foreground="#2f4f6f").grid(row=0, column=1, sticky="w")
        ttk.Label(head, text=APP_SUB, foreground="#6b6b6b").grid(row=1, column=1, sticky="w")
        ttk.Label(head, text=f"v{APP_VERSION}", foreground="#8b949e").grid(row=0, column=2, rowspan=2, sticky="e")

        left = ttk.LabelFrame(self, text=" Komutlar ", padding=4)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(left, show="tree", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.tag_configure("warn", foreground="#b26a00")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        groups: dict[str, str] = {}
        for name, (tr_name, group, desc) in COMMANDS.items():
            if group not in groups:
                groups[group] = self.tree.insert("", "end", text=f"  {group}", open=True)
            tag = "warn" if name in ("gui", "wizard", "can") else ""
            self.tree.insert(groups[group], "end", iid=name, text=f"    {tr_name}", tags=(tag,) if tag else ())

        right = ttk.Frame(self)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        self.lbl_title = ttk.Label(right, text="Soldan bir komut seç", font=("Segoe UI", 11, "bold"), foreground="#2f4f6f")
        self.lbl_title.grid(row=0, column=0, sticky="w")
        self.lbl_desc = ttk.Label(right, text="", foreground="#4b5563", wraplength=760, justify="left")
        self.lbl_desc.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        mid = ttk.Frame(right)
        mid.grid(row=2, column=0, sticky="nsew")
        mid.columnconfigure(0, weight=1)
        mid.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(mid, highlightthickness=0, height=300)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vs = ttk.Scrollbar(mid, orient="vertical", command=self.canvas.yview)
        vs.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=vs.set)
        self.form = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.form.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        act = ttk.Frame(right)
        act.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        act.columnconfigure(2, weight=1)
        self.btn_run = ttk.Button(act, text="▶ Çalıştır", command=self._run, state="disabled")
        self.btn_run.grid(row=0, column=0)
        ttk.Button(act, text="Komutu kopyala", command=self._copy_cmd).grid(row=0, column=1, padx=6)
        self.lbl_state = ttk.Label(act, text="", foreground="#1f8f3d")
        self.lbl_state.grid(row=0, column=2, sticky="w", padx=(10, 0))

        logf = ttk.LabelFrame(right, text=" Çıktı ", padding=4)
        logf.grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        right.rowconfigure(4, weight=1)
        logf.columnconfigure(0, weight=1)
        logf.rowconfigure(0, weight=1)
        self.log = tk.Text(logf, height=12, wrap="none", font=("Consolas", 9),
                           background="#0f1419", foreground="#d6dde6")
        self.log.grid(row=0, column=0, sticky="nsew")
        lsb = ttk.Scrollbar(logf, orient="vertical", command=self.log.yview)
        lsb.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=lsb.set, state="disabled")
        for tag, color in (("err", "#ff6b6b"), ("ok", "#7ee787"), ("warn", "#ffc857"), ("cmd", "#79c0ff")):
            self.log.tag_configure(tag, foreground=color)

        foot = ttk.Frame(self)
        foot.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        foot.columnconfigure(0, weight=1)
        ttk.Label(foot, text=CREDIT, foreground="#8b949e", font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")

    # ------------------------------------------------------------- form
    def _on_select(self, _e=None) -> None:
        sel = self.tree.selection()
        if not sel or sel[0] not in COMMANDS:
            return
        name = sel[0]
        self.current = name
        tr_name, group, desc = COMMANDS[name]
        self.lbl_title.configure(text=f"{tr_name}   ·   contitool {name}")
        self.lbl_desc.configure(text=desc)
        self._build_form(name)
        self.btn_run.configure(state="normal")

    def _build_form(self, name: str) -> None:
        for w in self.form.winfo_children():
            w.destroy()
        self.fields.clear()
        spec_args = self.cmd_specs.get(name, {}).get("args", [])
        saved = self.state.get(name, {})
        row = 0
        for spec in spec_args:
            dest = spec["dest"]
            label = ARG_TR.get(dest, spec["help"] or dest)
            if spec["required"]:
                label += " *"
            ttk.Label(self.form, text=label, wraplength=330, justify="left").grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            holder = ttk.Frame(self.form)
            holder.grid(row=row, column=1, sticky="ew", pady=3)
            self.form.columnconfigure(1, weight=1)
            default = saved.get(dest, spec["default"] or "")

            if spec["flag"]:
                var = tk.BooleanVar(value=bool(saved.get(dest, False)))
                cb = ttk.Checkbutton(holder, variable=var, text="evet")
                cb.pack(side="left")
                self.fields[dest] = FormField(spec, cb, var, "flag")
            elif spec["choices"]:
                var = tk.StringVar(value=str(default) if default else str(spec["choices"][0]))
                cb = ttk.Combobox(holder, textvariable=var, values=[str(c) for c in spec["choices"]],
                                  state="readonly", width=24)
                cb.pack(side="left")
                self.fields[dest] = FormField(spec, cb, var, "choice")
            else:
                var = tk.StringVar(value=str(default))
                ent = ttk.Entry(holder, textvariable=var, width=52)
                ent.pack(side="left", fill="x", expand=True)
                is_path = any(h in dest for h in PATH_HINTS) or "dosya" in label.lower()
                if is_path:
                    def browse(v=var, d=dest):
                        if "dir" in d or "out_dir" in d:
                            p = filedialog.askdirectory()
                        else:
                            p = filedialog.askopenfilename()
                        if p:
                            v.set(p)

                    ttk.Button(holder, text="…", width=3, command=browse).pack(side="left", padx=(4, 0))
                kind = "list" if (spec["append"] or spec["nargs"] in ("+", "*")) else "text"
                self.fields[dest] = FormField(spec, ent, var, kind)
            row += 1
        ttk.Label(self.form, text="* zorunlu alan · boş bırakılanlar motora hiç gönderilmez",
                  foreground="#8b949e", font=("Segoe UI", 8)).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 0))

    # -------------------------------------------------------------- argv
    def _argv(self) -> list[str]:
        if not self.current:
            return []
        argv = [self.current, "--no-color"]
        for dest, f in self.fields.items():
            spec = f.spec
            opt = spec["opts"][0] if spec["opts"] else dest
            if f.kind == "flag":
                if bool(f.var.get()):
                    argv.append(opt)
                continue
            raw = str(f.var.get()).strip()
            if not raw:
                continue
            if f.kind == "list":
                parts = [p.strip() for p in raw.replace(",", "\n").splitlines() if p.strip()]
                for p in parts:
                    argv.extend([opt, p])
            else:
                argv.extend([opt, raw])
        return argv

    def _copy_cmd(self) -> None:
        argv = self._argv()
        if not argv:
            return
        text = "python conti_cp_tool.py " + " ".join(f'"{a}"' if " " in a else a for a in argv)
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        self.lbl_state.configure(text="komut panoya kopyalandı")
        self._write(text + "\n", "cmd")

    # --------------------------------------------------------- çalıştır
    def _log_write(self, text: str, tag: str | None = None) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text, (tag,) if tag else ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _write(self, text: str, tag: str | None = None) -> None:
        self._log_write(text, tag)

    def _run(self) -> None:
        if self.busy or not self.current:
            return
        argv = self._argv()
        if not argv:
            return
        self.state[self.current] = {d: (bool(f.var.get()) if f.kind == "flag" else str(f.var.get()))
                                    for d, f in self.fields.items()}
        self._save_state()
        self.busy = True
        self.btn_run.configure(state="disabled")
        self.lbl_state.configure(text="çalışıyor…")
        self._write("\n$ contitool " + " ".join(argv) + "\n", "cmd")

        def worker() -> None:
            from contitool.cli.main import main as engine_main
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = QueueWriter(self.q)  # type: ignore[assignment]
            rc = 1
            try:
                rc = engine_main(argv)
            except SystemExit as exc:
                rc = int(exc.code or 0)
            except Exception:  # noqa: BLE001
                self.q.put(("err", traceback.format_exc()))
            finally:
                sys.stdout, sys.stderr = old_out, old_err
                self.q.put(("rc", str(rc)))

        threading.Thread(target=worker, daemon=True).start()

    def _drain(self) -> None:
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "out":
                    self._log_write(payload)
                elif kind == "err":
                    self._log_write(payload, "err")
                elif kind == "rc":
                    rc = int(payload)
                    self.busy = False
                    self.btn_run.configure(state="normal")
                    if rc == 0:
                        self.lbl_state.configure(text="✔ tamamlandı (rc=0)")
                        self._log_write("\n✔ işlem tamamlandı (rc=0)\n", "ok")
                    else:
                        self.lbl_state.configure(text=f"✘ hata (rc={rc})")
                        self._log_write(f"\n✘ motor rc={rc} döndürdü — yukarıdaki mesaja bak\n", "err")
        except queue.Empty:
            pass
        self.after(80, self._drain)



def selftest(out_dir: Path) -> int:
    """Frozen doğrulama: gömülü motorun komutları gerçekten çalışıyor mu?"""
    import contextlib, io
    out_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    rc_total = 0
    from contitool.core import zdc
    from contitool.cli.main import main as engine_main

    raw = bytes([0xFF]) * 65536
    raw = zdc.apply_zdc_passport(raw, dataset_pn="V03935374FG", dataset_ver="0001", equip="0AB")
    raw = zdc.inject_mke_preset(raw, "86")
    raw = zdc.inject_ssa_preset(raw)
    dflash = out_dir / "selftest_Dflash.bin"
    dflash.write_bytes(raw)

    cases = [
        ("banks", ["banks", "--no-color"]),
        ("guide", ["guide", "--no-color"]),
        ("inspect", ["inspect", "--no-color", "--dflash", str(dflash)]),
        ("parameterize", ["parameterize", "--no-color", "--input", str(dflash),
                          "--output", str(out_dir / "df_out.bin"), "--mke-preset", "84"]),
        ("gen-rsa-key", ["gen-rsa-key", "--no-color", "--output", str(out_dir / "k.json")]),
    ]
    for name, argv in cases:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                try:
                    rc = engine_main(argv)
                except SystemExit as exc:
                    rc = int(exc.code or 0)
        except Exception as exc:  # noqa: BLE001
            rc = 99
            lines.append(f"{name}: EXC {exc}")
        lines.append(f"{name}={rc}")
        if rc != 0:
            rc_total = 1
    lines.append(f"komut_sayisi={len(COMMANDS)}")
    lines.append(f"rc={rc_total}")
    (out_dir / "selftest.txt").write_text("\n".join(lines), encoding="utf-8")
    if sys.stdout is not None:
        print("\n".join(lines))
    return rc_total


def main() -> int:
    if "--selftest" in sys.argv:
        i = sys.argv.index("--selftest")
        target = Path(sys.argv[i + 1]) if i + 1 < len(sys.argv) else Path.cwd()
        return selftest(target)

    root = tk.Tk()
    root.title(f"{APP_TITLE}  v{APP_VERSION}")
    try:
        root.iconbitmap(str(ASSET_DIR / "logo.ico"))
    except tk.TclError:
        pass
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    ContiTR(root).pack(fill="both", expand=True)
    root.geometry("1280x880")
    root.minsize(1080, 720)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
