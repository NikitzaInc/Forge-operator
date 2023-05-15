# Here is a small discord bot i've made for my friend's server
# The bot helps users to make an order in my friends's forge
# Sorry for the poor translation in some places, English is not my native language and I can sometimes make mistakes
# I wouldn't have been able to make this bot without the help of github of Martine discord bot, great thanks to https://github.com/MartineBot and PredaaA
# Feel free to copy my code and use it for your projects! 

# How the bot works:
# When the bot enters the server, the admin must set the channel where users can leave orders and the channel where blacksmiths can see these orders
# The admin should send special slash command /setupbot (/setup command is also shown in bot's command list, I don't understand why this command is there, I didn't ever made it ಠ_ಠ)
# When someone wants to order something, bot send him a ephemeral message with some information and select menu (discord.ui.Select) where user can choose items he wants to buy
# Bot also sends some buttons (discord.ui.Button):
# 1 - "SelectEnchantments" which let user choose what enchantments he wants to be applied to his items
# 2 - "OrderNetherite" which let user choose what items he wants to be made of netherite
# 3 - "OrderComment" which let user add a comment to his order
# 4 - "OrderSubmit" which let user save his order and send it to the blacksmiths
# The bot doesn't allow two players to make orders at the same time
# When order is sent to blacksmiths, they can accept the order or reject the order
# If they accept the order, they can reject the order if they face some troubles with it or, when order is ready, they can tell user that his order is ready
# User gets messages from the bot in DM about his order
# The bot keeps in his memory up to 10 orders, next ones overwrite the previous ones.

import traceback
from discord import app_commands
import discord
from threading import Timer
     
# Guild in discord API means discord server
MY_GUILD = discord.Object(id=your_guild_id)

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)

# Firstly, admin should send special slash command /setupbot to submit the channel where users can leave orders and the channel where blacksmiths can see these orders
@client.tree.command()

@app_commands.describe(
    channel_orders="Задайте канал, в котором покупатели смогут оставить свой заказ.",
    channel_orderlist="Задайте канал, в котором кузнецы смогут видеть и принимать поступившие заказы.",

)
async def setupbot(interaction: discord.Interaction, channel_orders:discord.TextChannel, channel_orderlist:discord.TextChannel):
    """Задать каналы, где можно заказать и где отображаются оставленные заказы."""

    # I made a system which only allows me and my friend to use the slash command
    if  interaction.user.id == 366490933614608384 or interaction.user.id == 664948560818864166:
        
        # To response to a slash command/button/select menu/etc. we should use interaction.response.send_message()
        # Ephemeral parameter means that the response can only be seen by the person who started the interaction 
        await interaction.response.send_message(ephemeral=True, content='Каналы '+ channel_orders.name+' и '+channel_orderlist.name+ ' заданы!')
        orderlistInfo = discord.Embed(title="Этот канал назначен списком заказов!",color=discord.Colour.from_str('0x2366c4'))

        # Bot sends some starting information to the channels, submitted by admin
        await channel_orders.send("https://cdn.discordapp.com/attachments/939131677408653322/1104542455182925955/kuznya2.png")
        await channel_orderlist.send(embed=orderlistInfo)
        view=OrderButtonView()
        await channel_orders.send(view=view)

        # This variable we will need later
        global channel_orderlist_tinker
        channel_orderlist_tinker = channel_orderlist

    else:
        await interaction.response.send_message(":x: У вас нет права делать это!",ephemeral=True)

# Here are some variables and lists we will need
makingOrder = False
orderCommentSubmit = False
netherite = False

orderValues = [""]
netheriteValues = [""]
    
trezubEnchants = [""]
swordEnchants = [""]
crossbowEnchants = [""]
bowEnchants = [""]
axeEnchants = [""]
pickaxeEnchants = [""]
shovelEnchants = [""]
hoeEnchants = [""]
fishingRodEnchants = [""]
bootsEnchants = [""]
turtleEnchants = [""]
helmetEnchants = [""]
chestplateEnchants = [""]
leggingsEnchants = [""]
flintNsteelEnchants = [""]
shieldEnchants = [""]
scissorsEnchants = [""]

valueNumber = 0
orderIDname = [discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User]
orderIDnumber = [0,0,0,0,0,0,0,0,0,0]


# After each order we have to clear values of all variables and lists
# I understand that my code sometimes looks very goofy, but I don't understand how to make some things better
async def clearValues():
    global orderCommentSubmit
    global netherite

    global orderValues
    global netheriteValues

    global trezubEnchants
    global swordEnchants
    global crossbowEnchants
    global bowEnchants
    global axeEnchants
    global pickaxeEnchants
    global shovelEnchants
    global hoeEnchants
    global fishingRodEnchants
    global bootsEnchants
    global turtleEnchants
    global helmetEnchants
    global chestplateEnchants
    global leggingsEnchants
    global flintNsteelEnchants
    global shieldEnchants
    global scissorsEnchants

    orderCommentSubmit = False
    netherite = False

    orderValues = ["-"]
    netheriteValues = ["-"]
    
    trezubEnchants = ["-"]
    swordEnchants = ["-"]
    crossbowEnchants = ["-"]
    bowEnchants = ["-"]
    axeEnchants = ["-"]
    pickaxeEnchants = ["-"]
    shovelEnchants = ["-"]
    hoeEnchants = ["-"]
    fishingRodEnchants = ["-"]
    bootsEnchants = ["-"]
    turtleEnchants = ["-"]
    helmetEnchants = ["-"]
    chestplateEnchants = ["-"]
    leggingsEnchants = ["-"]
    flintNsteelEnchants = ["-"]
    shieldEnchants = ["-"]
    scissorsEnchants = ["-"]

    

# If someone started making an order and didn't finish within 10 minutes, bot should clean all the values and lists and allow another user make his order
async def timeout():
    global makingOrder
    makingOrder = False
    await clearValues()
    print("Order timed out!")
    print("-------")

# The main menu of an order, there user can choose items to buy and press the buttons (you can see them in lines 12-15) 
class StartOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Составить заказ!", custom_id="order",)

    async def callback(self, interaction:discord.Interaction): 
        embed1 = discord.Embed(
            title="Составьте ваш заказ!",
            color=discord.Colour.from_str('0x2366c4'),
            description="В выпадающем списке выберите товары, которые хотите приобрести.")
        embed1.add_field(name="Выбрать зачарования",value="Не забудьте выбрать зачарования для предметов! ***Имейте ввиду, что некоторые зачарования конфликтуют друг с другом. Если выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование!***",inline=False)
        embed1.add_field(name="Материал товара",value="***Все предметы брони, мечи и инструменты по умолчанию делаются алмазными.*** Если вас интересует незеритовый аналог товара, выберите его, нажав на соответствующую кнопку. Если же вас интересует иной материал, пожалуйста опишите это в комментарии к заказу.",inline=False)
        embed1.add_field(name="Добавить комментарий к заказу",value="Также можно добавить комментарий к заказу. Укажите все подробности заказа, например, место доставки, особенности материала или чар.",inline=False)
        embed1.add_field(name="Выбранные товары:",value="-",inline=True)

        embedCantStartOrder = discord.Embed(title=":clock2: В данный момент бот занят, пожалуйста попробуйте позже!",color=discord.Colour.from_str('0x2366c4'),)
        global makingOrder
        view=OrderView()

        # The bot doesn't allow two players to make orders at the same time
        if makingOrder == False:
            await interaction.response.send_message(embed=embed1,view=view,ephemeral=True)
            await clearValues()
            
            makingOrder = True
            print(interaction.user.name+" is making new order!")
            print("-------")
            t = Timer(600,timeout)
            t.start()

         
        else:
            await interaction.response.send_message(embed=embedCantStartOrder,ephemeral=True)
            print(interaction.user.name+" failed to order")
            print("-------")





#Selects

# Main selection menu where user can choose items to buy
class OrderSelect(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Трезубец"),
            discord.SelectOption(label="Меч"),
            discord.SelectOption(label="Арбалет"),
            discord.SelectOption(label="Лук"),
            discord.SelectOption(label="Топор"),
            discord.SelectOption(label="Кирка"), 
            discord.SelectOption(label="Лопата"),
            discord.SelectOption(label="Мотыга"),
            discord.SelectOption(label="Удочка"),
            discord.SelectOption(label="Черепаший панцирь"),
            discord.SelectOption(label="Шлем"),
            discord.SelectOption(label="Нагрудник"),
            discord.SelectOption(label="Поножи"),
            discord.SelectOption(label="Ботинки"),
            discord.SelectOption(label="Зажигалка"),
            discord.SelectOption(label="Щит"),
            discord.SelectOption(label="Ножницы")
        ]
        super().__init__(placeholder="Выберите нужные товары", min_values=1, max_values=17, options=options)
    
    async def callback(self, interaction:discord.Interaction):
        embedEdit = discord.Embed(
            title="Составьте ваш заказ!",
            color=discord.Colour.from_str('0x2366c4'),
            description="В выпадающем списке выберите товары, которые хотите приобрести.")
        embedEdit.add_field(name="Выбрать зачарования",value="Не забудьте выбрать зачарования для предметов! ***Имейте ввиду, что некоторые зачарования конфликтуют друг с другом. Если выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование!***",inline=False)
        embedEdit.add_field(name="Материал товара",value="***Все предметы брони, мечи и инструменты по умолчанию делаются алмазными.*** Если вас интересует незеритовый аналог товара, выберите его, нажав на соответствующую кнопку. Если же вас интересует иной материал, пожалуйста опишите это в комментарии к заказу.",inline=False)
        embedEdit.add_field(name="Добавить комментарий к заказу",value="Также можно добавить комментарий к заказу. Укажите все подробности заказа, например, место доставки, особенности материала или чар.",inline=False)
        embedEdit.add_field(name="Выбранные товары:",value=self.values,inline=True)
        await interaction.response.defer(ephemeral=True)  
        await interaction.edit_original_response(embed=embedEdit)

        global orderValues
        orderValues = self.values
        
        global trezub
        global sword
        global crossbow
        global bow
        global axe
        global pickaxe
        global shovel
        global hoe
        global fishingRod
        global boots
        global turtle
        global helmet
        global chestplate
        global leggings
        global flintNsteel
        global shield
        global scissors

        # These variables contain data about which items are selected by the user.
        trezub = False
        sword = False
        crossbow = False
        bow = False
        axe = False
        pickaxe = False
        shovel = False
        hoe = False
        fishingRod = False
        boots = False
        turtle = False
        helmet = False
        chestplate = False
        leggings = False
        flintNsteel = False
        shield = False
        scissors = False
        

        i=0

        print("Items chosen by "+ interaction.user.name +":")
        while i < len(self.values):
            print(self.values[i])
            if self.values[i] == "Трезубец":
                trezub = True
            if self.values[i] == "Меч":
                sword = True
            if self.values[i] == "Арбалет":
                crossbow = True
            if self.values[i] == "Лук":
                bow = True
            if self.values[i] == "Топор":
                axe = True
            if self.values[i] == "Кирка":
                pickaxe = True
            if self.values[i] == "Лопата":
                shovel = True
            if self.values[i] == "Мотыга":
                hoe = True
            if self.values[i] == "Удочка":
                fishingRod = True
            if self.values[i] == "Черепаший панцирь":
                turtle = True
            if self.values[i] == "Шлем":
                helmet = True
            if self.values[i] == "Нагрудник":
                chestplate = True
            if self.values[i] == "Поножи":
                leggings = True
            if self.values[i] == "Ботинки":
                boots = True
            if self.values[i] == "Зажигалка":
                flintNsteel = True
            if self.values[i] == "Щит":
                shield = True
            if self.values[i] == "Ножницы":
                scissors = True

            i += 1
        print("-------")





# Selection menu where users can choose what items should br done with netherite
class OrderSelectNetherite(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Всe выбранные товары"),
            discord.SelectOption(label="Меч"),
            discord.SelectOption(label="Топор"),
            discord.SelectOption(label="Кирка"),
            discord.SelectOption(label="Лопата"),
            discord.SelectOption(label="Мотыга"),
            discord.SelectOption(label="Шлем"),
            discord.SelectOption(label="Нагрудник"),
            discord.SelectOption(label="Поножи"),
            discord.SelectOption(label="Ботинки"),
        ]
        super().__init__(placeholder="Выберите нужные товары", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global netheriteValues 
        global netherite
        netheriteValues = self.values
        netherite = True

        embedEdit = discord.Embed(title="Выберите товары, которые необходимо сделать из незерита!",color=discord.Colour.from_str('0x2366c4')) 
        embedEdit.add_field(name="Из незерита будут сделаны:",value=self.values,inline=False) 
        await interaction.response.defer(ephemeral=True)  
        await interaction.edit_original_response(embed=embedEdit)


# Enchantments selrction menus
# Here we allow user to choose enchantments for his items
# Trident Enchantments  
class SelectTrezubEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Громовержец"),
            discord.SelectOption(label="Пронзатель (V)",description="Несовместимо с тягуном."),
            discord.SelectOption(label="Верность (III)",description="Несовместимо с тягуном."),
            discord.SelectOption(label="Тягун (III)",description="Несовместимо с пронзателем, верностью."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования трезубца", min_values=1, max_values=7, options=options)
        
    

    async def callback(self, interaction:discord.Interaction):
            global trezubEnchants
            trezubEnchants = self.values

            trezubEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
            if trezub == True:
                trezubEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            if sword == True:
                trezubEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            if crossbow == True:
                trezubEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            if bow == True:
                trezubEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=trezubEmbed)

# Sword Enchantments
class SelectSwordEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Острота (V)",description="Несовместимо с бичом членистоногих, небесной карой."),
            discord.SelectOption(label="Бич членистоногих (V)",description="Несовместимо с остротой, небесной карой."),
            discord.SelectOption(label="Небесная кара (V)",description="Несовместимо с бичом членистоногих, остротой."),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Разящий клинок (III)"),
            discord.SelectOption(label="Заговор огня (II)"),
            discord.SelectOption(label="Отдача (II)"),
            discord.SelectOption(label="Добыча (III)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования меча", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
            global swordEnchants
            swordEnchants = self.values
            
            swordEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
            if trezub == True:
                swordEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            if sword == True:
                swordEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            if crossbow == True:
                swordEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            if bow == True:
                swordEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=swordEmbed)

# Crossbow Enchantments
class SelectCrossbowEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Тройной выстрел",description="Несовместимо с пронзающей стрелой."),
            discord.SelectOption(label="Пронзающая стрела (IV)",description="Несовместимо с тройным выстрелом."),
            discord.SelectOption(label="Быстрая перезарядка (III)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования арбалета", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
            global crossbowEnchants
            crossbowEnchants = self.values

            crossbowEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
            if trezub == True:
                crossbowEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            if sword == True:
                crossbowEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            if crossbow == True:
                crossbowEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            if bow == True:
                crossbowEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=crossbowEmbed)

# Bow Enchantments
class SelectBowEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Несовместимо с бесконечностью."),
            discord.SelectOption(label="Бесконечность",description="Несовместимо с починкой."),
            discord.SelectOption(label="Сила (V)"),
            discord.SelectOption(label="Отбрасывание (II)"),
            discord.SelectOption(label="Горящая стрела"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования лука", min_values=1, max_values=7, options=options)

    async def callback(self, interaction:discord.Interaction):
        global bowEnchants
        bowEnchants = self.values

        bowEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
        if trezub == True:
            bowEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
        if sword == True:
            bowEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
        if crossbow == True:
            bowEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
        if bow == True:
            bowEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=bowEmbed)


# Axe Enchantments
class SelectAxeEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Острота (V)",description="Несовместимо с бичом членистоногих, небесной карой."),
            discord.SelectOption(label="Небесная кара (V)",description="Несовместимо с бичом членистоногих, остротой."),
            discord.SelectOption(label="Бич членистоногих (V)",description="Несовместимо с остротой, небесной карой."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования топора", min_values=1, max_values=9, options=options)

    async def callback(self, interaction:discord.Interaction):
        global axeEnchants
        axeEnchants = self.values
        axeEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if axe == True:
            axeEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if pickaxe == True:
            axeEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if shovel == True:
            axeEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if hoe == True:
            axeEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if fishingRod == True:
            axeEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=axeEmbed)


# Pickaxe Enchantments
class SelectPickaxeEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования кирки", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
        global pickaxeEnchants
        pickaxeEnchants = self.values
        pickaxeEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if axe == True:
            pickaxeEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if pickaxe == True:
            pickaxeEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if shovel == True:
            pickaxeEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if hoe == True:
            pickaxeEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if fishingRod == True:
            pickaxeEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=pickaxeEmbed)


# Shovel Enchantments
class SelectShovelEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования лопаты", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
        global shovelEnchants
        shovelEnchants = self.values
        shovelEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if axe == True:
            shovelEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if pickaxe == True:
            shovelEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if shovel == True:
            shovelEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if hoe == True:
            shovelEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if fishingRod == True:
            shovelEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=shovelEmbed)


# Hoe Enchantments
class SelectHoeEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования мотыги", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
        global hoeEnchants
        hoeEnchants = self.values
        hoeEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if axe == True:
            hoeEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if pickaxe == True:
            hoeEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if shovel == True:
            hoeEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if hoe == True:
            hoeEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if fishingRod == True:
            hoeEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=hoeEmbed)
        

# FishingRod Enchantments
class SelectFishingRodEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Приманка(III)"),
            discord.SelectOption(label="Везучий рыбак (III)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования удочки", min_values=1, max_values=5, options=options)

    async def callback(self, interaction:discord.Interaction):
        global fishingRodEnchants
        fishingRodEnchants = self.values
        fishingRodEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if axe == True:
            fishingRodEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if pickaxe == True:
            fishingRodEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if shovel == True:
            fishingRodEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if hoe == True:
            fishingRodEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if fishingRod == True:
            fishingRodEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=fishingRodEmbed)


# Boots Enchantments
class SelectBootsEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Защита (IV)", description="Несовместимо с взрывоустойчивостью, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Взрывоустойчивость (IV)", description="Несовместимо с защитой, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Огнеупорность (IV)", description="Несовместимо с взрывоустойчивостью, защитой, защитой от снарядов."),
            discord.SelectOption(label="Защита от снарядов (IV)", description="Несовместимо с взрывоустойчивостью, защитой, огнеупорностью."),
            discord.SelectOption(label="Шипы (III)"),
            discord.SelectOption(label="Подводная ходьба (III)", description="Несовместимо с ледоходом."),
            discord.SelectOption(label="Невесомость (IV)"),
            discord.SelectOption(label="Ледоход (II)", description="Несовместимо с подводной ходьбой."),
            discord.SelectOption(label="Скорость души (III)"),
            discord.SelectOption(label="Проклятие несъёмности"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования ботинок", min_values=1, max_values=13, options=options)

    async def callback(self, interaction:discord.Interaction):
        global bootsEnchants
        bootsEnchants = self.values
        bootsEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if boots == True:
            bootsEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        if turtle == True:
            bootsEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if helmet == True:
            bootsEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if chestplate == True:
            bootsEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if leggings == True:
            bootsEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if boots == True:
            bootsEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=bootsEmbed)


# Turtle helmet Enchantments
class SelectTurtleEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Защита (IV)", description="Несовместимо с взрывоустойчивостью, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Взрывоустойчивость (IV)", description="Несовместимо с защитой, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Огнеупорность (IV)", description="Несовместимо с взрывоустойчивостью, защитой, защитой от снарядов."),
            discord.SelectOption(label="Защита от снарядов (IV)", description="Несовместимо с взрывоустойчивостью, защитой, огнеупорностью."),
            discord.SelectOption(label="Шипы (III)"),
            discord.SelectOption(label="Подводное дыхание (III)"),
            discord.SelectOption(label="Подводник"),
            discord.SelectOption(label="Проклятие несъёмности"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования черепашьего панциря", min_values=1, max_values=11, options=options)

    async def callback(self, interaction:discord.Interaction):
        global turtleEnchants
        turtleEnchants = self.values
        turtleEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if boots == True:
            turtleEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        if turtle == True:
            turtleEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if helmet == True:
            turtleEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if chestplate == True:
            turtleEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if leggings == True:
            turtleEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if boots == True:
            turtleEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=turtleEmbed)

# Helmet Enchantments
class SelectHelmetEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Защита (IV)", description="Несовместимо с взрывоустойчивостью, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Взрывоустойчивость (IV)", description="Несовместимо с защитой, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Огнеупорность (IV)", description="Несовместимо с взрывоустойчивостью, защитой, защитой от снарядов."),
            discord.SelectOption(label="Защита от снарядов (IV)", description="Несовместимо с взрывоустойчивостью, защитой, огнеупорностью."),
            discord.SelectOption(label="Шипы (III)"),
            discord.SelectOption(label="Подводное дыхание (III)"),
            discord.SelectOption(label="Подводник"),
            discord.SelectOption(label="Проклятие несъёмности"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования шлема", min_values=1, max_values=11, options=options)

    async def callback(self, interaction:discord.Interaction):
        global helmetEnchants
        helmetEnchants = self.values
        helmetEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if turtle == True:
            helmetEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if helmet == True:
            helmetEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if chestplate == True:
            helmetEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if leggings == True:
            helmetEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if boots == True:
            helmetEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=helmetEmbed)

# Chestplate Enchantments
class SelectChestplateEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Защита (IV)", description="Несовместимо с взрывоустойчивостью, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Взрывоустойчивость (IV)", description="Несовместимо с защитой, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Огнеупорность (IV)", description="Несовместимо с взрывоустойчивостью, защитой, защитой от снарядов."),
            discord.SelectOption(label="Защита от снарядов (IV)", description="Несовместимо с взрывоустойчивостью, защитой, огнеупорностью."),
            discord.SelectOption(label="Шипы (III)"),
            discord.SelectOption(label="Проклятие несъёмности"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования нагрудника", min_values=1, max_values=9, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chestplateEnchants
        chestplateEnchants = self.values
        chestplateEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if turtle == True:
            chestplateEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if helmet == True:
            chestplateEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if chestplate == True:
            chestplateEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if leggings == True:
            chestplateEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if boots == True:
            chestplateEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=chestplateEmbed)


# Leggings Enchantments
class SelectLeggingsEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Защита (IV)", description="Несовместимо с взрывоустойчивостью, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Взрывоустойчивость (IV)", description="Несовместимо с защитой, огнеупорностью, защитой от снарядов."),
            discord.SelectOption(label="Огнеупорность (IV)", description="Несовместимо с взрывоустойчивостью, защитой, защитой от снарядов."),
            discord.SelectOption(label="Защита от снарядов (IV)", description="Несовместимо с взрывоустойчивостью, защитой, огнеупорностью."),
            discord.SelectOption(label="Шипы (III)"),
            discord.SelectOption(label="Проворство (III)"),
            discord.SelectOption(label="Проклятие несъёмности"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования понож", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global leggingsEnchants
        leggingsEnchants = self.values
        leggingsEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if turtle == True:
            leggingsEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if helmet == True:
            leggingsEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if chestplate == True:
            leggingsEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if leggings == True:
            leggingsEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if boots == True:
            leggingsEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=leggingsEmbed)

# Flint and steel Enchantments
class SelectFlintNsteelEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования зажигалки", min_values=1, max_values=3, options=options)

    async def callback(self, interaction:discord.Interaction):
        global flintNsteelEnchants
        flintNsteelEnchants = self.values
        flintNsteelEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if flintNsteel == True:
            flintNsteelEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
        if shield == True:
            flintNsteelEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
        if scissors == True:
            flintNsteelEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=flintNsteelEmbed)

# Shield Enchantments
class SelectShieldEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования щита", min_values=1, max_values=3, options=options)

    async def callback(self, interaction:discord.Interaction):
        global shieldEnchants
        shieldEnchants = self.values
        shieldEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if flintNsteel == True:
            shieldEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
        if shield == True:
            shieldEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
        if scissors == True:
            shieldEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=shieldEmbed)

# Scissors Enchantments
class SelectScissorsEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования ножниц", min_values=1, max_values=3, options=options)

    async def callback(self, interaction:discord.Interaction):
        global scissorsEnchants
        scissorsEnchants = self.values
        scissorsEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if flintNsteel == True:
            scissorsEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
        if shield == True:
            scissorsEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
        if scissors == True:
            scissorsEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=scissorsEmbed)


# Buttons

# Main order menu
# When we press "Submit order" button, bot sends 2 messages with all information about order: First message is sent in the "channel_orders" to the client, second one is sent to the blacksmiths in the "channel_orerlist"
class OrderSubmit(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Подтвердить заказ", custom_id="orderSubmit")

    async def callback(self, interaction:discord.Interaction): 
        submitEmbed = discord.Embed(title="Ваш заказ составлен и отправлен кузнецам!", description="Cпасибо за вашу покупку! Когда ваш заказ будет готов, вам сообщат в личные сообщения.", color=discord.Colour.from_str('0x2366c4'))
        tinkerEmbed = discord.Embed(title="Новый заказ!", color=discord.Colour.from_str('0x2366c4'), description="Заказчик: "+interaction.user.mention)
        
        submitEmbed.add_field(name="Выбранные товары:", value=orderValues, inline=False)
        tinkerEmbed.add_field(name="Выбранные товары:", value=orderValues, inline=False)


        print(interaction.user.name+" made a new order!")

        # The bot sends only those embed fields that the client used
        if netherite == True:
            submitEmbed.add_field(name="Из незерита будут сделаны:", value=netheriteValues, inline=False)
            tinkerEmbed.add_field(name="Из незерита должны быть сделаны:", value=netheriteValues, inline=False)
            print("Netherite ones: "+netheriteValues.__str__())
        
        if trezub == True:
            submitEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            print("Trident enchantments: "+trezubEnchants.__str__())
        if sword == True:
            submitEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            print("Sword enchantments: "+swordEnchants.__str__())
        if crossbow == True:
            submitEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            print("Crossbow enchantments: "+crossbowEnchants.__str__())
        if bow == True:
            submitEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            print("Bow enchantments: "+bowEnchants.__str__())
        if axe == True:
            submitEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
            print("Axe enchantments: "+axeEnchants.__str__())
        if pickaxe == True:
            submitEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
            print("Pickaxe enchantments: "+pickaxeEnchants.__str__())
        if shovel == True:
            submitEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
            print("Shovel enchantments: "+shovelEnchants.__str__())
        if hoe == True:
            submitEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
            print("Hoe enchantments: "+hoeEnchants.__str__())
        if fishingRod == True:
            submitEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)
            print("Fishing rod enchantments: "+fishingRodEnchants.__str__())
        if turtle == True:
            submitEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
            print("Turtle helmet enchantments: "+turtleEnchants.__str__())
        if helmet == True:
            submitEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
            print("Helmet enchantments: "+helmetEnchants.__str__())
        if chestplate == True:
            submitEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
            print("Chestplate enchantments: "+chestplateEnchants.__str__())
        if leggings == True:
            submitEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
            print("Leggings enchantments: "+leggingsEnchants.__str__())
        if boots == True:
            submitEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
            print("Boots enchantments: "+bootsEnchants.__str__())
        if flintNsteel == True:
            submitEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
            print("Flint and steel enchantments: "+flintNsteelEnchants.__str__())
        if shield == True:
            submitEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
            print("Shield enchantments: "+shieldEnchants.__str__())
        if scissors == True:
            submitEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)
            print("Scissors enchantments: "+scissorsEnchants.__str__())

        if orderCommentSubmit == True:
            submitEmbed.add_field(name="Ваш комментарий к заказу:", value=orderCommentValue, inline=False)
            tinkerEmbed.add_field(name="Комментарий к заказу:", value=orderCommentValue, inline=False)
            print("Customer's comment: "+orderCommentValue.__str__())

        global orderIDname
        global orderIDnumber
        global valueNumber
        if valueNumber == len(orderIDnumber):
            valueNumber = 0
        orderIDname[valueNumber] = interaction.user
        

        await interaction.response.send_message(embed=submitEmbed, ephemeral=True)
        await channel_orderlist_tinker.send(embed=tinkerEmbed)
        message = await channel_orderlist_tinker.send(view=OrderTinkerView())

        # We also save the id of a message with which bot has responded and the user that made the order
        orderIDnumber[valueNumber] = message.id
        print("Orders data:")
        print(orderIDnumber)
        print(orderIDname)
        print("-------")

        valueNumber += 1
        
            
        global makingOrder
        makingOrder = False





# Button to choose netherite ones if they are are needed
# This interaction responses with a embed and select menu (line 219)
class OrderNetherite(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Выбрать незеритовые аналоги", custom_id="orderNetherite")

    async def callback(self, interaction:discord.Interaction): 
        embedNetherite = discord.Embed(title="Выберите товары, которые необходимо сделать из незерита!",color=discord.Colour.from_str('0x2366c4'))
        embedNetherite.add_field(name="Из незерита будут сделаны:",value="-",inline=False)  
        await interaction.response.send_message(embed=embedNetherite,view=OrderNetheriteView(), ephemeral=True)


# if someone wants to comment on his order
# this interaction responses with a modal where you can type your message
class OrderComment(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Добавить комментарий к заказу", custom_id="orderComment")

    async def callback(self, interaction:discord.Interaction): 
        await interaction.response.send_modal(orderCommentModal())


# Menu, where someone can choose enchantments for his items
# This interaction responses with a embed and select menus in which you can choose enchantments for items you have chosen in first select (orderSelect)
# The bot sends the enchantment select menus only for those items that the user has selected in first select (orderSelect)
class SelectEnchantments(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Выбрать зачарования", custom_id="orderEnchantments")

    async def callback(self, interaction:discord.Interaction): 
        embedEnchantments= discord.Embed(title="Выберите зачарования товаров",color=discord.Colour.from_str('0x2366c4')) 
        embedEnchantments.add_field(name="***Предупреждение!***",value="***Имейте в виду, что многие зачарования конфликтуют друг с другом.*** Если в списке выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование! Помните, что вы можете расписать необходимые зачарования более подробно с помощью комментария к заказу.",inline=False)
        
        
        if trezub == True or sword == True or crossbow == True or bow == True or axe == True or pickaxe == True or shovel == True or hoe == True or fishingRod == True or boots == True or turtle == True or helmet == True or chestplate == True or leggings == True or flintNsteel == True or shield == True or scissors == True:
            await interaction.response.send_message(embed=embedEnchantments, ephemeral=True)
        else:
            embedNone = discord.Embed(title="Вы не выбрали ни одного товара!",color=discord.Colour.from_str('0x2366c4'))
            await interaction.response.send_message(embed=embedNone, ephemeral=True)

        # discord limits the amount of selects we can put in one view, so i had to make 4 different views and send them with 4 messages 
        # (I also divided items on weaponry, tools, armour and other)

        if trezub == True or sword == True or crossbow == True or bow == True:
            await interaction.followup.send(view=OrderEnchantmentsView1(), ephemeral=True)

        if axe == True or pickaxe == True or shovel == True or hoe == True or fishingRod == True:
            await interaction.followup.send(view=OrderEnchantmentsView2(), ephemeral=True)

        if boots == True or turtle == True or helmet == True or chestplate == True or leggings == True:
            await interaction.followup.send(view=OrderEnchantmentsView3(), ephemeral=True)

        if flintNsteel == True or shield == True or scissors == True:
            await interaction.followup.send(view=OrderEnchantmentsView4(), ephemeral=True)


# Button for blacksmiths, to accept the order
class AcceptOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Принять заказ", custom_id="AcceptOrder")

    async def callback(self, interaction:discord.Interaction): 
        embedAccept = discord.Embed(description="Заказ принял: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))

        await interaction.response.defer()
        n = 0
        getID = await interaction.original_response()
        
        getID_2 = getID.__str__()
        getID_3 = int(getID_2[23:42])
        
        while n < len(orderIDnumber):
            if getID_3 == orderIDnumber[n]:
                await orderIDname[n].send(embed=discord.Embed(title="Ваш заказ принят!",description="Кузнец: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4')))
                print("Order id:"+orderIDnumber[n].__str__()+" accepted")
                print("Customer: "+orderIDname[n].name)
                print("-------")
                
            n += 1
        
        await interaction.edit_original_response(embed=embedAccept,view=OrderTinkerViewAccepted())


# Button for blacksmiths, to reject the order
class RejectOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Отклонить заказ", custom_id="RejectOrder")

    async def callback(self, interaction:discord.Interaction): 
       await interaction.response.send_modal(orderRejectModal())

# Button for blacksmiths, to tell customer that his order is ready
class ReadyOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Заказ готов", custom_id="ReadyOrder")

    async def callback(self, interaction:discord.Interaction): 
        embedReady = discord.Embed(description="Заказ выполнил: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))
        await interaction.response.defer()
        n = 0
        getID = await interaction.original_response()
        
        getID_2 = getID.__str__()
        getID_3 = int(getID_2[23:42])
        
        while n < len(orderIDnumber):
            if getID_3 == orderIDnumber[n]:
                await orderIDname[n].send(embed=discord.Embed(title="Ваш заказ готов!", color=discord.Colour.from_str('0x2366c4')))
                print("Order id:"+orderIDnumber[n].__str__()+" ready")
                print("Customer: "+orderIDname[n].name)
                print("-------")
                
            n += 1
        await interaction.edit_original_response(embed=embedReady,view=None)






# Modals

# if someone wants to comment on his order, bot should show this modal  
class orderCommentModal(discord.ui.Modal, title="Добавьте комментарий к заказу!"):
    comment = discord.ui.TextInput(
        label="Опишите все необходимые подробности заказа.",
        style=discord.TextStyle.long
    )
    async def on_submit(self, interaction: discord.Interaction):
        global orderCommentValue
        global orderCommentSubmit
        orderCommentValue = self.comment
        orderCommentSubmit = True

        embedComment = discord.Embed(title="Ваш комментарий", color=discord.Colour.from_str('0x2366c4'), description=self.comment)
        await interaction.response.send_message(embed=embedComment,ephemeral=True)
    
    #I sometimes get errors with modals, so i have to put some error handeling here
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)


        traceback.print_exception(type(error), error, error.__traceback__)


# if blacksmith wants to reject the order, bot should show this modal and blacksmith must write the reason 
class orderRejectModal(discord.ui.Modal, title="Опиши причину отказа!"):
    comment = discord.ui.TextInput(
        label="Опиши причину отклонения, её увидит заказчик.",
        style=discord.TextStyle.long
    )
    async def on_submit(self, interaction: discord.Interaction):
        global orderRejectValue
        orderRejectValue = self.comment
        await interaction.response.defer()
        embedReject = discord.Embed(title="Заказ отклонён!",description="Заказ отклонил: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))
        embedReject.add_field(name="Причина:",value=orderRejectValue)

        getID = await interaction.original_response()
        
        getID_2 = getID.__str__()
        getID_3 = int(getID_2[23:42])
        n = 0
        while n < len(orderIDnumber):
            if getID_3 == orderIDnumber[n]:
                await orderIDname[n].send(embed=embedReject)
                print("Order id:"+orderIDnumber[n].__str__()+" rejected")
                print("Customer: "+orderIDname[n].name)
                print("-------")
                
            n += 1

        
        await interaction.edit_original_response(embed=embedReject,view=OrderTinkerViewRejected())
    
    #I sometimes get errors with modals, so i have to put some error handeling here
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)


        traceback.print_exception(type(error), error, error.__traceback__)






#views
#starting order
class OrderButtonView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(StartOrder())


#main order menu
class OrderView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(OrderSelect())
        self.add_item(SelectEnchantments())
        self.add_item(OrderNetherite())
        self.add_item(OrderComment())
        self.add_item(OrderSubmit())
        
# if netherite ones are needed
class OrderNetheriteView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(OrderSelectNetherite())

# if someone wants to comment on his order
class OrderCommentView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(OrderComment())

# menu, where someone can choose enchantments for his items
# discord limits the amount of selects we can put in one view, so i had to make 4 different views and send them with 4 messages 
# (I also divided items on weaponry, tools, armour and other)
class OrderEnchantmentsView1(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if trezub == True:
            self.add_item(SelectTrezubEnchantments())
        if sword == True:
            self.add_item(SelectSwordEnchantments())
        if crossbow == True:
            self.add_item(SelectCrossbowEnchantments())
        if bow == True:
            self.add_item(SelectBowEnchantments())
        

class OrderEnchantmentsView2(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if axe == True:
            self.add_item(SelectAxeEnchantments())
        if pickaxe == True:
            self.add_item(SelectPickaxeEnchantments())
        if shovel == True:
            self.add_item(SelectShovelEnchantments())
        if hoe == True:
            self.add_item(SelectHoeEnchantments())
        if fishingRod == True:
            self.add_item(SelectFishingRodEnchantments())
        

class OrderEnchantmentsView3(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if turtle == True:
            self.add_item(SelectTurtleEnchantments())
        if helmet == True:
            self.add_item(SelectHelmetEnchantments())
        if chestplate == True:
            self.add_item(SelectChestplateEnchantments())
        if leggings == True:
            self.add_item(SelectLeggingsEnchantments())
        if boots == True:
            self.add_item(SelectBootsEnchantments())

class OrderEnchantmentsView4(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if flintNsteel == True:
            self.add_item(SelectFlintNsteelEnchantments())
        if shield == True:
            self.add_item(SelectShieldEnchantments())
        if scissors == True:
            self.add_item(SelectScissorsEnchantments())


# view with 2 buttons for blacksmith (accept order or reject order)
class OrderTinkerView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(AcceptOrder())
        self.add_item(RejectOrder())   


# another view with 2 buttons for blacksmith (tell customer that his order is ready or reject order)
class OrderTinkerViewAccepted(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(ReadyOrder())
        self.add_item(RejectOrder())    


# another view with "accept order" button for blacksmith (if the order is rejected earlier)
class OrderTinkerViewRejected(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(AcceptOrder())
        


client.run("TOKEN")
