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
# The bot keeps in his memory up to 10 orders, next ones overwrite the previous ones.
# The bot doesn't allow two players to make orders at the same time
# When order is sent to blacksmiths, they can accept the order or reject the order
# Blacksmith must submit the basic cost of the order using special button, bot calculate the real cost using special discount system
# This cost is added to customer's points. Bot saves usernames and points of all customers in special file (customers.txt)   
# If blacksmiths accept the order, they can reject the order if they face some troubles with it or change the cost of the order or, when order is ready, they can tell customer that his order is ready
# User gets messages from the bot in DM about his order


import traceback
from discord import app_commands
from discord.utils import get
import discord
from threading import Timer
     
# Guild in discord API means discord server
MY_GUILD = discord.Object(id=your_guild_id)

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        intents.guilds = True
        intents.members = True
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
    #These two lines are the values those admin must put in his command and their descriptions
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
# We have to use user and member simultaneously because to get information about user we must use discord.User and to apply roles to user we must use discord.Member
orderIDname = [discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User,discord.User]
orderIDmember = [discord.Member,discord.Member,discord.Member,discord.Member,discord.Member,discord.Member,discord.Member,discord.Member,discord.Member,discord.Member]
orderIDnumber = [0,0,0,0,0,0,0,0,0,0]

orderIDcost = [0,0,0,0,0,0,0,0,0,0]
orderIDpoints = [0,0,0,0,0,0,0,0,0,0]


# After each order we have to clear values of all variables and lists used in making order
# I understand that my code sometimes looks very goofy, but I don't understand how to make some things better
def clearValues():
    global orderCommentSubmit
    global netherite

    global orderValues
    global netheriteValues

    global enchants

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
def timeout():
    global makingOrder
    makingOrder = False
    clearValues()
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
        # If someone is making order (makingOrder = True) it responds with a "The bot is currently being used, please try again later!" message
        if makingOrder == False:
            await interaction.response.send_message(embed=embed1,view=view,ephemeral=True)
            clearValues()
            
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

        # This list contains data about which items are selected by the user.
        global enchants
        enchants = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]
        
        i=0
        print("Items chosen by "+ interaction.user.name +":")
        while i < len(self.values):
            print(self.values[i])
            if self.values[i] == "Трезубец":
                enchants[0] = True
            if self.values[i] == "Меч":
                enchants[1]  = True
            if self.values[i] == "Арбалет":
                enchants[2]  = True
            if self.values[i] == "Лук":
                enchants[3]  = True
            if self.values[i] == "Топор":
                enchants[4]  = True
            if self.values[i] == "Кирка":
                enchants[5]  = True
            if self.values[i] == "Лопата":
                enchants[6]  = True
            if self.values[i] == "Мотыга":
                enchants[7]  = True
            if self.values[i] == "Удочка":
                enchants[8]  = True
            if self.values[i] == "Черепаший панцирь":
                enchants[9]  = True
            if self.values[i] == "Шлем":
                enchants[10]  = True
            if self.values[i] == "Нагрудник":
                enchants[11]  = True
            if self.values[i] == "Поножи":
                enchants[12]  = True
            if self.values[i] == "Ботинки":
                enchants[13]  = True
            if self.values[i] == "Зажигалка":
                enchants[14]  = True
            if self.values[i] == "Щит":
                enchants[15]  = True
            if self.values[i] == "Ножницы":
                enchants[16]  = True

            i += 1
        print("-------")


# Selection menu where users can choose what items should be done with netherite
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

        print("Netherite ones chosen by "+ interaction.user.name +":")
        print(netheriteValues)
        print("-------")

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
            if enchants[0] == True:
                trezubEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            if enchants[1]  == True:
                trezubEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            if enchants[2]  == True:
                trezubEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            if enchants[3]  == True:
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
            if enchants[0] == True:
                swordEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            if enchants[1]  == True:
                swordEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            if enchants[2]  == True:
                swordEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            if enchants[3]  == True:
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
            if enchants[0] == True:
                crossbowEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            if enchants[1]  == True:
                crossbowEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            if enchants[2]  == True:
                crossbowEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            if enchants[3]  == True:
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
        if enchants[0] == True:
            bowEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
        if enchants[1]  == True:
            bowEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
        if enchants[2]  == True:
            bowEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
        if enchants[3]  == True:
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

        if enchants[4]  == True:
            axeEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if enchants[5]  == True:
            axeEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if enchants[6]  == True:
            axeEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if enchants[7]  == True:
            axeEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if enchants[8]  == True:
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

        if enchants[4]  == True:
            pickaxeEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if enchants[5]  == True:
            pickaxeEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if enchants[6]  == True:
            pickaxeEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if enchants[7]  == True:
            pickaxeEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if enchants[8]  == True:
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

        if enchants[4]  == True:
            shovelEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if enchants[5]  == True:
            shovelEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if enchants[6]  == True:
            shovelEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if enchants[7]  == True:
            shovelEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if enchants[8]  == True:
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

        if enchants[4]  == True:
            hoeEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if enchants[5]  == True:
            hoeEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if enchants[6]  == True:
            hoeEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if enchants[7]  == True:
            hoeEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if enchants[8]  == True:
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

        if enchants[4]  == True:
            fishingRodEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
        if enchants[5]  == True:
            fishingRodEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
        if enchants[6]  == True:
            fishingRodEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
        if enchants[7]  == True:
            fishingRodEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
        if enchants[8]  == True:
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

        if enchants[13]  == True:
            bootsEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        if enchants[9]  == True:
            bootsEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if enchants[10]  == True:
            bootsEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if enchants[11]  == True:
            bootsEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if enchants[12]  == True:
            bootsEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if enchants[13]  == True:
            bootsEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=bootsEmbed)

# Turtle Enchantments
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

        if enchants[13]  == True:
            turtleEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
        if enchants[9]  == True:
            turtleEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if enchants[10]  == True:
            turtleEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if enchants[11]  == True:
            turtleEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if enchants[12]  == True:
            turtleEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if enchants[13]  == True:
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

        if enchants[9]  == True:
            helmetEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if enchants[10]  == True:
            helmetEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if enchants[11]  == True:
            helmetEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if enchants[12]  == True:
            helmetEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if enchants[13]  == True:
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

        if enchants[9]  == True:
            chestplateEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if enchants[10]  == True:
            chestplateEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if enchants[11]  == True:
            chestplateEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if enchants[12]  == True:
            chestplateEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if enchants[13]  == True:
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

        if enchants[9]  == True:
            leggingsEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
        if enchants[10]  == True:
            leggingsEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
        if enchants[11]  == True:
            leggingsEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
        if enchants[12]  == True:
            leggingsEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
        if enchants[13]  == True:
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

        if enchants[14]  == True:
            flintNsteelEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
        if enchants[15]  == True:
            flintNsteelEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
        if enchants[16]  == True:
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

        if enchants[14]  == True:
            shieldEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
        if enchants[15]  == True:
            shieldEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
        if enchants[16]  == True:
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

        if enchants[14]  == True:
            scissorsEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
        if enchants[15]  == True:
            scissorsEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
        if enchants[16]  == True:
            scissorsEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=scissorsEmbed)

# Buttons

# Main order menu
# When we press "Submit order" button, bot sends 2 messages with all information about order: First message is sent in the "channel_orders" to the client, 
# second one is sent to the blacksmiths in the "channel_orerlist".
# Bot also saves id of response message and the user, that made the order in 2 lists (orderIDnumber and orderIDname).
# These two we will use to match user and his order later
class OrderSubmit(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Подтвердить заказ", custom_id="orderSubmit")

    async def callback(self, interaction:discord.Interaction): 

        customerRole = get(interaction.user.guild.roles, name="Покупатель")
        await interaction.user.add_roles(customerRole)

        #Some discount roles we will use later (lines 1339-1351)
        global DiscountRole_1
        global DiscountRole_2
        global DiscountRole_3
        global DiscountRole_4
        global DiscountRole_5
        DiscountRole_1 = get(interaction.user.guild.roles, name="Проходимец")
        DiscountRole_2 = get(interaction.user.guild.roles, name="Частый гость")
        DiscountRole_3 = get(interaction.user.guild.roles, name="Местный")
        DiscountRole_4 = get(interaction.user.guild.roles, name="Родное личико")
        DiscountRole_5 = get(interaction.user.guild.roles, name="В доску свой")


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
        
        if enchants[0] == True:
            submitEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования трезубца:", value=trezubEnchants, inline=False)
            print("Trident enchantments: "+trezubEnchants.__str__())
        if enchants[1]  == True:
            submitEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования меча:", value=swordEnchants, inline=False)
            print("Sword enchantments: "+swordEnchants.__str__())
        if enchants[2]  == True:
            submitEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования арбалета:", value=crossbowEnchants, inline=False)
            print("Crossbow enchantments: "+crossbowEnchants.__str__())
        if enchants[3]  == True:
            submitEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования лука:", value=bowEnchants, inline=False)
            print("Bow enchantments: "+bowEnchants.__str__())
        if enchants[4]  == True:
            submitEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования топора:", value=axeEnchants, inline=False)
            print("Axe enchantments: "+axeEnchants.__str__())
        if enchants[5]  == True:
            submitEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования кирки:", value=pickaxeEnchants, inline=False)
            print("Pickaxe enchantments: "+pickaxeEnchants.__str__())
        if enchants[6]  == True:
            submitEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования лопаты:", value=shovelEnchants, inline=False)
            print("Shovel enchantments: "+shovelEnchants.__str__())
        if enchants[7]  == True:
            submitEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования мотыги:", value=hoeEnchants, inline=False)
            print("Hoe enchantments: "+hoeEnchants.__str__())
        if enchants[8]  == True:
            submitEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования удочки:", value=fishingRodEnchants, inline=False)
            print("Fishing rod enchantments: "+fishingRodEnchants.__str__())
        if enchants[9]  == True:
            submitEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования черепашьего панциря:", value=turtleEnchants, inline=False)
            print("Turtle enchants[10]  enchantments: "+turtleEnchants.__str__())
        if enchants[10]  == True:
            submitEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования шлема:", value=helmetEnchants, inline=False)
            print("Helmet enchantments: "+helmetEnchants.__str__())
        if enchants[11]  == True:
            submitEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования нагрудника:", value=chestplateEnchants, inline=False)
            print("Chestplate enchantments: "+chestplateEnchants.__str__())
        if enchants[12]  == True:
            submitEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования понож:", value=leggingsEnchants, inline=False)
            print("Leggings enchantments: "+leggingsEnchants.__str__())
        if enchants[13]  == True:
            submitEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования ботинок:", value=bootsEnchants, inline=False)
            print("Boots enchantments: "+bootsEnchants.__str__())
        if enchants[14]  == True:
            submitEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования зажигалки:", value=flintNsteelEnchants, inline=False)
            print("Flint and steel enchantments: "+flintNsteelEnchants.__str__())
        if enchants[15]  == True:
            submitEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования щита:", value=shieldEnchants, inline=False)
            print("Shield enchantments: "+shieldEnchants.__str__())
        if enchants[16]  == True:
            submitEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)
            tinkerEmbed.add_field(name="Зачарования ножниц:", value=scissorsEnchants, inline=False)
            print("Scissors enchantments: "+scissorsEnchants.__str__())

        if orderCommentSubmit == True:
            submitEmbed.add_field(name="Ваш комментарий к заказу:", value=orderCommentValue, inline=False)
            tinkerEmbed.add_field(name="Комментарий к заказу:", value=orderCommentValue, inline=False)
            print("Customer's comment: "+orderCommentValue.__str__())
        global orderIDname
        global orderIDnumber
        global orderIDmember
        global valueNumber

        if valueNumber == len(orderIDnumber):
            valueNumber = 0

        orderIDname[valueNumber] = interaction.user
        orderIDmember[valueNumber] = interaction.guild.get_member_named("Nikitza")

        await interaction.response.send_message(embed=submitEmbed, ephemeral=True)
        await channel_orderlist_tinker.send(embed=tinkerEmbed)
        message = await channel_orderlist_tinker.send(view=OrderTinkerView())

        # We also save the id of a message with which bot has responded and the user that made the order
        orderIDnumber[valueNumber] = message.id
        print("-------")
        print("Last orders data:")
        print("Orders ID: "+orderIDnumber.__str__())
        print(" ")
        print("Orders users: "+orderIDname.__str__())
        print(" ")
        print("Orders members: "+orderIDmember.__str__())
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
# this interaction responses with a modal where you can type your message (line 1204)
class OrderComment(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.gray, label="Добавить комментарий к заказу", custom_id="orderComment")

    async def callback(self, interaction:discord.Interaction): 
        await interaction.response.send_modal(orderCommentModal())


# Menu, where someone can choose enchantments for his items
# This interaction responses with a embed and select menus in which you can choose enchantments for items you have chosen in first select (orderSelect)
# The bot sends the enchantment select menus only for those items that the user has selected in first select (orderSelect) (lines 407 - 934)
class SelectEnchantments(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Выбрать зачарования", custom_id="orderEnchantments")

    async def callback(self, interaction:discord.Interaction): 
        embedEnchantments= discord.Embed(title="Выберите зачарования товаров",color=discord.Colour.from_str('0x2366c4')) 
        embedEnchantments.add_field(name="***Предупреждение!***",value="***Имейте в виду, что многие зачарования конфликтуют друг с другом.*** Если в списке выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование! Помните, что вы можете расписать необходимые зачарования более подробно с помощью комментария к заказу.",inline=False)
        
        
        if enchants[0] == True or enchants[1]  == True or enchants[2]  == True or enchants[3]  == True or enchants[4]  == True or enchants[5]  == True or enchants[6]  == True or enchants[7]  == True or enchants[8]  == True or enchants[13]  == True or enchants[9]  == True or enchants[10]  == True or enchants[11]  == True or enchants[12]  == True or enchants[14]  == True or enchants[15]  == True or enchants[16]  == True:
            await interaction.response.send_message(embed=embedEnchantments, ephemeral=True)
        else:
            embedNone = discord.Embed(title="Вы не выбрали ни одного товара!",color=discord.Colour.from_str('0x2366c4'))
            await interaction.response.send_message(embed=embedNone, ephemeral=True)

        # discord limits the amount of selects we can put in one view, so i had to make 4 different views and send them with 4 messages 
        # (I also divided items on weaponry, tools, armour and other)

        if enchants[0] == True or enchants[1]  == True or enchants[2]  == True or enchants[3]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView1(), ephemeral=True)

        if enchants[4]  == True or enchants[5]  == True or enchants[6]  == True or enchants[7]  == True or enchants[8]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView2(), ephemeral=True)

        if enchants[13]  == True or enchants[9]  == True or enchants[10]  == True or enchants[11]  == True or enchants[12]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView3(), ephemeral=True)

        if enchants[14]  == True or enchants[15]  == True or enchants[16]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView4(), ephemeral=True)


# Button for blacksmiths, to accept the order
class AcceptOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Принять заказ", custom_id="AcceptOrder")

    async def callback(self, interaction:discord.Interaction): 
        embedAccept = discord.Embed(title="Заказ принят",description="Заказ принял: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))

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
# It responses with a modal, where blacksmith types a reason
class RejectOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Отклонить заказ", custom_id="RejectOrder")

    async def callback(self, interaction:discord.Interaction): 
       await interaction.response.send_modal(orderRejectModal())

# Button for blacksmiths, to set the cost of an order
class OrderCost(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Стоимость заказа", custom_id="OrderCost")

    async def callback(self, interaction:discord.Interaction): 
       await interaction.response.send_modal(GetCostModal())

# Button for blacksmiths, to tell customer that his order is ready
class ReadyOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Заказ готов", custom_id="ReadyOrder")

    async def callback(self, interaction:discord.Interaction): 
        embedReady = discord.Embed(title="Заказ выполнен",description="Заказ выполнил: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))
        await interaction.response.defer()
        n = 0
        getID = await interaction.original_response()
        
        getID_2 = getID.__str__()
        getID_3 = int(getID_2[23:42])
        
        # Here bot gets the cost of the order and current discount points it must apply to customer 
        while n < len(orderIDnumber):
            if getID_3 == orderIDnumber[n]:
                with open('customers.txt','r+') as customerlistReady:
                    CostContentReady = customerlistReady.readlines()
                    print(CostContentReady)
                    k = 0
                    while k < len(CostContentReady):
                        CostContentLineReady = CostContentReady[k]
                        CostContentValueReady = CostContentLineReady.split()

                        if CostContentValueReady[0] == orderIDname[n].name:
                            CostContentReady[k] = orderIDname[n].name+" "+orderIDpoints[n].__str__()+"\n"
                        k += 1

                    print(CostContentReady)
                    customerlistReady.seek(0)
                    customerlistReady.writelines(CostContentReady)

                await orderIDname[n].send(embed=discord.Embed(title="Ваш заказ готов!", color=discord.Colour.from_str('0x2366c4')))
                print("Order id:"+orderIDnumber[n].__str__()+" ready")
                print("Customer: "+orderIDname[n].name)
                print("-------")
                embedReady.add_field(name="Cтоимость:",value=orderIDcost[n].__str__()+" AP")
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

# When order is ready, blacksmith should tell the bot the cost of the order 
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

# Here is a modal, where blacksmith types cost of the order without any discounts

# Then the bot calculate the cost with needed discount, to figure which discount it should use, bot compares 'points1' value with min and max amounts of points for each discount
# I understand that using a lot of "if" statements is bad, but I can't find a way to make it better, sorry
class GetCostModal(discord.ui.Modal, title="Введите стоимость заказа"):
    comment = discord.ui.TextInput(
        label="Стоимость заказа без учёта скидки.",
        style=discord.TextStyle.short
    )
    async def on_submit(self, interaction: discord.Interaction):
        

        global orderCost
        orderCost = int(self.comment.__str__())
        global orderCost_withDiscount
        orderCost_withDiscount = orderCost

        await interaction.response.defer()
        
        getID = await interaction.original_response()
        
        getID_2 = getID.__str__()
        getID_3 = int(getID_2[23:42])

        n = 0
        while n < len(orderIDnumber):
            if getID_3 == orderIDnumber[n]:
                CostUserName = orderIDname[n]
                CostUserMember = orderIDmember[n]
                

            n += 1

        # The bot opens "customers.txt" file, where it gets a list with usersnames of customers and their points
        with open('customers.txt','r+') as customerlist:
            CostContent = customerlist.readlines()
            print(CostContent)
            foundUser = False
            k = 0
            while k < len(CostContent): 
                # After that, the bot splits this list into required elements:
                # CostContent ['name1 points1','name2 points2'] --> CostContentLine = "name1 points1" --> CostContentValue ['name1','points1']
                CostContentLine = CostContent[k]
                CostContentValue = CostContentLine.split()
                # After that, bot compares 'name1' value with names from OrderIDname list
                if CostContentValue[0] == CostUserName.name:
                    foundUser = True
                    # If it finds this user, bot check how much discount points user has
                    if int(CostContentValue[1]) >= 5:
                        if int(CostContentValue[1]) >= 150 and int(CostContentValue[1]) < 200:
                            orderCost_withDiscount = round(0.95*orderCost)
                        elif int(CostContentValue[1]) >= 200 and int(CostContentValue[1]) < 300:
                            orderCost_withDiscount = round(0.9*orderCost)
                        elif int(CostContentValue[1]) >= 300 and int(CostContentValue[1]) < 450:
                            orderCost_withDiscount = round(0.85*orderCost)
                        elif int(CostContentValue[1]) >= 450 and int(CostContentValue[1]) < 600:
                            orderCost_withDiscount = round(0.75*orderCost)
                        elif int(CostContentValue[1]) >= 600:
                            orderCost_withDiscount = round(0.7*orderCost)
                        else:
                            orderCost_withDiscount = orderCost
                k += 1

            # If user made the order his first time (he wasn't found in customers.txt file), bot should apply this user and his points to file 
            if foundUser == False:
                CostContent.append(CostUserName.name+" 0\n")
                print(CostContent)
                customerlist.seek(0)
                customerlist.writelines(CostContent)
                customerPoints = 0
                setCustomerPoints = 0
                orderCost_withDiscount = orderCost
            else:
                setCustomerPoints = int(CostContentValue[1])
                customerPoints = int(CostContentValue[1])

        setCustomerPoints += orderCost_withDiscount

        embedCost = discord.Embed(title="Заказ принят",description="Заказ принял: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))
        embedCost.add_field(name="Стоимость без учёта скидки:", value=orderCost.__str__()+ " AP")
        embedCost.add_field(name="Стоимость c учётом скидки:",value=orderCost_withDiscount.__str__()+" AP")

        # Here bot adds special discount roles to a user if he reached specific amount of points 
        if customerPoints < 150 and setCustomerPoints >= 150 and setCustomerPoints < 200:
            await CostUserMember.add_roles(DiscountRole_1)
            embedCost.add_field(name=CostUserName.name+" получает роль "+DiscountRole_1.name,value="Всего "+CostUserName.name+" потратил в кузне "+ setCustomerPoints.__str__()+" AP.",inline=False)
        elif customerPoints < 200 and setCustomerPoints >= 200 and setCustomerPoints < 300:
            await CostUserMember.add_roles(DiscountRole_2)
            embedCost.add_field(name=CostUserName.name+" получает роль "+DiscountRole_2.name,value="Всего "+CostUserName.name+" потратил в кузне "+ setCustomerPoints.__str__()+" AP.",inline=False)
        elif customerPoints < 300 and setCustomerPoints >= 300 and setCustomerPoints < 450:
            await CostUserMember.add_roles(DiscountRole_3)
            embedCost.add_field(name=CostUserName.name+" получает роль "+DiscountRole_3.name,value="Всего "+CostUserName.name+" потратил в кузне "+ setCustomerPoints.__str__()+" AP.",inline=False)
        elif customerPoints < 450 and setCustomerPoints >= 450 and setCustomerPoints < 600:
            await CostUserMember.add_roles(DiscountRole_4)
            embedCost.add_field(name=CostUserName.name+" получает роль "+DiscountRole_4.name,value="Всего "+CostUserName.name+" потратил в кузне "+ setCustomerPoints.__str__()+" AP.",inline=False)
        elif customerPoints < 600 and setCustomerPoints >= 600:
            await CostUserMember.add_roles(DiscountRole_5)
            embedCost.add_field(name=CostUserName.name+" получает роль "+DiscountRole_5.name,value="Всего "+CostUserName.name+" потратил в кузне "+ setCustomerPoints.__str__()+" AP.",inline=False)

        global orderIDcost
        global orderIDpoints

        n = 0
        # Bot saves current cost and point of user to use it in ReadyOrder class (line 1148)
        while n < len(orderIDnumber):
            if getID_3 == orderIDnumber[n]:
                orderIDcost[n] = orderCost_withDiscount
                orderIDpoints[n] = setCustomerPoints
                
            n += 1
        print("Customers' data:")
        print("Last orders' cost: "+orderIDcost.__str__())
        print("Last customers' points: "+orderIDpoints.__str__())
        print("-------")
  
        await interaction.edit_original_response(embed=embedCost)
        await CostUserName.send(embed=discord.Embed(title="Стоимость вашего заказа с учётом скидки: " +orderCost_withDiscount.__str__()+ " АР.", color=discord.Colour.from_str('0x2366c4')))






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
        if enchants[0] == True:
            self.add_item(SelectTrezubEnchantments())
        if enchants[1]  == True:
            self.add_item(SelectSwordEnchantments())
        if enchants[2]  == True:
            self.add_item(SelectCrossbowEnchantments())
        if enchants[3]  == True:
            self.add_item(SelectBowEnchantments())
        
class OrderEnchantmentsView2(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if enchants[4]  == True:
            self.add_item(SelectAxeEnchantments())
        if enchants[5]  == True:
            self.add_item(SelectPickaxeEnchantments())
        if enchants[6]  == True:
            self.add_item(SelectShovelEnchantments())
        if enchants[7]  == True:
            self.add_item(SelectHoeEnchantments())
        if enchants[8]  == True:
            self.add_item(SelectFishingRodEnchantments())
        
class OrderEnchantmentsView3(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if enchants[9]  == True:
            self.add_item(SelectTurtleEnchantments())
        if enchants[10]  == True:
            self.add_item(SelectHelmetEnchantments())
        if enchants[11]  == True:
            self.add_item(SelectChestplateEnchantments())
        if enchants[12]  == True:
            self.add_item(SelectLeggingsEnchantments())
        if enchants[13]  == True:
            self.add_item(SelectBootsEnchantments())

class OrderEnchantmentsView4(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if enchants[14]  == True:
            self.add_item(SelectFlintNsteelEnchantments())
        if enchants[15]  == True:
            self.add_item(SelectShieldEnchantments())
        if enchants[16]  == True:
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
        self.add_item(OrderCost())
        self.add_item(RejectOrder())    

# another view with "accept order" button for blacksmith (if the order is rejected earlier)
class OrderTinkerViewRejected(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(AcceptOrder())
        


client.run("TOKEN")
