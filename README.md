# ContiTR — J533 Türkçe Kontrol Paneli

Continental VAG MQB **J533 Gateway** (`3Q0 907 530`) için **Türkçe** masaüstü arayüz.
Motor **hiç değiştirilmeden** gömülüdür: **ContiTool — PerkTheFox**.

> **Kaynak:** https://github.com/perkthefox/mqb_contitool · `vwhacking.antonperk.com` · Drive2 · Telegram
> Ücretsiz topluluk aracı — **ticari satışı yasaktır**, atıf korunmalıdır.

## Nasıl çalışır

Arayüz, motorun kendi `build_arg_parser()` tanımını okur; **17 komutun tamamı** ve **tüm argümanları**
otomatik olarak Türkçe formlara dönüşür. Çalıştırınca motorun kendi `main()` fonksiyonu çağrılır →
çıktı, doğrulama ve davranış orijinalle **birebir aynıdır**.

| Grup | Komutlar |
|---|---|
| **1 · Dump** | Dump İncele · 12 CP Bankası Tablosu · Tezgâh Rehberi |
| **2 · Bileşen Koruması** | CP Bağla (turnkey) · CP Yaması (CodeFlash) · CP Anahtarı Yaz · CP Bankasını Sil |
| **3 · Engineering** | Engineering Mode (RSA'sız Uflash + Feature 0x80/81/83 + CCP) |
| **4 · RSA & SWaP** | RSA Anahtar Üret · RSA Modulus Göm · FSC İmzala (171 B) · ODX İmzala · SWaP FeC Aktive Et |
| **5 · Parametre** | Parametre Düzenle (ZDC): MKE · Start-Stop · FPA profilleri/tuşlar · BEM · pasaport |
| **6 · CAN** | ports · identify · backup · read-mem · write-dflash · write-cflash · write-uflash · turnkey |

## Gereksinimler

- **Çevrimdışı komutlar:** Python 3.12+ ve Tkinter (harici paket yok).
- **CAN komutları:** `python-can` + `pyserial` **ve** uygun adaptör (CANable/SLCAN, PCAN, Vector, Kvaser,
  J2534 PassThru, VAS 6154 / VNCI 6154A). Adaptör yoksa CAN grubu çalışmaz, diğerleri etkilenmez.

```bash
pip install python-can pyserial
python contitr.py
```

## ⚠ Güvenlik

- **Araçta çalıştırma** — gateway sökülü, tezgâhta, regüle 12,5–13,8 V besleme; T20 pin 1/14/11/19/9,
  500 kbit/s, **120 Ω sonlandırma**.
- Yazmadan önce **tam yedek**: `Cflash.bin` (1,5 MB), `Uflash.bin` (32 KB), `Dflash.bin` (64 KB), `95640` (8 KB).
- Programlayıcıda **64 KB DataFlash** profili (`R7F7010543/563`); 32 KB profil anahtarları keser.
- Ucuz Çin adaptörleri güvenli sayılmaz.

## Lisans

Motor: **ContiTool / PerkTheFox** (ücretsiz, satış yasak). Arayüz: Denizli Garaj. Ayrıntı: `LICENSE.md`.
