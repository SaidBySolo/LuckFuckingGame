import asyncio
from typing import Any, Optional
from discord.embeds import Embed
from discord.ext.commands import Bot
from discord import Intents
from discord.ext.commands.context import Context
from discord.ext.commands.errors import BadArgument, MissingRequiredArgument
from discord.message import Message
from utils.provablyfair import ProvablyFair, RolledData


class Casino(Bot):
    def __init__(self, command_prefix: str, **options: Any) -> None:
        self.registered: list[int] = []
        self.participants: Any = {}
        self.gammer = []
        self.total_money: int = 0
        self.game: Optional[Message] = None
        self.created: bool = False
        super().__init__(command_prefix, help_command=None, **options)


bot = Casino("casino", intents=Intents.all())
bot.load_extension("jishaku")


@bot.command("register")
async def _register(ctx: Context):
    if ctx.author.id in bot.registered:
        return await ctx.send("Already registerd")
    bot.registered.append(ctx.author.id)
    bot.participants.update(
        {ctx.author.id: {"money": 10000, "id": ctx.author.id}})
    await ctx.send("Succesfully")


@bot.command("money")
async def _money(ctx: Context):
    if ctx.author.id not in bot.registered:
        return await ctx.send("Please register")
    await ctx.send(f"My money: {bot.participants[ctx.author.id]['money']}")


@bot.command("open")
async def _casino(ctx: Context, time: int, client_seed: str = None):
    if ctx.author.id not in bot.registered:
        return await ctx.send("Please register")
    if not bot.created and not bot.game:
        if time < 0 or time > 180:
            return await ctx.send("The time is negative or cannot exceed 180 seconds")
        bot.created = True
        pf = ProvablyFair(client_seed)
        bot.game = await ctx.send(
            embed=Embed(
                title="Gamble ON",
                description=f"Client seed: ``{pf.client_seed}``\nNonce: ``{pf.nonce}``\n",
            )
            .add_field(name=f"Current bet amount", value=str(bot.total_money))
            .set_footer(text=f"Server seed hash: {pf.server_seed_hash}")
        )
        await asyncio.sleep(time)

        try:
            rolled = pf.roll()

            if 0 <= rolled <= 500_000:
                win = "black"
            else:
                win = "white"

            if not bot.gammer:
                return await ctx.send(
                    embed=Embed(
                        title=f"Gamble OFF\n\nServer seed: ``{pf.server_seed}``",
                        description=f"Client seed: ``{pf.client_seed}``\n\nNonce: ``{pf.nonce}``\n\nRolled: ``{rolled}``",
                    )
                    .add_field(name="Winner", value=win)
                    .add_field(name=f"Nobody joined", value="None")
                    .set_footer(text=f"Server seed hash: {pf.server_seed_hash}")
                )
            elif 1 == len(bot.gammer):
                id = bot.gammer[0]
                bot.participants[id]["money"] += bot.total_money
                return await ctx.send(
                    embed=Embed(
                        title=f"Gamble OFF\n\nServer seed: ``{pf.server_seed}``",
                        description=f"Client seed: ``{pf.client_seed}``\n\nNonce: ``{pf.nonce}``\n\nRolled: ``{rolled}``",
                    )
                    .add_field(name="Winner", value=win)
                    .add_field(
                        name=f"went back to the host", value=str(bot.total_money)
                    )
                    .set_footer(text=f"Server seed hash: {pf.server_seed_hash}")
                )

            winlist = list(
                filter(lambda ele: ele["color"] ==
                       win, bot.participants.values())
            )

            win_money = bot.total_money // len(winlist)

            for winner in winlist:
                id = winner["id"]
                bot.participants[id]["money"] += win_money

            await ctx.send(
                embed=Embed(
                    title=f"Gamble OFF\n\nServer seed: ``{pf.server_seed}``",
                    description=f"Client seed: ``{pf.client_seed}``\n\nNonce: ``{pf.nonce}``\n\nRolled: ``{rolled}``",
                )
                .add_field(name="Winner", value=win)
                .add_field(
                    name=f"Amount to return to the winning team",
                    value=str(bot.total_money),
                )
                .set_footer(text=f"Server seed hash: {pf.server_seed_hash}")
            )

        finally:
            bot.created = False
            bot.game = None
            bot.gammer = []
            bot.total_money = 0


@bot.command("join")
async def _join(ctx: Context, color: str, bet: int):
    if ctx.author.id not in bot.registered:
        return await ctx.send("Please register")
    elif not bot.created:
        return await ctx.send("Must make first gamble")
    elif ctx.author.id in bot.gammer:
        await ctx.send("Already joined")
    else:
        if color not in ["red", "green"]:
            return await ctx.send("Must choice in ``black`` ``white``")

        m = bot.participants[ctx.author.id]["money"]

        if m - bet < 0 or 0 > bet:
            return await ctx.send(
                "You bet more than you have, or the amount you bet is incorrect."
            )

        bot.gammer.append(ctx.author.id)
        bot.participants[ctx.author.id]["color"] = color
        bot.participants[ctx.author.id]["money"] -= bet
        bot.total_money += bet

        embed_dict = bot.game.embeds[0].to_dict()
        embed_dict["fields"][0]["value"] = str(bot.total_money)

        await ctx.send(f"Joined now total bet: {bot.total_money}")

        await bot.game.edit(embed=Embed.from_dict(embed_dict))


@bot.command("verify")
async def _verify(
    ctx: Context,
    roll: int,
    nonce: int,
    server_seed: str,
    server_seed_hash: str,
    client_seed: str,
):
    pf = ProvablyFair()
    rd = RolledData(roll, nonce, server_seed_hash, client_seed)
    is_verify = pf.verify_roll(server_seed, rd)

    if is_verify:
        return await ctx.send("verified")
    else:
        return await ctx.send("not verified")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, BadArgument):
        return await ctx.send("Bad argument")
    elif isinstance(error, MissingRequiredArgument):
        return await ctx.send("Missing required argument")
    else:
        raise error


bot.run("token here XD")
