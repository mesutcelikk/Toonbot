import discord
from discord.ext import commands
from collections import Counter
import random
import datetime
import traceback


# TODO: Create custom Reaction setups per server
# TODO: Bad words filter.

class GlobalChecks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_check(self.disabled_commands)
        self.bot.add_check(self.ignored)
        self.bot.commands_used = Counter()
    
    def ignored(self, ctx):
        return ctx.author.id not in self.bot.ignored
    
    def disabled_commands(self, ctx):
        try:
            if ctx.command.name in self.bot.disabled_cache[ctx.guild.id]:
                return False
            else:
                return True
        except (KeyError, AttributeError):
            return True


class Reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_socket_response(self, msg):
        self.bot.socket_stats[msg.get('t')] += 1
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.commands_used[ctx.command.name] += 1
    
    # Error Handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Fail silently.
        
        elif isinstance(error, (commands.NoPrivateMessage, commands.MissingPermissions)):
            if ctx.guild is None:
                return await ctx.send('🚫 This command cannot be used in DMs')
            
            if len(error.missing_perms) == 1:
                perm_string = error.missing_perms[0]
            else:
                last_perm = error.missing_perms.pop(-1)
                perm_string = ", ".join(error.missing_perms) + " and " + last_perm
            return await ctx.send(f'🚫 You need {perm_string} permissions to do that.')
        
        elif isinstance(error, (discord.Forbidden, commands.DisabledCommand)):
            if isinstance(error, discord.Forbidden):
                print(f"Discord.Forbidden Error, check {ctx.command} bot_has_permissions  {ctx.message.content}\n"
                      f"{ctx.author}) in {ctx.channel.name} on {ctx.guild.name}")
            try:
                await ctx.message.add_reaction('⛔')
            except discord.Forbidden:
                return
        
        elif isinstance(error, commands.BotMissingPermissions):
            if len(error.missing_perms) == 1:
                perm_string = error.missing_perms[0]
            else:
                last_perm = error.missing_perms.pop(-1)
                perm_string = ", ".join(error.missing_perms) + " and " + last_perm
            return await ctx.send(
                f'🚫 I need {perm_string} permissions to do that.\n\n'
                f'If you have another bot for this command, you can disable this command for me with '
                f'{ctx.me.mention} disable {ctx.command}\n\nYou can also stop prefix clashes by using '
                f'{ctx.me.mention}prefix remove {ctx.prefix} to stop me sharing the `{ctx.prefix}` prefix.')
        
        elif isinstance(error, commands.CommandInvokeError):
            print(f"Error: ({ctx.author} ({ctx.author.id}) on {ctx.guild.name} ({ctx.guild.id}))\n"
                  f"Context: {ctx.message.content}\nIn {ctx.command.qualified_name}:")
            traceback.print_tb(error.original.__traceback__)
            print(f'{error.original.__class__.__name__}: {error.original}')
            return
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'⏰ On cooldown for {str(error.retry_after).split(".")[0]}s', delete_after=5)
            return
        
        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send(f"🚫 This command can only be used in NSFW channels.")
            return
        else:
            print(f"Unhandled Error Type: {error.original.__class__.__name__}\n"
                  f"({ctx.author} on {ctx.guild.name}) caused the following error\n"
                  f"{error}\n"
                  f"Context: {ctx.message.content}\n")
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # ignore bots
        if message.author.bot:
            return
        
        # ignore dms
        if message.guild is None:
            return
        
        # ignore Toonbot command messages.
        for i in self.bot.prefix_cache[message.guild.id]:
            if message.content.startswith(i):
                return
        
        # TODO - Cross server.
        if not message.guild.id == 332159889587699712:
            return
        
        # Filter out deleted numbers - Toonbot.
        try:
            int(message.content)
        except ValueError:
            pass
        else:
            return
        
        # Todo: Code "If message was not deleted by bot or user return "
        
        delchan = self.bot.get_channel(id=335816981423063050)
        e = discord.Embed(title="Deleted Message")
        e.description = f"'{message.content}'"
        e.set_author(name=message.author.name)
        e.add_field(name="User ID", value=message.author.id)
        e.add_field(name="Channel", value=message.channel.mention)
        e.set_thumbnail(url=message.author.avatar_url)
        e.timestamp = datetime.datetime.now()
        e.set_footer(text=f"Created: {message.created_at}")
        e.colour = message.author.color
        if message.attachments:
            att = message.attachments[0]
            if hasattr(att, "height"):
                e.add_field(name=f"Attachment info {att.filename} ({att.size} bytes)",
                            value=f"{att.height}x{att.width}")
                e.set_image(url=att.proxy_url)
        await delchan.send(embed=e)
    
    @commands.Cog.listener()
    async def on_message(self, m):
        c = m.content.lower()
        # ignore bot messages
        if m.author.bot:
            return
        
        if m.guild and m.guild.id == 332159889587699712:
            autokicks = ["make me a mod", "make me mod", "give me mod"]
            for i in autokicks:
                if i in c:
                    try:
                        await m.author.kick(reason="Asked to be made a mod.")
                    except discord.Forbidden:
                        return await m.channel.send(f"Done. {m.author.mention} is now a moderator.")
                    await m.channel.send(f"{m.author} was auto-kicked.")
            if "https://www.reddit.com/r/" in c and "/comments/" in c:
                if "nufc" not in c:
                    rm = "*Reminder: Please do not vote on submissions or comments in other subreddits.*"
                    await m.channel.send(rm)
        # Emoji reactions
        if "toon toon" in c:
            await m.channel.send("**BLACK AND WHITE ARMY**")


def setup(bot):
    bot.add_cog(Reactions(bot))
    bot.add_cog(GlobalChecks(bot))
