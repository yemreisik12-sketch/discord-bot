import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
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
        synced = await bot.tree.sync()
        print(f"{len(synced)} adet komut senkronize edildi.")
    except Exception as e:
        print(e)

# ==========================================
# 1. ARAÇ ALIM SİSTEMİ (Örnek Komut)
# ==========================================
@bot.tree.command(name="arac_alim", description="Araç alım talebi oluşturur.")
@app_commands.describe(arac_modeli="Araç Modeli", plaka="İstediğiniz Plaka")
async def arac_alim(interaction: discord.Interaction, arac_modeli: str, plaka: str):
    await interaction.response.defer(ephemeral=True)
    ARAC_KANAL_ID = 1543684123002937514 
    target_channel = interaction.guild.get_channel(ARAC_KANAL_ID)
    
    embed = discord.Embed(title="🚗 Yeni Araç Alım Talebi", color=discord.Color.blue())
    embed.add_field(name="Başvuran", value=interaction.user.mention, inline=False)
    embed.add_field(name="Araç Modeli", value=arac_modeli, inline=False)
    embed.add_field(name="İstenen Plaka", value=plaka, inline=False)
    
    if target_channel:
        await target_channel.send(embed=embed)
        await interaction.followup.send("Araç alım talebin yetkililere iletildi!", ephemeral=True)
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

        # Kullanıcının sunucu içindeki takma adını otomatik IC isim yapma
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

import os

# Güvenli Token Okuma (Hem bilgisayar hem bulut sunucu uyumlu)
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