import os
from threading import Thread
from flask import Flask

# 1. Mini Flask web sunucusu
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif ve çalışıyor kanka!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Web sunucusunu burada tetikliyoruz
keep_alive()

# --- BURADAN SONRASI DİSCORD KODLARIN ---
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} olarak giriş yapıldı, mermi gibiyiz!')
    try:
        # Sunucu ID'ni buraya yazarak anında senkronize edebilirsin:
        guild = discord.Object(id=1538222949918707712)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"{len(synced)} adet komut sunucuya senkronize edildi.")
    except Exception as e:
        print(e)

# ==========================================
# 1. ARAÇ KAYIT SİSTEMİ (/arac_kayit_et)
# ==========================================
@bot.tree.command(name="arac_kayit_et", description="Yeni araç kayıt ve alım talebi oluşturur.")
@app_commands.describe(
    marka="Araç Markası",
    model="Araç Modeli",
    yil="Üretim Yılı",
    foto="Araç Görseli",
    plaka="İstediğiniz Plaka"
)
async def arac_kayit_et(
    interaction: discord.Interaction, 
    marka: str, 
    model: str, 
    yil: str, 
    foto: discord.Attachment, 
    plaka: str
):
    await interaction.response.defer(ephemeral=True)
    ARAC_KANAL_ID = 1543684123002937514 
    target_channel = interaction.guild.get_channel(ARAC_KANAL_ID)
    
    embed = discord.Embed(title="🚗 Yeni Araç Kayıt ve Alım Talebi", color=discord.Color.blue())
    embed.add_field(name="Başvuran", value=interaction.user.mention, inline=False)
    embed.add_field(name="Marka", value=marka, inline=True)
    embed.add_field(name="Model", value=model, inline=True)
    embed.add_field(name="Yıl", value=yil, inline=True)
    embed.add_field(name="İstenen Plaka", value=plaka, inline=False)
    
    if foto and foto.content_type and foto.content_type.startswith("image/"):
        embed.set_image(url=foto.url)
        
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    
    if target_channel:
        await target_channel.send(embed=embed)
        await interaction.followup.send("Araç kayıt talebin yetkililere iletildi!", ephemeral=True)
    else:
        await interaction.followup.send("Araç onay kanalı bulunamadı!", ephemeral=True)


# ==========================================
# 2. KARAKTER ONAY VIEW (Butonlar ve Isim Değiştirme)
# ==========================================
class KarakterOnayView(View):
    def __init__(self, target_user_id: int, ic_isim: str):
        super().__init__(timeout=None)
        self.target_user_id = target_user_id
        self.ic_isim = ic_isim

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.success, custom_id="karakter_onay_btn")
    async def onay_button(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=f"✅ Onaylayan Yetkili: {interaction.user.name}")
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

        try:
            hedef_uye = interaction.guild.get_member(self.target_user_id)
            if hedef_uye:
                await hedef_uye.edit(nick=self.ic_isim)
                print(f"Başarılı: {hedef_uye.name} isimli kullanıcının adı {self.ic_isim} olarak değiştirildi.")
            else:
                print("Hata: Hedef üye sunucuda bulunamadı!")
        except Exception as e:
            print(f"❌ Takma ad değiştirilemedi (Hata Detayı): {e}")

        try:
            user = await interaction.client.fetch_user(self.target_user_id)
            dm_embed = discord.Embed(title="🎉 Karakter Başvurunuz Onaylandı!", description=f"**{self.ic_isim}** adlı karakteriniz kabul edildi ve isminiz güncellendi.", color=discord.Color.green())
            await user.send(embed=dm_embed)
            await interaction.followup.send("Başvuru onaylandı, isim değiştirildi ve DM gönderildi!", ephemeral=True)
        except Exception:
            await interaction.followup.send("Onaylandı ve isim değiştirildi ancak kullanıcının DM'si kapalı.", ephemeral=True)

    @discord.ui.button(label="Reddet", style=discord.ButtonStyle.danger, custom_id="karakter_red_btn")
    async def reddet_button(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.set_footer(text=f"❌ Reddeden Yetkili: {interaction.user.name}")
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

        try:
            user = await interaction.client.fetch_user(self.target_user_id)
            dm_embed = discord.Embed(title="❌ Karakter Başvurunuz Reddedildi", description="Üzgünüz, karakter başvurunuz onaylanmadı.", color=discord.Color.red())
            await user.send(embed=dm_embed)
            await interaction.followup.send("Başvuru reddedildi ve kullanıcıya DM gönderildi!", ephemeral=True)
        except Exception:
            await interaction.followup.send("Reddedildi ancak kullanıcının DM'si kapalı.", ephemeral=True)


# ==========================================
# 3. KARAKTER OLUŞTURMA SİSTEMİ
# ==========================================
@bot.tree.command(name="karakter_olustur", description="Karakter oluşturma başvurusu yaparsınız.")
@app_commands.describe(ic_isim="IC İsim", karakter="Hikaye", dogum_tarihi="Tarih", dogum_yeri="Yer", meslek="Meslek", vesikalik="Fotoğraf")
async def karakter_olustur(interaction: discord.Interaction, ic_isim: str, karakter: str, dogum_tarihi: str, dogum_yeri: str, meslek: str, vesikalik: discord.Attachment):
    await interaction.response.defer(ephemeral=True)

    KARAKTER_ONAY_KANAL_ID = 1543971287804944526 
    target_channel = interaction.guild.get_channel(KARAKTER_ONAY_KANAL_ID)
    
    embed = discord.Embed(title="👤 Yeni Karakter Başvurusu", color=discord.Color.purple())
    embed.add_field(name="IC İsim", value=ic_isim, inline=False)
    embed.add_field(name="Karakter Bilgisi", value=karakter, inline=False)
    embed.add_field(name="Doğum Tarihi", value=dogum_tarihi, inline=True)
    embed.add_field(name="Doğum Yeri", value=dogum_yeri, inline=True)
    embed.add_field(name="Meslek", value=meslek, inline=True)
    if vesikalik and vesikalik.content_type and vesikalik.content_type.startswith("image/"):
        embed.set_image(url=vesikalik.url)
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

    if target_channel:
        view = KarakterOnayView(target_user_id=interaction.user.id, ic_isim=ic_isim)
        await target_channel.send(embed=embed, view=view)
        await interaction.followup.send("Başvurunuz yetkililere iletildi!", ephemeral=True)
    else:
        await interaction.followup.send("Karakter onay kanalı bulunamadı!", ephemeral=True)


# ==========================================
# 4. RP AÇMA, KAPAMA VE 15 DK ÖNCEDEN HABER VERME SİSTEMİ
# ==========================================
aktif_rp_panelleri = {}

class RPDurumView(View):
    def __init__(self, rp_linki: str):
        super().__init__(timeout=None)
        self.durum = "Aktif (Bekleniyor)"

@bot.tree.command(name="rp_on", description="RP duyurusunu başlatır ve 15 dk kala sivilere DM atar.")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    rp_turu="RP Türü (Örn: Şehir)",
    acilma_saati="Açılış Saati (Örn: 18:00)",
    tik_hedefi="Hedeflenen Katılımcı Sayısı",
    rp_linki="Oyunculara verilecek RP Linki",
    gorsel_url="Banner / Görsel Linki (İsteğe Bağlı)"
)
async def rp_on(
    interaction: discord.Interaction,
    rp_turu: str,
    acilma_saati: str,
    tik_hedefi: int,
    rp_linki: str,
    gorsel_url: str = None
):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(title=f"🚨 RP DUYURUSU: {rp_turu}", color=discord.Color.gold())
    embed.add_field(name="Açılış Saati", value=acilma_saati, inline=True)
    embed.add_field(name="Hedeflenen Katılımcı", value=str(tik_hedefi), inline=True)
    embed.add_field(name="RP Linki", value=f"[Tıkla Katıl]({rp_linki})", inline=False)
    embed.add_field(name="Durum", value="🟢 Aktif (Bekleniyor)", inline=False)
    if gorsel_url:
        embed.set_image(url=gorsel_url)

    view = RPDurumView(rp_linki=rp_linki)
    
    mesaj = await interaction.channel.send(embed=embed, view=view)
    aktif_rp_panelleri[interaction.channel_id] = (mesaj, view)
    
    await interaction.followup.send("RP başarıyla başlatıldı ve duyuru atıldı!", ephemeral=True)

    try:
        saat_parca = acilma_saati.split(":")
        hedef_saat = int(saat_parca[0])
        hedef_dakika = int(saat_parca[1])
        
        simdi = datetime.now()
        etkinlik_zamani = simdi.replace(hour=hedef_saat, minute=hedef_dakika, second=0, microsecond=0)
        
        if etkinlik_zamani < simdi:
            etkinlik_zamani += timedelta(days=1)
            
        haber_verme_zamani = etkinlik_zamani - timedelta(minutes=15)
        bekleme_suresi = (haber_verme_zamani - simdi).total_seconds()
        
        if bekleme_suresi > 0:
            async def bildirim_gonderici():
                await asyncio.sleep(bekleme_suresi)
                
                SIVIL_ROL_ID = 1538223860099579964
                
                for uye in interaction.guild.members:
                    if not uye.bot and any(rol.id == SIVIL_ROL_ID for rol in uye.roles):
                        try:
                            dm_embed = discord.Embed(
                                title="⏰ RP Başlıyor!", 
                                description=f"**{rp_turu}** temalı RP'nin başlamasına **15 dakika** kaldı!\nHazırlıklarını tamamla, sunucuya giriş linki:\n{rp_linki}",
                                color=discord.Color.orange()
                            )
                            await uye.send(embed=dm_embed)
                        except:
                            pass 
            
            bot.loop.create_task(bildirim_gonderici())
    except Exception as e:
        print(f"15 dk otomatik bildirim zamanlaması kurulamadı: {e}")


@bot.tree.command(name="rp_off", description="Aktif olan RP duyurusunu sonlandırır ve paneli kapatır.")
@app_commands.checks.has_permissions(administrator=True)
async def rp_off(interaction: discord.Interaction):
    if interaction.channel_id in aktif_rp_panelleri:
        mesaj, view = aktif_rp_panelleri[interaction.channel_id]
        
        for embed in mesaj.embeds:
            embed.color = discord.Color.red()
            for i, field in enumerate(embed.fields):
                if field.name == "Durum":
                    embed.set_field_at(i, name="Durum", value="🔴 Sona Erdi", inline=False)
                    
        await mesaj.edit(embed=embed, view=None)
        del aktif_rp_panelleri[interaction.channel_id]
        
        await interaction.response.send_message("🛑 RP başarıyla sonlandırıldı ve panel kapatıldı!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Bu kanalda aktif bir RP paneli bulunamadı!", ephemeral=True)


# ==========================================
# 5. 4 ADIMLI HIZ / DRIFT ODAKLI CEZA KES SİSTEMİ (EGM VE JGK ROL ID İLE)
# ==========================================
aktif_ceza_panelleri = {}
EGM_ROL_ID = 1543678246208540713  # <--- Buraya EGM rolünün ID'sini yaz!
JGK_ROL_ID = 1543678498860957716  # <--- Buraya JGK rolünün ID'sini yaz!

class CezaAdim2Select(Select):
    def __init__(self, hedef_kullanici):
        self.hedef_kullanici = hedef_kullanici
        options = [
            discord.SelectOption(label="1. Derece Men (1 Saat - Trafik)", description="Aşırı hız ve tehlikeli makaslar", emoji="🏎️"),
            discord.SelectOption(label="2. Derece Men (6 Saat - Drift/Sürüş)", description="Kalabalık yerde drift ve kontrolsüz sürüş", emoji="🚗"),
            discord.SelectOption(label="3. Derece Men (24 Saat - Kasti Zarar)", description="Non-RP, kasti kaza ve yetkiliye saygısızlık", emoji="⚠️"),
            discord.SelectOption(label="4. Derece Men (Kalıcı / Süresiz)", description="Hile, ağır ihlal ve sunucu düzenini bozma", emoji="🚨")
        ]
        super().__init__(placeholder="Lütfen ceza derecesini ve sebebini seçin...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        secilen_sebep = self.values[0]
        
        embed = discord.Embed(
            title="🛑 Ceza Sistemi - Adim 3 / 4",
            description=f"**Hedef Kullanıcı:** {self.hedef_kullanici.mention}\n**Seçilen Ceza:** {secilen_sebep}\n\nBu cezayı onaylıyor musunuz?",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Onaylandığında işlem resmiyet kazanacaktır.")
        
        onay_view = CezaOnayView(self.hedef_kullanici, secilen_sebep)
        await interaction.response.edit_message(embed=embed, view=onay_view)

class CezaAdim1View(View):
    def __init__(self, hedef_kullanici):
        super().__init__(timeout=180)
        self.hedef_kullanici = hedef_kullanici
        self.add_item(CezaAdim2Select(hedef_kullanici))

    @discord.ui.button(label="İptal Et", style=discord.ButtonStyle.red, emoji="❌")
    async def iptal(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="❌ Ceza işlemi yetkili tarafından iptal edildi.", embed=None, view=None)
        if interaction.channel.id in aktif_ceza_panelleri:
            del aktif_ceza_panelleri[interaction.channel.id]

class CezaOnayView(View):
    def __init__(self, hedef_kullanici, sebep):
        super().__init__(timeout=180)
        self.hedef_kullanici = hedef_kullanici
        self.sebep = sebep

    @discord.ui.button(label="Cezayı Uygula", style=discord.ButtonStyle.green, emoji="🔨")
    async def onayla(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🚨 Ceza Başarıyla Uygulandı (Adim 4 / 4)",
            color=discord.Color.red()
        )
        embed.add_field(name="Cezalandırılan", value=self.hedef_kullanici.mention, inline=False)
        embed.add_field(name="İşlemi Yapan Yetkili", value=interaction.user.mention, inline=False)
        embed.add_field(name="Ceza Detayı", value=self.sebep, inline=False)
        embed.add_field(name="Durum", value="🔴 Oyuncuya Ceza Verildi", inline=False)
        embed.set_footer(text=f"İşlem Zamanı: {interaction.created_at.strftime('%H:%M:%S')}")

        await interaction.response.edit_message(embed=embed, view=None)
        
        if interaction.channel.id in aktif_ceza_panelleri:
            del aktif_ceza_panelleri[interaction.channel.id]

    @discord.ui.button(label="Geri Dön", style=discord.ButtonStyle.gray, emoji="⬅️")
    async def geri(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🛑 Ceza Sistemi - Adim 1",
            description=f"Hedef kullanıcı: {self.hedef_kullanici.mention}\nLütfen aşağıdaki menüden bir ceza derecesi seçin.",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=CezaAdim1View(self.hedef_kullanici))

@bot.tree.command(name="ceza_kes", description="4 adımlı interaktif ceza ve uzaklaştırma panelini açar.")
async def ceza_kes(interaction: discord.Interaction, uye: discord.Member):
    # EGM veya JGK rolü var mı kontrolü
    user_rol_idleri = [rol.id for rol in interaction.user.roles]
    has_permission = (EGM_ROL_ID in user_rol_idleri) or (JGK_ROL_ID in user_rol_idleri)
    
    if not has_permission:
        await interaction.response.send_message("❌ Bu komutu kullanabilmek için EGM veya JGK rolüne sahip olmalısın!", ephemeral=True)
        return

    if interaction.channel.id in aktif_ceza_panelleri:
        await interaction.response.send_message("⚠️ Bu kanalda zaten aktif bir ceza paneli bulunuyor!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛑 Ceza Sistemi - Adim 1 / 4",
        description=f"Hedef kullanıcı: {uye.mention}\nLütfen devam etmek için menüden ceza derecesini seçin.",
        color=discord.Color.blue()
    )
    
    view = CezaAdim1View(uye)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    msg = await interaction.original_response()
    aktif_ceza_panelleri[interaction.channel.id] = msg


# ==========================================
# TOKEN VE BAŞLATMA
# ==========================================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    try:
        with open("token.txt", "r", encoding="utf-8") as f:
            TOKEN = f.read().strip()
    except FileNotFoundError:
        print("❌ Token bulunamadı! Lütfen token.txt oluşturun veya DISCORD_TOKEN değişkenini ayarlayın.")

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)