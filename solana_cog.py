import discord
from discord.ext import commands
from datetime import datetime, timezone
import logging
import config
from solana_tracker import SolanaTracker

logger = logging.getLogger(__name__)

class SolanaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.solana_tracker = SolanaTracker()
    
    @commands.command(name='soladd')
    @commands.has_permissions(administrator=True)
    async def solana_add_address(self, ctx, address: str, nickname: str = None):
        """Ajoute une adresse Solana au tracking
        
        Usage: !soladd <address> [nickname]
        Exemple: !soladd 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM "Wallet Principal"
        """
        try:
            # Vérifier si l'adresse est valide
            if not address or len(address) < 32:
                await ctx.send("❌ Adresse Solana invalide. Format attendu: 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
                return
            
            # Ajouter l'adresse au tracker
            success = await self.solana_tracker.add_address(
                address=address,
                nickname=nickname,
                added_by=str(ctx.author)
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Adresse Solana ajoutée",
                    description=f"L'adresse `{address}` a été ajoutée au tracking.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                if nickname:
                    embed.add_field(name="Surnom", value=nickname, inline=True)
                embed.add_field(name="Ajoutée par", value=ctx.author.mention, inline=True)
                embed.set_footer(text="Vous recevrez des notifications pour tous les mouvements de cette adresse")
                
                await ctx.send(embed=embed)
                logger.info(f"Solana address {address} added by {ctx.author}")
            else:
                await ctx.send("❌ Erreur lors de l'ajout de l'adresse. Vérifiez que l'adresse est valide.")
                
        except Exception as e:
            logger.error(f"Error adding Solana address: {e}")
            await ctx.send(f"❌ Erreur lors de l'ajout de l'adresse: {str(e)}")
    
    @commands.command(name='solremove')
    @commands.has_permissions(administrator=True)
    async def solana_remove_address(self, ctx, address: str):
        """Retire une adresse Solana du tracking
        
        Usage: !solremove <address>
        Exemple: !solremove 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
        """
        try:
            success = await self.solana_tracker.remove_address(address)
            
            if success:
                embed = discord.Embed(
                    title="✅ Adresse Solana retirée",
                    description=f"L'adresse `{address}` a été retirée du tracking.",
                    color=discord.Color.green(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Retirée par", value=ctx.author.mention, inline=True)
                
                await ctx.send(embed=embed)
                logger.info(f"Solana address {address} removed by {ctx.author}")
            else:
                await ctx.send("❌ Adresse non trouvée dans la liste des adresses trackées.")
                
        except Exception as e:
            logger.error(f"Error removing Solana address: {e}")
            await ctx.send(f"❌ Erreur lors de la suppression de l'adresse: {str(e)}")
    
    @commands.command(name='sollist')
    async def solana_list_addresses(self, ctx):
        """Affiche la liste des adresses Solana trackées"""
        try:
            addresses = self.solana_tracker.get_tracked_addresses()
            
            if not addresses:
                await ctx.send("📝 Aucune adresse Solana n'est actuellement trackée.")
                return
            
            embed = discord.Embed(
                title="📝 Adresses Solana trackées",
                description=f"Total: {len(addresses)} adresse(s)",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Diviser la liste en chunks si trop longue
            chunk_size = 5
            for i in range(0, len(addresses), chunk_size):
                chunk = addresses[i:i + chunk_size]
                field_value = ""
                for addr in chunk:
                    nickname = f" ({addr['nickname']})" if addr['nickname'] else ""
                    field_value += f"`{addr['address']}`{nickname}\n"
                
                embed.add_field(
                    name=f"Adresses {i+1}-{min(i+chunk_size, len(addresses))}",
                    value=field_value,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing Solana addresses: {e}")
            await ctx.send(f"❌ Erreur lors de l'affichage de la liste: {str(e)}")
    
    @commands.command(name='solactivity')
    async def solana_activity(self, ctx, address: str = None, limit: int = 10):
        """Affiche l'activité récente d'une adresse Solana ou toutes les adresses
        
        Usage: !solactivity [address] [limit]
        Exemple: !solactivity 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM 20
        """
        try:
            if limit > 50:
                limit = 50  # Limiter à 50 pour éviter les messages trop longs
            
            activities = self.solana_tracker.get_recent_activity(address, limit)
            
            if not activities:
                if address:
                    await ctx.send(f"📊 Aucune activité récente trouvée pour l'adresse `{address}`")
                else:
                    await ctx.send("📊 Aucune activité récente trouvée.")
                return
            
            embed = discord.Embed(
                title="📊 Activité Solana récente",
                color=discord.Color.purple(),
                timestamp=datetime.now(timezone.utc)
            )
            
            if address:
                embed.description = f"Activité pour `{address}` (limite: {limit})"
            else:
                embed.description = f"Activité globale (limite: {limit})"
            
            # Grouper par adresse
            activities_by_address = {}
            for activity in activities:
                addr = activity['address']
                if addr not in activities_by_address:
                    activities_by_address[addr] = []
                activities_by_address[addr].append(activity)
            
            # Afficher les activités
            for addr, addr_activities in list(activities_by_address.items())[:3]:  # Limiter à 3 adresses
                field_value = ""
                for activity in addr_activities[:5]:  # 5 activités max par adresse
                    tx_type = activity.get('transaction_type', 'unknown')
                    amount = activity.get('amount')
                    signature = activity.get('signature', '')[:8] + "..."
                    
                    if amount:
                        field_value += f"**{tx_type}** - {amount} - `{signature}`\n"
                    else:
                        field_value += f"**{tx_type}** - `{signature}`\n"
                
                embed.add_field(
                    name=f"Adresse: {addr[:8]}...",
                    value=field_value or "Aucune activité",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error showing Solana activity: {e}")
            await ctx.send(f"❌ Erreur lors de l'affichage de l'activité: {str(e)}")
    
    @commands.command(name='solsettings')
    @commands.has_permissions(administrator=True)
    async def solana_settings(self, ctx, address: str, min_amount: float = 0, notification_types: str = "all"):
        """Configure les paramètres de notification pour une adresse Solana
        
        Usage: !solsettings <address> <min_amount> <notification_types>
        Exemple: !solsettings 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM 100 token_transfer,dex_swap
        """
        try:
            success = self.solana_tracker.db.set_notification_settings(
                address=address,
                min_amount=min_amount,
                notification_types=notification_types,
                discord_channel_id=ctx.channel.id
            )
            
            if success:
                embed = discord.Embed(
                    title="⚙️ Paramètres de notification configurés",
                    description=f"Paramètres mis à jour pour l'adresse `{address}`",
                    color=discord.Color.blue(),
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Montant minimum", value=f"{min_amount}", inline=True)
                embed.add_field(name="Types de notifications", value=notification_types, inline=True)
                embed.add_field(name="Canal Discord", value=ctx.channel.mention, inline=True)
                
                await ctx.send(embed=embed)
                logger.info(f"Solana notification settings updated for {address} by {ctx.author}")
            else:
                await ctx.send("❌ Erreur lors de la configuration des paramètres.")
                
        except Exception as e:
            logger.error(f"Error setting Solana notification settings: {e}")
            await ctx.send(f"❌ Erreur lors de la configuration: {str(e)}")
    
    @commands.command(name='soltest')
    @commands.has_permissions(administrator=True)
    async def solana_test_connection(self, ctx):
        """Test la connexion aux endpoints Solana (RPC et WebSocket)
        
        Usage: !soltest
        """
        try:
            embed = discord.Embed(
                title="🧪 Test de Connexion Solana",
                description="Test des endpoints QuickNode Solana...",
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Test RPC
            rpc_status = "❌ Non configuré"
            rpc_url = config.SOLANA_RPC_URL
            if rpc_url:
                try:
                    from solana.rpc.async_api import AsyncClient
                    test_client = AsyncClient(rpc_url)
                    version = await test_client.get_version()
                    await test_client.close()
                    rpc_status = f"✅ Connecté (v{version.value})"
                except Exception as e:
                    rpc_status = f"❌ Erreur: {str(e)[:50]}..."
            else:
                rpc_status = "❌ SOLANA_RPC_URL non configuré"
            
            # Test WebSocket
            ws_status = "❌ Non configuré"
            ws_url = config.SOLANA_WS_URL
            if ws_url:
                try:
                    import websockets
                    async with websockets.connect(ws_url, timeout=10) as websocket:
                        await websocket.ping()
                        ws_status = "✅ Connecté"
                except Exception as e:
                    ws_status = f"❌ Erreur: {str(e)[:50]}..."
            else:
                ws_status = "❌ SOLANA_WS_URL non configuré"
            
            # Test du tracker
            tracker_status = "❌ Non initialisé"
            try:
                if hasattr(self, 'solana_tracker') and self.solana_tracker:
                    tracker_status = "✅ Initialisé"
                else:
                    tracker_status = "❌ SolanaTracker non trouvé"
            except Exception as e:
                tracker_status = f"❌ Erreur: {str(e)[:50]}..."
            
            # Ajouter les résultats à l'embed
            embed.add_field(
                name="🔗 RPC Endpoint",
                value=f"**Status:** {rpc_status}\n**URL:** `{rpc_url[:50]}...`" if rpc_url else f"**Status:** {rpc_status}",
                inline=False
            )
            
            embed.add_field(
                name="🌐 WebSocket Endpoint",
                value=f"**Status:** {ws_status}\n**URL:** `{ws_url[:50]}...`" if ws_url else f"**Status:** {ws_status}",
                inline=False
            )
            
            embed.add_field(
                name="🤖 Solana Tracker",
                value=f"**Status:** {tracker_status}",
                inline=False
            )
            
            # Déterminer la couleur finale
            if "✅" in rpc_status and "✅" in ws_status and "✅" in tracker_status:
                embed.color = discord.Color.green()
                embed.title = "✅ Test de Connexion Solana - SUCCÈS"
            else:
                embed.color = discord.Color.orange()
                embed.title = "⚠️ Test de Connexion Solana - PROBLÈMES DÉTECTÉS"
            
            embed.set_footer(text="Vérifiez les variables d'environnement sur Railway si des erreurs sont détectées")
            
            await ctx.send(embed=embed)
            logger.info(f"Solana connection test performed by {ctx.author}")
            
        except Exception as e:
            logger.error(f"Error testing Solana connection: {e}")
            await ctx.send(f"❌ Erreur lors du test de connexion: {str(e)}")

async def setup(bot):
    await bot.add_cog(SolanaCog(bot))
