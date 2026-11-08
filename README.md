# ContiTR — Continental J533 Türkçe (ContiTool)

Continental VAG MQB **J533 Gateway** (`3Q0 907 530`, Renesas RH850/F1L) için
**ContiTool'un aynısı**, arayüzü **Türkçe**.

> Bu program ContiTool'un ta kendisidir: aynı ekranlar, aynı akış, aynı motor kodu.
> Arayüzdeki **871 metnin tamamı Türkçeye** çevrildi (katalog: `motor/contitool/i18n_tr.py`).
> Dil düğmesi **TR / EN**; Rusça da motor içinde duruyor (`--lang ru`).

**Kaynak:** ContiTool — **PerkTheFox**
`https://github.com/perkthefox/mqb_contitool` · `vwhacking.antonperk.com` ·
Drive2 · Telegram · sürüm **2.0.1a**
Ücretsiz topluluk/araştırma aracı — **ticari satışı yasaktır**, atıf korunmalıdır.
Türkçe yerelleştirme + paketleme: **Denizli Garaj**.

## Ne yapar (orijinalin tüm işlevleri)

| Bölüm | İçerik |
|---|---|
| **ECU açma** | Tezgâhtaki gateway'i CAN üzerinden okur ve açar; CodeFlash 1,5 MB + Uflash 32 KB + DataFlash 64 KB tam yedek |
| **CP (KSCHUTZ)** | Hibrit trampoline ile bileşen koruması bağlama; 12 köle bankası + master #0; 95640 maske atlama; IKA anahtarları |
| **Engineering** | RSA'sız FBL (`Uflash +0x342A`), Feature `0x80/81/83`, CCP kara listesi, fabrika RAM-Loader `0x6F0` |
| **RSA / SWaP** | RSA-1024 (`e=3`) anahtar üretme/gömme, **FSC 171 B** sertifikası, ODX `<FW-SIGNATURE>`, FeC aktive etme |
| **Parametreleme** | ZDC: FPA sürüş profilleri + MODE/direksiyon düğmeleri, Kl.15 hafızası, MKE, Start-Stop, BEM alternatör, dataset pasaportu ve bölüm aktarımı |
| **CAN terminali** | Canlı trafik, UDS istek/yanıt (ISO-TP), `3E 00` canlılık, filtreli izleme |
| **Sağlık** | DTC okuma/silme, yazma sonrası doğrulama, hatırlatıcı raporlar |
| **Adaptörler** | SLCAN/CANable, PCAN, Vector, Kvaser, J2534 PassThru, VAS 6154 / VNCI 6154A (D-PDU) |

## Çalıştırma

```bash
pip install PySide6-Essentials python-can pyserial
python contitr.py            # Türkçe (varsayılan)
python contitr.py --lang en  # İngilizce arayüz
```

Hazır exe: **release v2.0** (`ContiTR-J533.exe`, imzalı, tek dosya, ~40 MB).

## ⚠ Güvenlik (orijinalin uyarıları aynen geçerlidir)

- **Araçta çalıştırmayın.** Gateway sökülü, **tezgâhta**, regüle 12,5–13,8 V besleme.
- **CAN sonlandırma zorunlu:** adaptörde sonlandırıcı veya Pin 19 (CAN-H) – Pin 9 (CAN-L)
  arasında **120 Ω** direnç. Sonlandırma yoksa veriyolu Bus-Off'a düşer.
- **Yazmadan önce tam yedek:** `Cflash.bin` (1,5 MB), `Uflash.bin` (32 KB),
  `Dflash.bin` (64 KB), harici `95640` (8 KB).
- Harici programlayıcıda **64 KB DataFlash** profili (`R7F7010543/563`); 32 KB profil
  CP anahtarlarının bulunduğu `0xC000..0xFFFF` bölgesini keser.
- Ucuz Çin adaptörleri güvenli sayılmaz. Brick riski tamamen kullanıcıya aittir.

## Teknik notlar

- Motor `motor/contitool/` altında **orijinal koduyla** durur. Yerelleştirme için
  yalnızca üç yere dokunuldu: `i18n.py` (`tr()` kataloğu + `tr` dil kodu),
  `cli/main.py` (`--lang` seçenekleri), `gui/main_window.py` (dil düğmesi TR/EN).
  Motor mantığı, adresler, protokoller **değiştirilmedi**.
- Çeviri kataloğu `i18n_tr.py`: **871/871 metin (%100)**. Katalogda olmayan yeni bir
  metin eklenirse İngilizce görünür (motor bozulmaz).
- `--selftest <klasör>`: motor sürümü, katalog boyutu, çeviri örneği, dil geçişleri ve
  Qt arayüzünün kurulabildiğini doğrular (frozen exe'de de çalışır).
- `panel_konsol.py`: v1.0'daki komut paneli (yedek olarak duruyor, exe'ye dahil değil).

## Lisans

Motor: **ContiTool / PerkTheFox** (ücretsiz, satış yasak). Arayüz yerelleştirmesi: Denizli Garaj.
Ayrıntı: `LICENSE.md`.
