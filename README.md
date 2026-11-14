# ContiTR — Continental J533 Türkçe (ContiTool v2.1.1)

Continental VAG MQB **J533 Gateway** (`3Q0 907 530`, Renesas RH850/F1L) için
**ContiTool'un aynısı**, arayüzü **Türkçe**.

> Motor: **ContiTool 2.1.1 — PerkTheFox** (`github.com/perkthefox/mqb_contitool`)
> Ücretsiz topluluk aracı — **ticari satışı yasaktır**, atıf korunmalıdır.
> Türkçe yerelleştirme + paketleme: **Denizli Garaj**.

## Sadakat garantisi

Motor, orijinal v2.1.1 ile **bayt bayt aynıdır**. Yerelleştirme için yalnız **3 dosyaya**
dokunuldu ve her fark otomatik denetlenir (`_fidelity.py`):

```
değişen dosya: 3 → cli/main.py · gui/main_window.py · i18n.py
eklenen dosya: 1 → i18n_tr.py (Türkçe metin kataloğu)
sonuç: rc=0 — izin verilmeyen tek bir satır farkı yok
```

Yani **protokol, adres, yazma akışı, CRC/RSA mantığı orijinalin aynısı**; yalnızca
görünen metinler Türkçe. Bu yüzden "yanlış analiz → parçayı bozma" riski yerelleştirme
katmanından gelmez.

Türkçe kapsam: **1.107 / 1.107 metin (%100)**.

## v2.1.1'in getirdikleri (Türkçe arayüzde)

| Özellik | Ne yapar |
|---|---|
| **RH850 IDCODE + CHIP ID** | `SELFID` (128 bit) CodeFlash `0xAB00` ve Extra Area `0xFF300050`'den okunup **çapraz doğrulanır**; `CHIP ID` (32 B, SCDS0 `0xFFCD00E0`) wafer/lot etiketiyle gösterilir. Dump'ın gerçekten bu çipten alındığının donanım kanıtı |
| **EEPROM & OPBT** | Harici **ST M95640** (8 KB, CSIH1 SPI) salt okuma + **OPBT0..OPBT8** (36 B) çözümlemesi; NvM 0x00 pasaport, VIN, kodlama `0x0600`, kurulum listesi `0x04A3`, BEM akü, NvM 0x5E güvenlik bloğu, CRC-16/CCITT-FALSE doğrulaması, OPBT0/OPBT8 bit alanları. Tam yedeğe `Eeprom.bin` + `Opbt.bin` otomatik eklenir |
| **Yazılım parça numarası (F187)** | `FD_0DATA` varyant tablosundan `3Q0907530AC/AG/AL/AR…` gibi tam yazılım numarası ECU başlığında |
| **FPA editörü** | `On`/`Off` hedef modları + **15 kademeli DCC** sertlik sürgüsü, `CharismaFunctions` katalog düzeltmeleri |
| **FRF / ODX yazma** | ODİS dosyasıyla doğrudan yazma, ECU kimliğine göre doğrulama |
| **Yeni arayüz** | Karbon-çinko tema, HiDPI, iki satırlı ECU kimlik başlığı, bellek dump defteri, `Ctrl+J` işlem günlüğü |
| **Düzeltmeler** | SLCAN/CANable 64 KB akış kaybı (toplu okuma + 256 KB SetupComm), D-PDU 27.2 yeniden bağlanma/ISO-TP yedeği, 5Q0/Lear reddi, ZDC yüklemede yalnız değişen bloklar |

## Çalıştırma

```bash
pip install PySide6-Essentials python-can pyserial
python contitr.py            # Türkçe (varsayılan)
python contitr.py --lang en  # İngilizce
python contitr.py --lang ru  # Rusça (motor içinde)
```

Hazır exe: **release v2.1.1** (`ContiTR-J533.exe`, imzalı, tek dosya, ~41 MB).

## ⚠ Güvenlik (orijinalin uyarıları aynen geçerlidir)

- **Araçta değil, tezgâhta** çalıştırın; gateway sökülü, regüle 12,5–13,8 V besleme.
- **CAN sonlandırma zorunlu:** adaptörde sonlandırıcı veya Pin 19 (CAN-H) – Pin 9 (CAN-L) arası **120 Ω**.
- **Yazmadan önce tam yedek:** CodeFlash 1,5 MB + Uflash 32 KB + DataFlash 64 KB (+ EEPROM/OPBT v2.1.1'de otomatik).
- Harici programlayıcıda **64 KB DataFlash** profili (`R7F7010543/563`).
- OPBT ve harici EEPROM'a **yazma bilinçli olarak yok** (salt okuma) — geçersiz OPBT boot/debug erişimini kilitleyebilir.
- Ucuz Çin adaptörleri güvenli sayılmaz. Brick riski kullanıcıya aittir.

## Depo düzeni

```
contitr.py            launcher (--lang, --selftest)
motor/contitool/      ContiTool v2.1.1 (yalnız 3 dosyada yerelleştirme)
motor_v201/           önceki motor (v2.0.1a) — yedek, çalıştırılmaz
panel_konsol.py       v1.0 komut paneli (arşiv)
dist_v211/            imzalı exe (v2.1.1)
_fidelity.py          orijinalle fark denetimi (rc=0 = yalnız yerelleştirme)
```

## Lisans

Motor: **ContiTool / PerkTheFox** (ücretsiz, satış yasak). Yerelleştirme: Denizli Garaj. Ayrıntı: `LICENSE.md`.
