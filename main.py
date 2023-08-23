# Here is a small discord bot i've made for my friend's server
# The bot helps users to make an order in my friends's forge
# Sorry for the poor translation in some places, English is not my native language and I can sometimes make mistakes
# I wouldn't have been able to make this bot without the help of github of Martine discord bot, great thanks to https://github.com/MartineBot and PredaaA
# Feel free to copy my code and use it for your projects! 

# How the bot works:
# When the bot enters the server, the admin must set the channel where users can leave orders (channel_orders) and the channel where blacksmiths can see these orders (channel_orderlist)
# The admin should send special slash command /setupbot (/setup command is also shown in bot's command list, I don't understand why this command is there, I didn't ever made it ಠ_ಠ)
# Bot works even after restarts, saving information about channels it works with and 10 last orders
# ---------
# When someone wants to order something, bot send him a ephemeral message with some information and select menu (discord.ui.Select) where user can choose items he wants to buy
# Bot also sends some buttons (discord.ui.Button):
# 1 - "SelectEnchantments" which let user choose what enchantments he wants to be applied to his items
#   This button responses with different selection menus, each one for the item user has selected in the first selection menu
# 2 - "OrderNetherite" which let user choose what items he wants to be made of netherite
#   This button responses with a selection menu with options corresponding to the options selected by user in the first selection menu
# 3 - "OrderTrims" which let user choose decoration trims for his armour
#   This button responses with different selection menus, each one for the item user has selected in the first selection menu
# 3 - "OrderComment" which let user add a comment to his order
# 4 - "OrderSubmit" which let user save his order and send it to the blacksmiths
#   This button responses with a modal (https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=modals#modal)
# ---------
# Bot saves all orders in special file "setuporderinformation.txt". Each order is saved in format: <Customer ID> <ID of order message in channel_orderlist> <ID of order message with buttons in channel_orderlist> <Status of the order> 
# Statuses of the order:
# 0 - Order submitted
# 1 - Order accepted
# 2 - The cost of the order was set
# 3 - Order ready
# 4 - Order rejected
# When order is sent to blacksmiths, they can accept the order or reject the order with buttons (Bot apply statuses according to the condition of the order)
# Blacksmith must submit the basic cost of the order using special button, bot calculate the real cost using special discount system
# This cost is added to customer's points. Bot saves usernames and points of all customers in special file (customers.txt)   
# If blacksmiths accept the order, they can reject the order if they face some troubles with it, or change the cost of the order, or, when order is ready, they can tell customer that his order is ready
# User gets messages from the bot in DM about his order
# ---------
# The bot keeps in his memory up to 10 orders, next ones overwrite the previous ones.
# The bot doesn't allow two players to make orders at the same time.
# The bot doesn't allow blacklisted players to make orders.
# The bot doesnt allow to make empty orders.
# Blacksmiths can get all blacklisted users or add users to blacklist by their IDs or names
# They also can delete user's ID from blacklist
# The bot responds to the slash command "Help" with different embeds with information for users and blacksmiths.
# If you don't understand some parts of my code or how smth works, feel free to contact me: nikitzacompany@gmail.com or Nikitza#1663 on Discord



import traceback
from discord import app_commands
from discord.utils import get
import discord
from threading import Timer
    
# Guild in discord API means discord server
MY_GUILD = discord.Object(id=your_guild_id)
activity = discord.Activity(type=discord.ActivityType.watching, name="в #заказы")       

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents.all()):
        
        super().__init__(intents=intents, activity=activity)
        self.tree = app_commands.CommandTree(self)
        

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.all()
client = MyClient(intents=intents)

orderIDcost = [0,0,0,0,0,0,0,0,0,0]         # This list contains cost of 10 last orders (We use it to match customer and cost of his order)
orderIDnumber = [0,0,0,0,0,0,0,0,0,0]       # This list contains IDs of 10 last order messages in channel_orderlist (We use it to match customers and their orders)

@client.event
async def on_ready():
    NikitzaUser = await client.fetch_user(664948560818864166)                   # I can't be 100% sure that everything is OK after restart, so I made bot ping me each start
    await NikitzaUser.send("Бот рестартнулся, чекни не наебнулось ли чего")

    print("Bot starting...")
    print("Made by Nikitza Inc")
    # After each restart bot can't work with buttons/etc. it sent previously, so we have to send "Start order" button again
    with open('setupinformation.txt','r+') as setupinformation:             # After each restart (or after /setupchannels command) bot saves channel_orders and channel_orderlist values in "setupinformation.txt" file
            setupInformationContent = setupinformation.readlines()          # Reading data of our file, we get a list of all lines

            messageGuild = client.get_guild(your_guild_id)                  # Getting a guild bot currently in (we will use it later)
            print("Loading information from previous setup:")               
            print("Guild: "+ messageGuild.name)
            
            messageChannel = client.get_channel(int(setupInformationContent[0]))                        # Getting channel where users make their orders
            print("Orders channel: "+ messageChannel.name + ", ID: "+messageChannel.id.__str__())
            global channel_orderlist_tinker
            channel_orderlist_tinker = client.get_channel(int(setupInformationContent[3]))              # Getting channel where blacksmiths can work with orders
            print("Orders list channel: "+ channel_orderlist_tinker.name +", ID: "+channel_orderlist_tinker.id.__str__())
            print("-------")

            firstMessage = await messageChannel.fetch_message(int(setupInformationContent[1]))          # Getting first previously sent message 
            secondMessage = await messageChannel.fetch_message(int(setupInformationContent[2]))         # Getting second previously sent message (with "Start order" button)
            
            print("First message ID: "+firstMessage.id.__str__())
            print("Second message ID: "+secondMessage.id.__str__())
            print("-------")

            await firstMessage.delete()                                                                 # Deleting previously sent messages and sending new ones                    
            await secondMessage.delete()
            firstMessageSend = await firstMessage.channel.send("https://cdn.discordapp.com/attachments/939131677408653322/1104542455182925955/kuznya2.png")
            view=OrderButtonView()
            secondMessageSend = await secondMessage.channel.send(view=view)

            

            # Preparing setup info for next loadings
            setupInfoNew = []
            setupInfoNew.append(messageChannel.id.__str__()+ '\n')
            setupInfoNew.append(firstMessageSend.id.__str__()+ '\n')        # Saving data of all new messages in one list
            setupInfoNew.append(secondMessageSend.id.__str__()+ '\n')
            setupInfoNew.append(channel_orderlist_tinker.id.__str__())
            print("Updated setup information:")
            print(setupInfoNew)
            print("-------")

            setupinformation.truncate(0)                                    # Clearing our "setupinformation.txt" file
            setupinformation.seek(0)
            setupinformation.writelines(setupInfoNew)                       # Writing our list to file

            #Some discount roles we will use later (lines 2219-2231)
            global DiscountRole_1
            global DiscountRole_2
            global DiscountRole_3
            global DiscountRole_4
            global DiscountRole_5
            DiscountRole_1 = get(messageGuild.roles, name="Проходимец")
            DiscountRole_2 = get(messageGuild.roles, name="Частый гость")
            DiscountRole_3 = get(messageGuild.roles, name="Местный")
            DiscountRole_4 = get(messageGuild.roles, name="Родное личико")
            DiscountRole_5 = get(messageGuild.roles, name="В доску свой")
    # After each restart bot can't work with buttons/etc. it sent previously, so we have to send 10 last order messages again
    with open('setuporderinformation.txt','r+') as setuporderinformation:   
        print("loading orders from previous setup...")
        setupOrderInfoContent = setuporderinformation.readlines()
        orderInfoUserIDs = [0]
        orderInfoFirstmessageIDs = [0]
        orderInfoMessageIDs = [0]
        orderInfoMessageStatus = [0]
        spl = len(setupOrderInfoContent) - 10 # List length-10 because we want to get 10 last orders 
        n = 0
        # Splitter
        while spl < len(setupOrderInfoContent):
            orderInfoSplit = setupOrderInfoContent[spl].split()
            if spl == len(setupOrderInfoContent) - 10:
                orderInfoUserIDs[0] = int(orderInfoSplit[0])
                orderInfoFirstmessageIDs[0] = int(orderInfoSplit[1])
                orderInfoMessageIDs[0] = int(orderInfoSplit[2])             # We a splitting our list that was loaded from the file to lines
                orderInfoMessageStatus[0] = int(orderInfoSplit[3])          # Then, we a splitting our lines to lists of values 
            else:                                                           # Each order has 2 messages in it: first contains embed with order information, second contains buttons for blacksmiths
                orderInfoUserIDs.append(int(orderInfoSplit[0]))             # We must get an ID of the first message (orderInfoFirstmessageIDs[]) and ID of the second message (orderInfoMessageIDs[])
                orderInfoFirstmessageIDs.append(int(orderInfoSplit[1]))     # You will find such splitter later in my code
                orderInfoMessageIDs.append(int(orderInfoSplit[2]))
                orderInfoMessageStatus.append(int(orderInfoSplit[3]))
            spl += 1
        
        bufferFirstMessageID = [0,0,0,0,0,0,0,0,0,0]
        bufferSecondMessageID = [0,0,0,0,0,0,0,0,0,0]
        print("Updating order messages...")
        while n < len(orderInfoMessageIDs):
            firstOrderMessage = await channel_orderlist_tinker.fetch_message(orderInfoFirstmessageIDs[n])       # Getting first previously sent message
            firstOrderMessageEmbed = firstOrderMessage.embeds[0]                                                # Getting the embed that was in that message
            secondOrderMessage = await channel_orderlist_tinker.fetch_message(orderInfoMessageIDs[n])           # Getting second previously sent message
            if orderInfoMessageStatus[n] != 0:                                                                  
                secondOrderMessageEmbed = secondOrderMessage.embeds[0]                                          # Getting the embed that was in that message(if it has one)

            match orderInfoMessageStatus[n]:                    # According to the status of the order, we must sent a sepecific set of buttons
                case 0:
                    sendView = OrderTinkerView()
                case 1:
                    sendView = OrderTinkerViewAccepted()
                case 2:
                    sendView = OrderTinkerViewAccepted()
                case 3:
                    sendView = OrderTinkerViewReady()
                case 4:
                    sendView = OrderTinkerViewRejected()
            
            await firstOrderMessage.delete()
            await secondOrderMessage.delete()
            firstOrderMessageSend = await channel_orderlist_tinker.send(embed=firstOrderMessageEmbed)           # Deleting previously sent messages and sending new ones
            if orderInfoMessageStatus[n] != 0:
                secondOrderMessageSend = await channel_orderlist_tinker.send(embed=secondOrderMessageEmbed, view=sendView)
            else:
                secondOrderMessageSend = await channel_orderlist_tinker.send(view=sendView)

            bufferFirstMessageID[n] = firstOrderMessageSend.id
            bufferSecondMessageID[n] = secondOrderMessageSend.id            # Saving IDs of all new messages in lists
            orderIDnumber[n] = secondOrderMessageSend.id
            n += 1
            print(f'>{n} order updated')
        
        orderInfoFirstmessageIDs = bufferFirstMessageID
        orderInfoMessageIDs = bufferSecondMessageID
        print("Order messages IDs: "+ orderIDnumber.__str__())

        # Collect all values back in one list
        unsplit = len(setupOrderInfoContent) - 10
        op = 0
        while unsplit < len(setupOrderInfoContent):

            orderInfoLine = orderInfoUserIDs[op].__str__() + " "+ orderInfoFirstmessageIDs[op].__str__()+" "+orderInfoMessageIDs[op].__str__()+" "+orderInfoMessageStatus[op].__str__()+'\n'
            setupOrderInfoContent[unsplit] = orderInfoLine
            unsplit += 1
            op += 1
        
        setuporderinformation.truncate(0)
        setuporderinformation.seek(0)
        setuporderinformation.writelines(setupOrderInfoContent)     # Uploading that list to our file
        print("All orders updated!")
        print("-------")

    with open("last10costsNpoints.txt",'r+') as costsnumbers:    # Loading last 10 order's costs and customer's points from file "last10costsNpoints.txt"
        costsPointsContent = costsnumbers.readlines()
        print("Updating costs and customers' points...")
        
        global orderIDcost
        cp = 0
        while cp < len(costsPointsContent):
            costsPointsContentLine = costsPointsContent[cp].split()
            orderIDcost[cp] = costsPointsContentLine[0]             # This list contains cost of 10 last orders (We use it to match customer and cost of his order)
            cp += 1
        print("Costs list: "+orderIDcost.__str__())
        print("Orders' message numbers: "+ orderIDnumber.__str__())
        print("Updating costs and orders' messages IDs completed!")
        print("-------")


# SLASH COMMANDS
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=modals#commands

# When ready, admin should send special slash command /setupbot to submit the channel where users can leave orders and the channel where blacksmiths can see these orders
@client.tree.command()
@app_commands.describe(
    channel_orders="Задайте канал, в котором покупатели смогут оставить свой заказ.",                           #Here are descriptions of command elements 
    channel_orderlist="Задайте канал, в котором кузнецы смогут видеть и принимать поступившие заказы.")
async def setupchannels(interaction: discord.Interaction, channel_orders:discord.TextChannel, channel_orderlist:discord.TextChannel):
    """Задать каналы, где можно заказать и где отображаются оставленные заказы."""      # Description of the command

    # I made a system which only allows me and my friend to use the slash command
    if  interaction.user.id == 366490933614608384 or interaction.user.id == 664948560818864166:
        
        # To response to a slash command/button/select menu/etc. we should use interaction.response.send_message()
        # Ephemeral parameter means that the response can only be seen by the person who started the interaction 
        await interaction.response.send_message(ephemeral=True, content='Каналы '+ channel_orders.name+' и '+channel_orderlist.name+ ' заданы!')
        orderlistInfo = discord.Embed(title="Этот канал назначен списком заказов!",color=discord.Colour.from_str('0x2366c4'))

        # Bot sends some starting information to the channels, submitted by admin
        view=OrderButtonView()
        messagePNG = await channel_orders.send("https://cdn.discordapp.com/attachments/939131677408653322/1104542455182925955/kuznya2.png")
        messageButton = await channel_orders.send(view=view)

        await channel_orderlist.send(embed=orderlistInfo)

        # This variable we will need later to understand in which channel bot should send orders to blacksmiths
        global channel_orderlist_tinker
        channel_orderlist_tinker = channel_orderlist
        
        # Preparing setup info for next loadings
        setupInfo = []
        setupInfo.append(channel_orders.id.__str__()+ '\n')
        setupInfo.append(messagePNG.id.__str__()+ '\n')
        setupInfo.append(messageButton.id.__str__()+ '\n')
        setupInfo.append(channel_orderlist.id.__str__())
        print("Successful channels and messages setup:")
        print(setupInfo)
        print("-------")

        with open('setupinformation.txt','r+') as setupinformation:     # Opening file setupinformation.txt
            setupinformation.truncate(0)                                # Clearing this file
            setupinformation.seek(0)                                    # Searching for start of the file (if we don't do it bot writes in the end of text that was in the file)
            setupinformation.writelines(setupInfo)                      # Writing our list to file

    else:
        await interaction.response.send_message(":x: У вас нет права делать это!",ephemeral=True)


# With the help of this commands admin and blacksmiths can add user's id to blacklist or remove it from blacklist or get all blacklisted users
@client.tree.command()
@app_commands.describe(
    addname="Если игрок, которого вы хотите добавить в чёрный список, есть в дс кузни, выберите его в списке.",
    addid = "Если игрок, которого вы хотите добавить в чёрный список, отсутствует в дс кузни, введите его ID.",
    removeid = "Введите ID игрока (ID discord пользователя) которого хотите убрать из чёрного списка."
)
async def blacklist(interaction: discord.Interaction, addname:discord.User = None, addid:str = "0",removeid:str = "0"):
    """Открыть чёрный список кузни, добавить в него или убрать из него игрока."""

    # I made a system which only allows me and my friends to use the slash command 
    # TODO rewrite this system better way
    if  interaction.user.id == 366490933614608384 or interaction.user.id == 664948560818864166 or interaction.user.id == 402530884386816001 or interaction.user.id == 356112816970924033 or interaction.user.id == 745553166426308619:
        
        with open('blacklist.txt','r+') as blacklist:
            blacklistContent = blacklist.readlines()
            if addid != "0": 
                blacklistContent.append(addid + "\n")
                userFromId = await client.fetch_user(addid)
                embedBlacklistID = discord.Embed(title='Игрок '+userFromId.name +' добавлен в чёрный список!', color=discord.Colour.from_str('0x2366c4'))
                await interaction.response.send_message(embed=embedBlacklistID)
                print(userFromId.name+ " was added to blacklist by "+ interaction.user.name)
                print("Blacklist:")    
                print(blacklistContent)
                print("-------")
                
            elif addname != None:
                blacklistContent.append(addname.id.__str__() + "\n")
                embedBlacklistName = discord.Embed(title='Игрок '+ addname.name +' добавлен в чёрный список!', color=discord.Colour.from_str('0x2366c4'))
                await interaction.response.send_message(embed=embedBlacklistName)
                print(addname.name+ " was added to blacklist by "+ interaction.user.name)
                print("Blacklist:")    
                print(blacklistContent)
                print("-------")
            
            # This removes user's id to blacklist
            elif removeid != "0":
                f = 0
                someoneUnblacklisted = False

                while f < len(blacklistContent):
                    if blacklistContent[f] == removeid + "\n":
                        blacklistContent.pop(f)
                        someoneUnblacklisted = True
                    f +=1
            
                if someoneUnblacklisted == True:
                    userFromId = await client.fetch_user(removeid)
                    embedRemoveBlacklistID = discord.Embed(title='Игрок '+userFromId.name +' удалён из чёрного списка!', color=discord.Colour.from_str('0x2366c4'))
                    await interaction.response.send_message(embed=embedRemoveBlacklistID)
                    print(userFromId.name+ " was removed from blacklist by "+ interaction.user.name)
                    print("Blacklist:")    
                    print(blacklistContent)
                    print("-------")
                
                else:    
                    embedCantRemoveBlacklistID = discord.Embed(title=':x: Такого игрока нет в чёрном списке!', color=discord.Colour.from_str('0x2366c4'))
                    await interaction.response.send_message(embed=embedCantRemoveBlacklistID, ephemeral=True)

                # Last one ID was duplicated so we have to remove it and write list to file
                blacklist.truncate(0)
                blacklist.seek(0)
                blacklist.writelines(blacklistContent)

            else:
                if len(blacklistContent) == 0:
                    await interaction.response.send_message(embed=discord.Embed(title="Чёрный список пуст!", color=discord.Colour.from_str('0x2366c4')))
                else:
                    blacklistLine = f'<@{blacklistContent[0][0:len(blacklistContent[0])-1]}>' + "\n"
                    h = 1

                    while h < len(blacklistContent):
                        blacklistContentLine = blacklistContent[h]
                        blacklistLine += f'<@{blacklistContentLine[0:len(blacklistContentLine)-1]}>' + "\n"
                        h += 1

                    embedBlacklistList = discord.Embed(color=discord.Colour.from_str('0x2366c4'))
                    embedBlacklistList.add_field(name="Чёрный список:",value=blacklistLine, inline=False)
                    await interaction.response.send_message(embed=embedBlacklistList)

                    print("Blacklist:")    
                    print(blacklistContent)
                    print("-------")

            
            blacklist.seek(0)
            blacklist.writelines(blacklistContent)
    else:
        await interaction.response.send_message(":x: У вас нет права делать это!",ephemeral=True)

# Help command
# Bot sends different messages to blacksmiths and to customers
@client.tree.command()
@app_commands.describe()
async def help(interaction: discord.Interaction):
    """Получить информацию о работе с ботом."""

    if  interaction.user.id == 366490933614608384 or interaction.user.id == 664948560818864166 or interaction.user.id == 402530884386816001 or interaction.user.id == 356112816970924033 or interaction.user.id == 745553166426308619:
        
        helpBlacksmiths = discord.Embed(title="Информация для кузнецов",color=discord.Colour.from_str('0x2366c4'))
        helpBlacksmiths.add_field(
            name="Инструкция по работе с заказом:",
            value=f'Когда покупатель составляет заказ, он отправляется в <#{channel_orderlist_tinker.id.__str__()}>.'+'\n'+
            'Вы можете принять его, нажав соответствующую кнопку. Ecли заказ составлен некорректно, вы можете отклонить его, **указав причину отказа.**'+'\n'+'\n'+
            'Когда вы приняли заказ, вы должны указать его стоимость **без учёта скидки покупателя**. Бот автоматически посчитает стоимость заказа с учётом скидки.'+'\n'+
            'Если по той или иной причине вы не можете завершить заказ, вы можете отклонить его, **указав причину отказа.**'+'\n'+
            'Все возникающие вопросы вы можете уточнить у заказчика в личном сообщении.'+'\n'+'\n'+
            'Когда заказ готов, оповестите заказчика, нажав соответствующую кнопку.',
            inline=False)
        helpBlacksmiths.add_field(
            name="Команды:",
            value="• `/help` - вызывает это меню."+'\n'+
            "• `/blacklist` - вызывает чёрный список кузни."+'\n'+
            "• `/blacklist addname <игрок>` - добавить игрока в чёрный список кузни (если он есть на этом сервере)."+'\n'+
            "• `/blacklist addid <id>` - добавить id игрока в чёрный список кузни (если игрока нет на этом сервере)."+'\n'+
            "• `/blacklist removeid <id>` - убрать id игрока из чёрного списка кузни."+'\n'+
            "• `/setupchannels channel_orders <канал> channel_orderlist <канал>` - обновить каналы, с которыми работает бот.",
            inline=False)
        await interaction.response.send_message(embed=helpBlacksmiths)

    else:
        helpUsers = discord.Embed(title="Информация для покупателей",color=discord.Colour.from_str('0x2366c4'))
        helpUsers.add_field(
            name="Инструкция по составлению заказа",
            value='Перейдите в канал <#824589091646472214> и начните составление заказа.'+'\n'+
            'Выберите необходимые вам товары. ***Все предметы брони, мечи и инструменты по умолчанию делаются алмазными.*** '+'\n'+'\n'+
            'Не забудьте выбрать зачарования для предметов c помощью кнопки '+'\n'+'"**`Выбрать зачарования`**"! '+
            '***Имейте ввиду, что некоторые зачарования конфликтуют друг с другом. Если выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование!***'+ '\n'+'\n'+
            'Если вас интересует незеритовый аналог товара, выберите его, нажав на соответствующую кнопку. Если же вас интересует иной материал, пожалуйста опишите это в комментарии к заказу.'+ '\n'+'\n'+
            'Для добавления украшений(декораций) к вашей броне, нажмите кнопку "**`Выбрать украшения брони`**".'+'\n'+'\n'+
            'В вашем комментарии укажите все необходимые подробности заказа, например, место доставки, особенности материала или чар.'+'\n'+
            'Когда вы составили ваш заказ, нажмите кнопку "**`Подтвердить заказ`**".',
            inline=False)
        helpUsers.add_field(
            name="После составления заказа",
            value='Когда ваш заказ примет кузнец, вы получите уведомление в **личные сообщения**. Там же вы найдёте стоимость вашего заказа.'+'\n'+
            'Когда ваш заказ будет готов, вас уведомят в личных сообщениях. Вы сможете выбрать способ оплаты - наличными деньгами на месте или с помощью банковской карты.',
            inline=False)
        
        await interaction.response.send_message(embed=helpUsers)


# Here are some variables and lists we will need

makingOrder = False             # True if someone is making order (obviously). We will need this variable to not let 2 customers make their orders in the same time (this leads to horrible errors) 
madeOrder = False               # True if someone has just made order (obviously too). We will need thid variable to not let someone make an order twice
orderCommentSubmit = False      # True if customer submitted his comment. We will need it to let bot understand if he need to put user's comment in final order embed
netherite = False               # True if customer submitted some netherite made items. We will need it to let bot understand if he need to put values of netherite selection menu in final order embed

orderValues = "-"               # This string variable contains values of main item selection menu which were chosen by customer
netheriteValues = "-"           # This string variable contains values of netherite selection menu if customer has chosen ones

products = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]      # This list contains data which items customer selected in main item selection menu

chosenTrims = ["-","-","-","-","-"]                                                 # This list contains values of armour trim pattern selection menus which were chosen by customer
chosenMaterials = ["-","-","-","-","-"]                                             # This list contains values of armour trim material selection menus which were chosen by customer
trimsEnabled = [False,False,False,False,False]                                      # This list contains data about which armour trims the customer has selected
enchants = ["-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-"]    # This list contains values of item's enchantments selection menus which were chosen by customer

valueNumber = 0                             # This variable we use to save data of customer and his order





# After each order we have to clear values of all variables and lists used in making order
# I understand that my code sometimes looks very goofy, but I don't understand how to make some things better
def clearValues():
    global orderCommentSubmit
    global netherite
    global madeOrder

    global orderValues
    global netheriteValues

    global chosenTrims
    global chosenMaterials
    global trimsEnabled

    global products
    global enchants

    orderCommentSubmit = False
    netherite = False
    madeOrder = False

    chosenTrims = ["-","-","-","-","-"]
    chosenMaterials = ["-","-","-","-","-"]
    trimsEnabled = [False,False,False,False,False]

    products = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]
    enchants = ["-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-","-"]

    #These should be made into one list, but I'm too lazy to do it
    orderValues = "-"
    netheriteValues = "-"

# If someone started making an order and didn't finish within 10 minutes, bot should clean all the values and lists and allow another user make his order
def timeout():
    global makingOrder
    makingOrder = False
    clearValues()
    print("Order timed out!")
    print("-------")

# This function we will nee to arrange all selected options of a selection menu in one string
def valueLine(values):
    valueLine = values[0]
    num = 1
    while num < len(values):
        valueLine += ", "+ values[num]
        num += 1
    return valueLine

# The main menu of an order, there user can choose items to buy and press the buttons (you can see them in lines 12-15) 
class StartOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Составить заказ!", custom_id="order",)

    async def callback(self, interaction:discord.Interaction): 
        embed1 = discord.Embed(
            title="Составьте ваш заказ!",
            color=discord.Colour.from_str('0x2366c4'),
            description="В выпадающем списке выберите товары, которые хотите приобрести.")
        embed1.add_field(name="<:Enchanted_Book:1140597764326162503> Выбрать зачарования",value="Не забудьте выбрать зачарования для предметов! ***Имейте ввиду, что некоторые зачарования конфликтуют друг с другом. Если выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование!***",inline=False)
        embed1.add_field(name="<:Netherite_Ingot:1140595704293756938> Материал товара",value="***Все предметы брони, мечи и инструменты по умолчанию делаются алмазными.*** Если вас интересует незеритовый аналог товара, выберите его, нажав на соответствующую кнопку. Если же вас интересует иной материал, пожалуйста опишите это в комментарии к заказу.",inline=False)
        embed1.add_field(name="<:Tide_Armor_Trim:1140599228025012346> Украшения брони", value='Добавьте уникальности вашему обмундированию! Для добавления украшений (декораций) к вашей броне, нажмите кнопку "**Выбрать украшения брони**".')
        embed1.add_field(name="💬 Добавить комментарий к заказу",value="Также можно добавить комментарий к заказу. Укажите все подробности заказа, например, место доставки, особенности материала или чар.",inline=False)
        embed1.add_field(name="Выбранные товары:",value="-",inline=True)
        

        embedCantStartOrder = discord.Embed(title=":clock2: В данный момент бот занят другим пользователем, пожалуйста попробуйте через 7-10 минут!",color=discord.Colour.from_str('0x2366c4'))
        global makingOrder
        view=OrderView()

        # The bot doesn't allow two players to make orders at the same time
        # If someone is making order (makingOrder = True) it responds with a "The bot is currently being used, please try again later!" message
        # Bot also doesn't allow blacklisted players to make orders

        if makingOrder == False:
            with open('blacklist.txt','r') as blacklistOrder:
                blacklistOrderContent = blacklistOrder.readlines()
                

                i = 0
                blacklisted = False

                while i < len(blacklistOrderContent):
                    blacklistID = int(blacklistOrderContent[i],base=10)
                    

                    if interaction.user.id == blacklistID:
                        blacklisted = True
                    i+=1

                if blacklisted == True:    
                    await interaction.response.send_message(ephemeral=True, embed=discord.Embed(title=":x: Вы не можете сделать заказ так как находитесь в чёрном списке!",color=discord.Colour.from_str('0x2366c4')))
                    print("Blacklisted "+ interaction.user.name+" failed to order!")
                
                else:
                    await interaction.response.send_message(embed=embed1,view=view,ephemeral=True)
                    clearValues()
            
                    makingOrder = True
                    print(interaction.user.name+" is making new order!")
                    print("-------")

                    global timeoutTimer
                    timeoutTimer = Timer(600,timeout)       #We wait 10 minutes, then we clear all data the customer submitted
                    timeoutTimer.start()

        else:
            await interaction.response.send_message(embed=embedCantStartOrder,ephemeral=True)
            print(interaction.user.name+" failed to order")
            print("-------")



# SELECTION MENUS
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=modals#select-menus

# Main selection menu where user can choose items to buy
class OrderSelect(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Трезубец",emoji='<:trezubets:1140545960485867560>'),
            discord.SelectOption(label="Меч",emoji='<:sword:1128128015604387881>'),
            discord.SelectOption(label="Арбалет",emoji='<:crossbow:1140535524654858350>'),
            discord.SelectOption(label="Лук",emoji='<:lukLuchok:1140553958209880115>'),
            discord.SelectOption(label="Топор",emoji='<:Diamond_Axe:1140564246208446594>'),
            discord.SelectOption(label="Кирка",emoji='<:Diamond_Pickaxe:1140564674165886976>'), 
            discord.SelectOption(label="Лопата",emoji='<:Diamond_Shovel:1140582652290793573>'),
            discord.SelectOption(label="Мотыга",emoji='<:Diamond_Hoe:1140582868746248220>'),
            discord.SelectOption(label="Удочка",emoji='<:Fishing_Rod:1140583684391579720>'),
            discord.SelectOption(label="Черепаший панцирь",emoji='<:Turtle_Shell:1140584351617273856>'),
            discord.SelectOption(label="Шлем",emoji='<:Diamond_Helmet:1140585332602064996>'),
            discord.SelectOption(label="Нагрудник",emoji='<:Diamond_Chestplate:1140586301494657125>'),
            discord.SelectOption(label="Поножи",emoji='<:Diamond_Leggings:1140586298298613781>'),
            discord.SelectOption(label="Ботинки",emoji='<:Diamond_Boots:1140586343228002425>'),
            discord.SelectOption(label="Зажигалка",emoji='<:Flint_and_Steel:1140587538495586305>'),
            discord.SelectOption(label="Щит",emoji='<:Shield:1140587885951717498>'),
            discord.SelectOption(label="Ножницы",emoji='<:Shears:1140588229331009586>')
        ]
        super().__init__(placeholder="Выберите нужные товары", min_values=1, max_values=17, options=options)
    
    async def callback(self, interaction:discord.Interaction):
        global embedEdit
        embedEdit = discord.Embed(
            title="Составьте ваш заказ!",
            color=discord.Colour.from_str('0x2366c4'),
            description="В выпадающем списке выберите товары, которые хотите приобрести.")
        embedEdit.add_field(name="<:Enchanted_Book:1140597764326162503> Выбрать зачарования",value="Не забудьте выбрать зачарования для предметов! ***Имейте ввиду, что некоторые зачарования конфликтуют друг с другом. Если выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование!***",inline=False)
        embedEdit.add_field(name="<:Netherite_Ingot:1140595704293756938> Материал товара",value="***Все предметы брони, мечи и инструменты по умолчанию делаются алмазными.*** Если вас интересует незеритовый аналог товара, выберите его, нажав на соответствующую кнопку. Если же вас интересует иной материал, пожалуйста опишите это в комментарии к заказу.",inline=False)
        embedEdit.add_field(name="<:Tide_Armor_Trim:1140599228025012346> Украшения брони", value='Добавьте уникальности вашему обмундированию! Для добавления украшений (декораций) к вашей броне, нажмите кнопку "**Выбрать украшения брони**".')
        embedEdit.add_field(name="💬 Добавить комментарий к заказу",value="Также можно добавить комментарий к заказу. Укажите все подробности заказа, например, место доставки, особенности материала или чар.",inline=False)
        embedEdit.add_field(name="Выбранные товары:",value=valueLine(self.values),inline=True)
        await interaction.response.defer(ephemeral=True)  
                                                            
        await interaction.edit_original_response(embed=embedEdit)
                                                        
        global orderValues                              
        orderValues = valueLine(self.values)

        global trimsEnabled
        trimsEnabled = [False,False,False,False,False]

        # This list contains data about which items are selected by the user.
        global products
        products = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]
        
        i=0
        print("Items chosen by "+ interaction.user.name +":")
        while i < len(self.values):
            print(self.values[i])
            if self.values[i] == "Трезубец":
                products[0] = True
            if self.values[i] == "Меч":
                products[1]  = True
            if self.values[i] == "Арбалет":
                products[2]  = True
            if self.values[i] == "Лук":
                products[3]  = True
            if self.values[i] == "Топор":
                products[4]  = True
            if self.values[i] == "Кирка":
                products[5]  = True
            if self.values[i] == "Лопата":
                products[6]  = True
            if self.values[i] == "Мотыга":
                products[7]  = True
            if self.values[i] == "Удочка":
                products[8]  = True
            if self.values[i] == "Черепаший панцирь":
                products[9]  = True
            if self.values[i] == "Шлем":
                products[10]  = True
            if self.values[i] == "Нагрудник":
                products[11]  = True
            if self.values[i] == "Поножи":
                products[12]  = True
            if self.values[i] == "Ботинки":
                products[13]  = True
            if self.values[i] == "Зажигалка":
                products[14]  = True
            if self.values[i] == "Щит":
                products[15]  = True
            if self.values[i] == "Ножницы":
                products[16]  = True

            i += 1
        print("-------")


# Selection menu where users can choose what items should be done with netherite
class OrderSelectNetherite(discord.ui.Select):
    def __init__(self):
        valuesCount = 1
        options=[discord.SelectOption(label="Всe выбранные товары",emoji='<:Netherite_Ingot:1140595704293756938>')]
        if products[1] == True:
            options.append(discord.SelectOption(label="Меч",emoji='<:sword:1128128015604387881>'))
            valuesCount += 1
        if products[4] == True:
            options.append(discord.SelectOption(label="Топор",emoji='<:Diamond_Axe:1140564246208446594>'))
            valuesCount += 1
        if products[5] == True:
            options.append(discord.SelectOption(label="Кирка",emoji='<:Diamond_Pickaxe:1140564674165886976>'))
            valuesCount += 1
        if products[6] == True:
            options.append(discord.SelectOption(label="Лопата",emoji='<:Diamond_Shovel:1140582652290793573>'))
            valuesCount += 1
        if products[7] == True:
            options.append(discord.SelectOption(label="Мотыга",emoji='<:Diamond_Hoe:1140582868746248220>'))
            valuesCount += 1
        if products[10] == True:
            options.append(discord.SelectOption(label="Шлем",emoji='<:Diamond_Helmet:1140585332602064996>'))
            valuesCount += 1
        if products[11] == True:
            options.append(discord.SelectOption(label="Нагрудник",emoji='<:Diamond_Chestplate:1140586301494657125>'))
            valuesCount += 1
        if products[12] == True:
            options.append(discord.SelectOption(label="Поножи",emoji='<:Diamond_Leggings:1140586298298613781>'))
            valuesCount += 1
        if products[13] == True:
            options.append(discord.SelectOption(label="Ботинки",emoji='<:Diamond_Boots:1140586343228002425>'))
            valuesCount += 1
        
        super().__init__(placeholder="Выберите нужные товары", min_values=1, max_values=valuesCount, options=options)

    async def callback(self, interaction:discord.Interaction):
        global netheriteValues 
        global netherite
        netheriteValues = valueLine(self.values)
        netherite = True

        print("Netherite ones chosen by "+ interaction.user.name +":")
        print(netheriteValues)
        print("-------")

        embedEdit = discord.Embed(title="Выберите товары, которые необходимо сделать из незерита!",color=discord.Colour.from_str('0x2366c4')) 
        embedEdit.add_field(name="Из незерита будут сделаны:",value=valueLine(self.values),inline=False) 
        await interaction.response.defer(ephemeral=True)  
        await interaction.edit_original_response(embed=embedEdit)


# Enchantments selection menus
# Here we allow user to choose enchantments for his items
# Trident Enchantments  
class SelectTrezubEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Громовержец"),
            discord.SelectOption(label="Пронзатель (V)"),
            discord.SelectOption(label="Верность (III)",description="Несовместимо с тягуном."),
            discord.SelectOption(label="Тягун (III)",description="Несовместимо с пронзателем, верностью."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования трезубца", min_values=1, max_values=7, options=options)
        
    

    async def callback(self, interaction:discord.Interaction):
            global enchants
            enchants[0] = valueLine(self.values)

            trezubEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
            if products[0] == True:
                trezubEmbed.add_field(name="Зачарования трезубца:", value=enchants[0], inline=False)
            if products[1]  == True:
                trezubEmbed.add_field(name="Зачарования меча:", value=enchants[1], inline=False)
            if products[2]  == True:
                trezubEmbed.add_field(name="Зачарования арбалета:", value=enchants[2], inline=False)
            if products[3]  == True:
                trezubEmbed.add_field(name="Зачарования лука:", value=enchants[3], inline=False)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=trezubEmbed)

# Sword Enchantments
class SelectSwordEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Острота (V)",description="Несовместимо с бичом членистоногих, небесной карой."),
            discord.SelectOption(label="Бич членистоногих (V)",description="Несовместимо с остротой, небесной карой."),
            discord.SelectOption(label="Небесная кара (V)",description="Несовместимо с бичом членистоногих, остротой."),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Разящий клинок (III)"),
            discord.SelectOption(label="Заговор огня (II)"),
            discord.SelectOption(label="Отдача (II)"),
            discord.SelectOption(label="Добыча (III)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования меча", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
            global enchants
            enchants[1] = valueLine(self.values)
            
            swordEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
            if products[0] == True:
                swordEmbed.add_field(name="Зачарования трезубца:", value=enchants[0], inline=False)
            if products[1]  == True:
                swordEmbed.add_field(name="Зачарования меча:", value=enchants[1], inline=False)
            if products[2]  == True:
                swordEmbed.add_field(name="Зачарования арбалета:", value=enchants[2], inline=False)
            if products[3]  == True:
                swordEmbed.add_field(name="Зачарования лука:", value=enchants[3], inline=False)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=swordEmbed)

# Crossbow Enchantments
class SelectCrossbowEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Тройной выстрел",description="Несовместимо с пронзающей стрелой."),
            discord.SelectOption(label="Пронзающая стрела (IV)",description="Несовместимо с тройным выстрелом."),
            discord.SelectOption(label="Быстрая перезарядка (III)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования арбалета", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
            global enchants
            enchants[2] = valueLine(self.values)

            crossbowEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
            if products[0] == True:
                crossbowEmbed.add_field(name="Зачарования трезубца:", value=enchants[0], inline=False)
            if products[1]  == True:
                crossbowEmbed.add_field(name="Зачарования меча:", value=enchants[1], inline=False)
            if products[2]  == True:
                crossbowEmbed.add_field(name="Зачарования арбалета:", value=enchants[2], inline=False)
            if products[3]  == True:
                crossbowEmbed.add_field(name="Зачарования лука:", value=enchants[3], inline=False)
            
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=crossbowEmbed)

# Bow Enchantments
class SelectBowEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Бесконечность"),
            discord.SelectOption(label="Сила (V)"),
            discord.SelectOption(label="Отбрасывание (II)"),
            discord.SelectOption(label="Горящая стрела"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования лука", min_values=1, max_values=7, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[3] = valueLine(self.values)

        bowEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))
        if products[0] == True:
            bowEmbed.add_field(name="Зачарования трезубца:", value=enchants[0], inline=False)
        if products[1]  == True:
            bowEmbed.add_field(name="Зачарования меча:", value=enchants[1], inline=False)
        if products[2]  == True:
            bowEmbed.add_field(name="Зачарования арбалета:", value=enchants[2], inline=False)
        if products[3]  == True:
            bowEmbed.add_field(name="Зачарования лука:", value=enchants[3], inline=False)
            
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=bowEmbed)

# Axe Enchantments
class SelectAxeEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
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
        global enchants
        enchants[4] = valueLine(self.values)
        axeEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[4]  == True:
            axeEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
        if products[5]  == True:
            axeEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
        if products[6]  == True:
            axeEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
        if products[7]  == True:
            axeEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
        if products[8]  == True:
            axeEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=axeEmbed)

# Pickaxe Enchantments
class SelectPickaxeEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования кирки", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[5] = valueLine(self.values)
        pickaxeEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[4]  == True:
            pickaxeEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
        if products[5]  == True:
            pickaxeEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
        if products[6]  == True:
            pickaxeEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
        if products[7]  == True:
            pickaxeEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
        if products[8]  == True:
            pickaxeEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=pickaxeEmbed)

# Shovel Enchantments
class SelectShovelEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования лопаты", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[6] = valueLine(self.values)
        shovelEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[4]  == True:
            shovelEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
        if products[5]  == True:
            shovelEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
        if products[6]  == True:
            shovelEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
        if products[7]  == True:
            shovelEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
        if products[8]  == True:
            shovelEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=shovelEmbed)

# Hoe Enchantments
class SelectHoeEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Шёлковое касание",description="Несовместимо с удачей."),
            discord.SelectOption(label="Удача (III)",description="Несовместимо с шелковым касанием."),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования мотыги", min_values=1, max_values=6, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[7] = valueLine(self.values)
        hoeEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[4]  == True:
            hoeEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
        if products[5]  == True:
            hoeEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
        if products[6]  == True:
            hoeEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
        if products[7]  == True:
            hoeEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
        if products[8]  == True:
            hoeEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=hoeEmbed)
        
# FishingRod Enchantments
class SelectFishingRodEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Приманка(III)"),
            discord.SelectOption(label="Везучий рыбак (III)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования удочки", min_values=1, max_values=5, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[8] = valueLine(self.values)
        fishingRodEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[4]  == True:
            fishingRodEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
        if products[5]  == True:
            fishingRodEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
        if products[6]  == True:
            fishingRodEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
        if products[7]  == True:
            fishingRodEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
        if products[8]  == True:
            fishingRodEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=fishingRodEmbed)

# Boots Enchantments
class SelectBootsEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
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
        global enchants
        enchants[13] = valueLine(self.values)
        bootsEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[9]  == True:
            bootsEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
        if products[10]  == True:
            bootsEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
        if products[11]  == True:
            bootsEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
        if products[12]  == True:
            bootsEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
        if products[13]  == True:
            bootsEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=bootsEmbed)

# Turtle Enchantments
class SelectTurtleEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
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
        global enchants
        enchants[9] = valueLine(self.values)
        turtleEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[9]  == True:
            turtleEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
        if products[10]  == True:
            turtleEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
        if products[11]  == True:
            turtleEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
        if products[12]  == True:
            turtleEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
        if products[13]  == True:
            turtleEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=turtleEmbed)

# Helmet Enchantments
class SelectHelmetEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
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
        global enchants
        enchants[10] = valueLine(self.values)
        helmetEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[9]  == True:
            helmetEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
        if products[10]  == True:
            helmetEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
        if products[11]  == True:
            helmetEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
        if products[12]  == True:
            helmetEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
        if products[13]  == True:
            helmetEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=helmetEmbed)

# Chestplate Enchantments
class SelectChestplateEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
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
        global enchants
        enchants[11] = valueLine(self.values)
        chestplateEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[9]  == True:
            chestplateEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
        if products[10]  == True:
            chestplateEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
        if products[11]  == True:
            chestplateEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
        if products[12]  == True:
            chestplateEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
        if products[13]  == True:
            chestplateEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=chestplateEmbed)

# Leggings Enchantments
class SelectLeggingsEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
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
        global enchants
        enchants[12] = valueLine(self.values)
        leggingsEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[9]  == True:
            leggingsEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
        if products[10]  == True:
            leggingsEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
        if products[11]  == True:
            leggingsEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
        if products[12]  == True:
            leggingsEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
        if products[13]  == True:
            leggingsEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
        
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=leggingsEmbed)

# Flint and steel Enchantments
class SelectFlintNsteelEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования зажигалки", min_values=1, max_values=3, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[14] = valueLine(self.values)
        flintNsteelEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[14]  == True:
            flintNsteelEmbed.add_field(name="Зачарования зажигалки:", value=enchants[14], inline=False)
        if products[15]  == True:
            flintNsteelEmbed.add_field(name="Зачарования щита:", value=enchants[15], inline=False)
        if products[16]  == True:
            flintNsteelEmbed.add_field(name="Зачарования ножниц:", value=enchants[16], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=flintNsteelEmbed)

# Shield Enchantments
class SelectShieldEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования щита", min_values=1, max_values=3, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[15] = valueLine(self.values)
        shieldEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[14]  == True:
            shieldEmbed.add_field(name="Зачарования зажигалки:", value=enchants[14], inline=False)
        if products[15]  == True:
            shieldEmbed.add_field(name="Зачарования щита:", value=enchants[15], inline=False)
        if products[16]  == True:
            shieldEmbed.add_field(name="Зачарования ножниц:", value=enchants[16], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=shieldEmbed)

# Scissors Enchantments
class SelectScissorsEnchantments(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Прочность (III)"),
            discord.SelectOption(label="Починка",description="Временно недоступно"),
            discord.SelectOption(label="Эффективность (V)"),
            discord.SelectOption(label="Проклятье утраты"),
        ]
        super().__init__(placeholder="Выберите зачарования ножниц", min_values=1, max_values=4, options=options)

    async def callback(self, interaction:discord.Interaction):
        global enchants
        enchants[16] = valueLine(self.values)
        scissorsEmbed = discord.Embed(title="Выбранные зачарования:", color=discord.Colour.from_str('0x2366c4'))

        if products[14]  == True:
            scissorsEmbed.add_field(name="Зачарования зажигалки:", value=enchants[14], inline=False)
        if products[15]  == True:
            scissorsEmbed.add_field(name="Зачарования щита:", value=enchants[15], inline=False)
        if products[16]  == True:
            scissorsEmbed.add_field(name="Зачарования ножниц:", value=enchants[16], inline=False)

        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=scissorsEmbed)

# Turtle helmet trim pattern
class SelectTrimPatternTurtle(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Страж",emoji='<:Sentry:1140626667598008380> '),
            discord.SelectOption(label="Вредина",emoji='<:Vex:1140626646437728406>'),
            discord.SelectOption(label="Дебри",emoji='<:Wild:1140626637512245309>'),
            discord.SelectOption(label="Берег",emoji='<:Coast:1140626682483572736>'),
            discord.SelectOption(label="Дюна",emoji='<:Dune:1140626678780014592>'),
            discord.SelectOption(label="Искатель",emoji='<:Wayfinder:1140626640901246986>'),
            discord.SelectOption(label="Сборщик",emoji='<:Raiser:1140626670785667182>'),
            discord.SelectOption(label="Скульптор",emoji='<:Shaper:1140626664078983200> '),
            discord.SelectOption(label="Вождь",emoji='<:Host:1140626674002702376>'),
            discord.SelectOption(label="Хранитель",emoji='<:Ward:1140626643325562900>'),
            discord.SelectOption(label="Тишина",emoji='<:Silence:1140626659955974275> '),
            discord.SelectOption(label="Прилив",emoji='<:Tide:1140626648157388841> '),
            discord.SelectOption(label="Рыло",emoji='<:Snout:1140626655535177798>'),
            discord.SelectOption(label="Ребро",emoji='<:Rib:1140626669330235574> '),
            discord.SelectOption(label="Око",emoji='<:Oko:1140626676766740480> '),
            discord.SelectOption(label="Шпиль",emoji='<:Spire:1140626651252805633> ')
        ]
        super().__init__(placeholder="Выберите шаблон украшения черепашьего панциря", min_values=1, max_values=16, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenTrims
        chosenTrims[0] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[0] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения черепашьего панциря:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[0], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[0], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Turtle helmet trim material
class SelectTrimMaterialTurtle(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Изумруд",emoji='<:Emerald:1140618895737241650>'),
            discord.SelectOption(label="Редстоун",emoji='<:Redstone_Dust:1140618892528590930>'),
            discord.SelectOption(label="Лазурит",emoji='<:Lapis_Lazuli:1140618881694707752>'),
            discord.SelectOption(label="Аметист",emoji='<:Amethyst_Shard:1140618890817310961>'),
            discord.SelectOption(label="Кварц",emoji='<:Nether_Quartz:1140618878775459851>'),
            discord.SelectOption(label="Незерит",emoji='<:Netherite_Ingot:1140595704293756938>'),
            discord.SelectOption(label="Алмаз",emoji='<:Diamond:1140600966752776213>'),
            discord.SelectOption(label="Золото",emoji='<:Gold_Ingot:1140618886350389319>'),
            discord.SelectOption(label="Железо",emoji='<:Iron_Ingot:1140618883611492453>'),
            discord.SelectOption(label="Медь",emoji='<:Copper_Ingot:1140618887868731503>')
        ]
        super().__init__(placeholder="Выберите материал украшения черепашьего панциря", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenMaterials
        chosenMaterials[0] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[0] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения черепашьего панциря:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[0], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[0], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Helmet trim pattern
class SelectTrimPatternHelmet(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Страж",emoji='<:Sentry:1140626667598008380> '),
            discord.SelectOption(label="Вредина",emoji='<:Vex:1140626646437728406>'),
            discord.SelectOption(label="Дебри",emoji='<:Wild:1140626637512245309>'),
            discord.SelectOption(label="Берег",emoji='<:Coast:1140626682483572736>'),
            discord.SelectOption(label="Дюна",emoji='<:Dune:1140626678780014592>'),
            discord.SelectOption(label="Искатель",emoji='<:Wayfinder:1140626640901246986>'),
            discord.SelectOption(label="Сборщик",emoji='<:Raiser:1140626670785667182>'),
            discord.SelectOption(label="Скульптор",emoji='<:Shaper:1140626664078983200> '),
            discord.SelectOption(label="Вождь",emoji='<:Host:1140626674002702376>'),
            discord.SelectOption(label="Хранитель",emoji='<:Ward:1140626643325562900>'),
            discord.SelectOption(label="Тишина",emoji='<:Silence:1140626659955974275> '),
            discord.SelectOption(label="Прилив",emoji='<:Tide:1140626648157388841> '),
            discord.SelectOption(label="Рыло",emoji='<:Snout:1140626655535177798>'),
            discord.SelectOption(label="Ребро",emoji='<:Rib:1140626669330235574> '),
            discord.SelectOption(label="Око",emoji='<:Oko:1140626676766740480> '),
            discord.SelectOption(label="Шпиль",emoji='<:Spire:1140626651252805633> ')
        ]
        super().__init__(placeholder="Выберите шаблон украшения шлема", min_values=1, max_values=16, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenTrims
        chosenTrims[1] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[1] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения шлема:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[1], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[1], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Helmet trim material
class SelectTrimMaterialHelmet(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Изумруд",emoji='<:Emerald:1140618895737241650>'),
            discord.SelectOption(label="Редстоун",emoji='<:Redstone_Dust:1140618892528590930>'),
            discord.SelectOption(label="Лазурит",emoji='<:Lapis_Lazuli:1140618881694707752>'),
            discord.SelectOption(label="Аметист",emoji='<:Amethyst_Shard:1140618890817310961>'),
            discord.SelectOption(label="Кварц",emoji='<:Nether_Quartz:1140618878775459851>'),
            discord.SelectOption(label="Незерит",emoji='<:Netherite_Ingot:1140595704293756938>'),
            discord.SelectOption(label="Алмаз",emoji='<:Diamond:1140600966752776213>'),
            discord.SelectOption(label="Золото",emoji='<:Gold_Ingot:1140618886350389319>'),
            discord.SelectOption(label="Железо",emoji='<:Iron_Ingot:1140618883611492453>'),
            discord.SelectOption(label="Медь",emoji='<:Copper_Ingot:1140618887868731503>')
        ]
        super().__init__(placeholder="Выберите материал украшения шлема", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenMaterials
        chosenMaterials[1] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[1] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения шлема:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[1], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[1], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Chestplate trim pattern
class SelectTrimPatternChestplate(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Страж",emoji='<:Sentry:1140626667598008380> '),
            discord.SelectOption(label="Вредина",emoji='<:Vex:1140626646437728406>'),
            discord.SelectOption(label="Дебри",emoji='<:Wild:1140626637512245309>'),
            discord.SelectOption(label="Берег",emoji='<:Coast:1140626682483572736>'),
            discord.SelectOption(label="Дюна",emoji='<:Dune:1140626678780014592>'),
            discord.SelectOption(label="Искатель",emoji='<:Wayfinder:1140626640901246986>'),
            discord.SelectOption(label="Сборщик",emoji='<:Raiser:1140626670785667182>'),
            discord.SelectOption(label="Скульптор",emoji='<:Shaper:1140626664078983200> '),
            discord.SelectOption(label="Вождь",emoji='<:Host:1140626674002702376>'),
            discord.SelectOption(label="Хранитель",emoji='<:Ward:1140626643325562900>'),
            discord.SelectOption(label="Тишина",emoji='<:Silence:1140626659955974275> '),
            discord.SelectOption(label="Прилив",emoji='<:Tide:1140626648157388841> '),
            discord.SelectOption(label="Рыло",emoji='<:Snout:1140626655535177798>'),
            discord.SelectOption(label="Ребро",emoji='<:Rib:1140626669330235574> '),
            discord.SelectOption(label="Око",emoji='<:Oko:1140626676766740480> '),
            discord.SelectOption(label="Шпиль",emoji='<:Spire:1140626651252805633> ')
        ]
        super().__init__(placeholder="Выберите шаблон украшения нагрудника", min_values=1, max_values=16, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenTrims
        chosenTrims[2] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[2] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения нагрудника:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[2], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[2], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Turtle helmet trim material
class SelectTrimMaterialChestplate(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Изумруд",emoji='<:Emerald:1140618895737241650>'),
            discord.SelectOption(label="Редстоун",emoji='<:Redstone_Dust:1140618892528590930>'),
            discord.SelectOption(label="Лазурит",emoji='<:Lapis_Lazuli:1140618881694707752>'),
            discord.SelectOption(label="Аметист",emoji='<:Amethyst_Shard:1140618890817310961>'),
            discord.SelectOption(label="Кварц",emoji='<:Nether_Quartz:1140618878775459851>'),
            discord.SelectOption(label="Незерит",emoji='<:Netherite_Ingot:1140595704293756938>'),
            discord.SelectOption(label="Алмаз",emoji='<:Diamond:1140600966752776213>'),
            discord.SelectOption(label="Золото",emoji='<:Gold_Ingot:1140618886350389319>'),
            discord.SelectOption(label="Железо",emoji='<:Iron_Ingot:1140618883611492453>'),
            discord.SelectOption(label="Медь",emoji='<:Copper_Ingot:1140618887868731503>')
        ]
        super().__init__(placeholder="Выберите материал украшения нагрудника", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenMaterials
        chosenMaterials[2] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[2] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения нагрудника:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[2], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[2], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Leggings trim pattern
class SelectTrimPatternLeggings(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Страж",emoji='<:Sentry:1140626667598008380> '),
            discord.SelectOption(label="Вредина",emoji='<:Vex:1140626646437728406>'),
            discord.SelectOption(label="Дебри",emoji='<:Wild:1140626637512245309>'),
            discord.SelectOption(label="Берег",emoji='<:Coast:1140626682483572736>'),
            discord.SelectOption(label="Дюна",emoji='<:Dune:1140626678780014592>'),
            discord.SelectOption(label="Искатель",emoji='<:Wayfinder:1140626640901246986>'),
            discord.SelectOption(label="Сборщик",emoji='<:Raiser:1140626670785667182>'),
            discord.SelectOption(label="Скульптор",emoji='<:Shaper:1140626664078983200> '),
            discord.SelectOption(label="Вождь",emoji='<:Host:1140626674002702376>'),
            discord.SelectOption(label="Хранитель",emoji='<:Ward:1140626643325562900>'),
            discord.SelectOption(label="Тишина",emoji='<:Silence:1140626659955974275> '),
            discord.SelectOption(label="Прилив",emoji='<:Tide:1140626648157388841> '),
            discord.SelectOption(label="Рыло",emoji='<:Snout:1140626655535177798>'),
            discord.SelectOption(label="Ребро",emoji='<:Rib:1140626669330235574> '),
            discord.SelectOption(label="Око",emoji='<:Oko:1140626676766740480> '),
            discord.SelectOption(label="Шпиль",emoji='<:Spire:1140626651252805633> ')
        ]
        super().__init__(placeholder="Выберите шаблон украшения понож", min_values=1, max_values=16, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenTrims
        chosenTrims[3] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[3] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения понож:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[3], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[3], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Leggings trim material
class SelectTrimMaterialLeggings(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Изумруд",emoji='<:Emerald:1140618895737241650>'),
            discord.SelectOption(label="Редстоун",emoji='<:Redstone_Dust:1140618892528590930>'),
            discord.SelectOption(label="Лазурит",emoji='<:Lapis_Lazuli:1140618881694707752>'),
            discord.SelectOption(label="Аметист",emoji='<:Amethyst_Shard:1140618890817310961>'),
            discord.SelectOption(label="Кварц",emoji='<:Nether_Quartz:1140618878775459851>'),
            discord.SelectOption(label="Незерит",emoji='<:Netherite_Ingot:1140595704293756938>'),
            discord.SelectOption(label="Алмаз",emoji='<:Diamond:1140600966752776213>'),
            discord.SelectOption(label="Золото",emoji='<:Gold_Ingot:1140618886350389319>'),
            discord.SelectOption(label="Железо",emoji='<:Iron_Ingot:1140618883611492453>'),
            discord.SelectOption(label="Медь",emoji='<:Copper_Ingot:1140618887868731503>')
        ]
        super().__init__(placeholder="Выберите материал украшения понож", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenMaterials
        chosenMaterials[3] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[3] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения понож:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[3], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[3], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Boots trim pattern
class SelectTrimPatternBoots(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Страж",emoji='<:Sentry:1140626667598008380> '),
            discord.SelectOption(label="Вредина",emoji='<:Vex:1140626646437728406>'),
            discord.SelectOption(label="Дебри",emoji='<:Wild:1140626637512245309>'),
            discord.SelectOption(label="Берег",emoji='<:Coast:1140626682483572736>'),
            discord.SelectOption(label="Дюна",emoji='<:Dune:1140626678780014592>'),
            discord.SelectOption(label="Искатель",emoji='<:Wayfinder:1140626640901246986>'),
            discord.SelectOption(label="Сборщик",emoji='<:Raiser:1140626670785667182>'),
            discord.SelectOption(label="Скульптор",emoji='<:Shaper:1140626664078983200> '),
            discord.SelectOption(label="Вождь",emoji='<:Host:1140626674002702376>'),
            discord.SelectOption(label="Хранитель",emoji='<:Ward:1140626643325562900>'),
            discord.SelectOption(label="Тишина",emoji='<:Silence:1140626659955974275> '),
            discord.SelectOption(label="Прилив",emoji='<:Tide:1140626648157388841> '),
            discord.SelectOption(label="Рыло",emoji='<:Snout:1140626655535177798>'),
            discord.SelectOption(label="Ребро",emoji='<:Rib:1140626669330235574> '),
            discord.SelectOption(label="Око",emoji='<:Oko:1140626676766740480> '),
            discord.SelectOption(label="Шпиль",emoji='<:Spire:1140626651252805633> ')
        ]
        super().__init__(placeholder="Выберите шаблон украшения ботинок", min_values=1, max_values=16, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenTrims
        chosenTrims[4] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[4] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения ботинок:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[4], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[4], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)

# Boots trim material
class SelectTrimMaterialBoots(discord.ui.Select):
    def __init__(self):
        options=[
            discord.SelectOption(label="Изумруд",emoji='<:Emerald:1140618895737241650>'),
            discord.SelectOption(label="Редстоун",emoji='<:Redstone_Dust:1140618892528590930>'),
            discord.SelectOption(label="Лазурит",emoji='<:Lapis_Lazuli:1140618881694707752>'),
            discord.SelectOption(label="Аметист",emoji='<:Amethyst_Shard:1140618890817310961>'),
            discord.SelectOption(label="Кварц",emoji='<:Nether_Quartz:1140618878775459851>'),
            discord.SelectOption(label="Незерит",emoji='<:Netherite_Ingot:1140595704293756938>'),
            discord.SelectOption(label="Алмаз",emoji='<:Diamond:1140600966752776213>'),
            discord.SelectOption(label="Золото",emoji='<:Gold_Ingot:1140618886350389319>'),
            discord.SelectOption(label="Железо",emoji='<:Iron_Ingot:1140618883611492453>'),
            discord.SelectOption(label="Медь",emoji='<:Copper_Ingot:1140618887868731503>')
        ]
        super().__init__(placeholder="Выберите материал украшения ботинок", min_values=1, max_values=10, options=options)

    async def callback(self, interaction:discord.Interaction):
        global chosenMaterials
        chosenMaterials[4] = valueLine(self.values)
        global trimsEnabled
        trimsEnabled[4] = True
        TurtlePatternEmbed = discord.Embed(title="Выбранные параметры украшения ботинок:", color=discord.Colour.from_str('0x2366c4'))
        TurtlePatternEmbed.add_field(name="Выбранный шаблон:", value=chosenTrims[4], inline=False)
        TurtlePatternEmbed.add_field(name="Выбранный материал:", value=chosenMaterials[4], inline=False)
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_response(embed=TurtlePatternEmbed)





# BUTTONS
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=modals#id1

# Main order menu
# When we press "Submit order" button, bot sends 3 messages with all information about order: 
# First message is sent in the "channel_orders" to the client
# Second message is sent to client's DM
# Third one is sent to the blacksmiths in the "channel_orerlist".
# Bot also saves id of response message and the user, that made the order in 2 lists (orderIDnumber and orderIDname).
# These two we will use to match user and his order later
class OrderSubmit(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Подтвердить заказ", custom_id="orderSubmit", emoji='✅', disabled=False)

    async def callback(self, interaction:discord.Interaction): 

        customerRole = get(interaction.user.guild.roles, name="Покупатель")
        await interaction.user.add_roles(customerRole)

        qp = 0
        noneSelected = True
        while qp < len(products):
            if products[qp] == True:
                noneSelected = False
            qp += 1
        
        if noneSelected == True:
            await interaction.response.send_message(embed=discord.Embed(title=":x: Вы не выбрали ни одного товара!", color=discord.Colour.from_str('0x2366c4')), ephemeral=True)
            print(interaction.user.name +" tried to make an empty order.")
            print("-------")
        else:
            print(interaction.user.name+" made a new order!")

        with open('setuporderinformation.txt',"r+") as getordernumber:
            OrderNumber = getordernumber.readlines()
        submitEmbed = discord.Embed(title="Ваш заказ составлен и отправлен кузнецам!", description="Cпасибо за вашу покупку! Когда ваш заказ будет готов, вам сообщат в личные сообщения.", color=discord.Colour.from_str('0x2366c4'))
        tinkerEmbed = discord.Embed(title=f'Заказ №{len(OrderNumber)+1}!', color=discord.Colour.from_str('0x2366c4'), description="Заказчик: "+interaction.user.mention)
        
        submitEmbed.add_field(name="Выбранные товары:", value=orderValues, inline=False)
        tinkerEmbed.add_field(name="Выбранные товары:", value=orderValues, inline=False)

        # The bot sends only those embed fields that the client used
        if netherite == True:
            submitEmbed.add_field(name="Из незерита будут сделаны:", value=netheriteValues, inline=False)
            tinkerEmbed.add_field(name="Из незерита должны быть сделаны:", value=netheriteValues, inline=False)
            print("Netherite ones: "+netheriteValues.__str__())
        
        
        if products[0] == True:
            submitEmbed.add_field(name="Зачарования трезубца:", value=enchants[0], inline=False)
            tinkerEmbed.add_field(name="Зачарования трезубца:", value=enchants[0], inline=False)
            print("Trident enchantments: "+enchants[0].__str__())
        if products[1]  == True:
            submitEmbed.add_field(name="Зачарования меча:", value=enchants[1], inline=False)
            tinkerEmbed.add_field(name="Зачарования меча:", value=enchants[1], inline=False)

            print("Sword enchantments: "+enchants[1].__str__())
        if products[2]  == True:
            submitEmbed.add_field(name="Зачарования арбалета:", value=enchants[2], inline=False)
            tinkerEmbed.add_field(name="Зачарования арбалета:", value=enchants[2], inline=False)
            print("Crossbow enchantments: "+enchants[2].__str__())
        if products[3]  == True:
            submitEmbed.add_field(name="Зачарования лука:", value=enchants[3], inline=False)
            tinkerEmbed.add_field(name="Зачарования лука:", value=enchants[3], inline=False)
            print("Bow enchantments: "+enchants[3].__str__())
        if products[4]  == True:
            submitEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
            tinkerEmbed.add_field(name="Зачарования топора:", value=enchants[4], inline=False)
            print("Axe enchantments: "+enchants[4].__str__())
        if products[5]  == True:
            submitEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
            tinkerEmbed.add_field(name="Зачарования кирки:", value=enchants[5], inline=False)
            print("Pickaxe enchantments: "+enchants[5].__str__())
        if products[6]  == True:
            submitEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
            tinkerEmbed.add_field(name="Зачарования лопаты:", value=enchants[6], inline=False)
            print("Shovel enchantments: "+enchants[6].__str__())
        if products[7]  == True:
            submitEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
            tinkerEmbed.add_field(name="Зачарования мотыги:", value=enchants[7], inline=False)
            print("Hoe enchantments: "+enchants[7].__str__())
        if products[8]  == True:
            submitEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)
            tinkerEmbed.add_field(name="Зачарования удочки:", value=enchants[8], inline=False)
            print("Fishing rod enchantments: "+enchants[8].__str__())
        if products[9]  == True:
            submitEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
            tinkerEmbed.add_field(name="Зачарования черепашьего панциря:", value=enchants[9], inline=False)
            print("Turtle helmet  enchantments: "+enchants[9].__str__())
        if products[10]  == True:
            submitEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
            tinkerEmbed.add_field(name="Зачарования шлема:", value=enchants[10], inline=False)
            print("Helmet enchantments: "+enchants[10].__str__())
        if products[11]  == True:
            submitEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
            tinkerEmbed.add_field(name="Зачарования нагрудника:", value=enchants[11], inline=False)
            print("Chestplate enchantments: "+enchants[11].__str__())
        if products[12]  == True:
            submitEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
            tinkerEmbed.add_field(name="Зачарования понож:", value=enchants[12], inline=False)
            print("Leggings enchantments: "+enchants[12].__str__())
        if products[13]  == True:
            submitEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
            tinkerEmbed.add_field(name="Зачарования ботинок:", value=enchants[13], inline=False)
            print("Boots enchantments: "+enchants[13].__str__())
        if products[14]  == True:
            submitEmbed.add_field(name="Зачарования зажигалки:", value=enchants[14], inline=False)
            tinkerEmbed.add_field(name="Зачарования зажигалки:", value=enchants[14], inline=False)
            print("Flint and steel enchantments: "+enchants[14].__str__())
        if products[15]  == True:
            submitEmbed.add_field(name="Зачарования щита:", value=enchants[15], inline=False)
            tinkerEmbed.add_field(name="Зачарования щита:", value=enchants[15], inline=False)
            print("Shield enchantments: "+enchants[15].__str__())
        if products[16]  == True:
            submitEmbed.add_field(name="Зачарования ножниц:", value=enchants[16], inline=False)
            tinkerEmbed.add_field(name="Зачарования ножниц:", value=enchants[16], inline=False)
            print("Scissors enchantments: "+enchants[16].__str__())
        
        if trimsEnabled[0] == True or trimsEnabled[1] == True or trimsEnabled[2] == True or trimsEnabled[3] == True or trimsEnabled[4] == True:
            trimsValue = ""
            if trimsEnabled[0] == True:
                trimsValue += "Украшения черепашьего панциря: "+ '\n'+ "Шаблон: "+chosenTrims[0]+", Материал: "+chosenMaterials[0]+ '\n'+ '\n'
            if trimsEnabled[1] == True:
                trimsValue += "Украшения шлема: "+ '\n'+ "Шаблон: "+chosenTrims[1]+", Материал: "+chosenMaterials[1]+ '\n'+ '\n'
            if trimsEnabled[2] == True:
                trimsValue += "Украшения нагрудника: "+ '\n'+ "Шаблон: "+chosenTrims[2]+", Материал: "+chosenMaterials[2]+ '\n'+ '\n'
            if trimsEnabled[3] == True:
                trimsValue += "Украшения понож: "+ '\n'+ "Шаблон: "+chosenTrims[3]+", Материал: "+chosenMaterials[3]+ '\n'+ '\n'
            if trimsEnabled[4] == True:
                trimsValue += "Украшения ботинок: "+ '\n'+ "Шаблон: "+chosenTrims[4]+", Материал: "+chosenMaterials[4]+ '\n'+ '\n'

            submitEmbed.add_field(name="Украшения брони:", value=trimsValue)
            tinkerEmbed.add_field(name="Украшения брони:", value=trimsValue)

        if orderCommentSubmit == True and noneSelected == False:
            submitEmbed.add_field(name="Ваш комментарий к заказу:", value=orderCommentValue, inline=False)
            tinkerEmbed.add_field(name="Комментарий к заказу:", value=orderCommentValue, inline=False)
            print("Customer's comment: "+orderCommentValue.__str__())

        global orderIDnumber
        global valueNumber
        global madeOrder
        if noneSelected == False:
            if madeOrder == False:
                print("-------")
                if valueNumber == 10:
                    valueNumber = 0

            
                await interaction.response.send_message(embed=submitEmbed, ephemeral=True)
                await interaction.user.send(embed=submitEmbed)
                message1 = await channel_orderlist_tinker.send(embed=tinkerEmbed)
                message2 = await channel_orderlist_tinker.send(view=OrderTinkerView())

                with open("setuporderinformation.txt","r+") as orderinformation:
                    orderInfo = orderinformation.readlines()
                    orderInfo.append(interaction.user.id.__str__()+" "+message1.id.__str__()+" "+ message2.id.__str__()+" 0"+'\n')

                    orderinformation.truncate(0)
                    orderinformation.seek(0)
                    orderinformation.writelines(orderInfo)

                timeoutTimer.cancel()
            
                orderIDnumber[valueNumber] = message2.id        # We also save the id of a message with which bot has responded and the user that made the order
                valueNumber += 1
        
                global makingOrder
                
                makingOrder = False
                madeOrder = True
            else:
                await interaction.response.send_message(embed=discord.Embed(title='Вы уже сделали заказ!',color=discord.Colour.from_str('0x2366c4')), ephemeral=True)


# Button to choose netherite ones if they are are needed
# This interaction responses with a embed and select menu (line 219)
class OrderNetherite(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Выбрать незеритовые аналоги", custom_id="orderNetherite",emoji='<:Netherite_Upgrade:1140599231355293766>')

    async def callback(self, interaction:discord.Interaction): 
        pq = 0
        noneSelected = True
        while pq < len(products):
            if products[pq] == True:
                noneSelected = False
            pq += 1
        
        if noneSelected == True:
            await interaction.response.send_message(embed=discord.Embed(title=":x: Вы не выбрали ни одного товара!", color=discord.Colour.from_str('0x2366c4')), ephemeral=True)
        else:
            embedNetherite = discord.Embed(title="Выберите товары, которые необходимо сделать из незерита!",color=discord.Colour.from_str('0x2366c4'))
            embedNetherite.add_field(name="Из незерита будут сделаны:",value="-",inline=False)  
            await interaction.response.send_message(embed=embedNetherite,view=OrderNetheriteView(), ephemeral=True)


# Button that let someone comment on his order
# This interaction responses with a modal where you can type your message (line 1204)
class OrderComment(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Добавить комментарий к заказу", custom_id="orderComment",emoji='💬')

    async def callback(self, interaction:discord.Interaction): 
        await interaction.response.send_modal(orderCommentModal())


# Menu, where someone can choose enchantments for his items
# This interaction responses with a embed and select menus in which you can choose enchantments for items you have chosen in first select (orderSelect)
# The bot sends the enchantment select menus only for those items that the user has selected in first select (orderSelect) (lines 407 - 934)
class SelectEnchantments(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Выбрать зачарования", custom_id="orderEnchantments",emoji='<:Enchanted_Book:1140597764326162503>')

    async def callback(self, interaction:discord.Interaction): 
        embedEnchantments= discord.Embed(title="Выберите зачарования товаров",color=discord.Colour.from_str('0x2366c4')) 
        embedEnchantments.add_field(name="***Предупреждение!***",value="***Имейте в виду, что многие зачарования конфликтуют друг с другом.*** Если в списке выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое конфликтующее зачарование! Помните, что вы можете расписать необходимые зачарования более подробно с помощью комментария к заказу.",inline=False)
        
        
        if products[0] == True or products[1]  == True or products[2]  == True or products[3]  == True or products[4]  == True or products[5]  == True or products[6]  == True or products[7]  == True or products[8]  == True or products[13]  == True or products[9]  == True or products[10]  == True or products[11]  == True or products[12]  == True or products[14]  == True or products[15]  == True or products[16]  == True:
            await interaction.response.send_message(embed=embedEnchantments, ephemeral=True)
        else:
            embedNone = discord.Embed(title=":x: Вы не выбрали ни одного товара!",color=discord.Colour.from_str('0x2366c4'))
            await interaction.response.send_message(embed=embedNone, ephemeral=True)

        # discord limits the amount of selects we can put in one view, so i had to make 4 different views and send them with 4 messages 
        # (I also divided items on weaponry, tools, armour and other)

        if products[0] == True or products[1]  == True or products[2]  == True or products[3]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView1(), ephemeral=True)

        if products[4]  == True or products[5]  == True or products[6]  == True or products[7]  == True or products[8]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView2(), ephemeral=True)

        if products[9]  == True or products[10]  == True or products[11]  == True or products[12]  == True or products[13]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView3(), ephemeral=True)

        if products[14]  == True or products[15]  == True or products[16]  == True:
            await interaction.followup.send(view=OrderEnchantmentsView4(), ephemeral=True)

# Menu, where someone can choose trims for his armour
# This interaction responses with a embed and select menus in which you can choose trims for his armour you have chosen in first select (orderSelect)
# The bot sends select menus only for those items that the user has selected in first select (orderSelect) (lines 407 - 934)
class SelectTrims(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Выбрать украшения брони",custom_id="orderTrims",emoji='<:Tide_Armor_Trim:1140599228025012346>')

    async def callback(self, interaction:discord.Interaction): 
        embedTrims= discord.Embed(title="Выберите украшения брони",color=discord.Colour.from_str('0x2366c4')) 
        embedTrims.add_field(name="***Предупреждение!***",value="***Имейте в виду, что к одному элементу брони нельзя применить несколько украшений.*** Если в списке выбраны несколько несовместимых позиций для товара, кузнец сделает по товару на каждое выбранное украшение!"+'\n'+" Помните, что вы можете расписать необходимые украшения более подробно с помощью комментария к заказу.",inline=False)
        embedTrims.add_field(name='Создайте свой уникальный дизайн!', value='Воспользуйтесь сайтом armortrims.com чтобы собрать свой сет или сгенерировать случайный, а потом выберите понравившиеся шаблоны и материалы в соответсвующих списках.')
        
        if products[9]  == True or products[10]  == True or products[11]  == True or products[12]  == True or products[13]  == True:
            await interaction.response.send_message(embed=embedTrims, ephemeral=True, view=SelectTrimsUrl())
        else:
            embedNone = discord.Embed(title=":x: Вы не выбрали ни одного элемента брони!",color=discord.Colour.from_str('0x2366c4'))
            await interaction.response.send_message(embed=embedNone, ephemeral=True)

        # I divided selects on each armour item
        if products[9] == True:
            await interaction.followup.send(view=OrderTrimsViewTurtle(), ephemeral=True)
        if products[10] == True:
            await interaction.followup.send(view=OrderTrimsViewHelmet(), ephemeral=True)
        if products[11] == True:
            await interaction.followup.send(view=OrderTrimsViewChastplate(), ephemeral=True)
        if products[12] == True:
            await interaction.followup.send(view=OrderTrimsViewLeggings(), ephemeral=True)
        if products[13] == True:
            await interaction.followup.send(view=OrderTrimsViewBoots(), ephemeral=True)


# Button for blacksmiths, to accept the order
class AcceptOrder(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.blurple, label="Принять заказ", custom_id="AcceptOrder")

    async def callback(self, interaction:discord.Interaction): 
        embedAccept = discord.Embed(title="Заказ принят",description="Заказ принял: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))

        await interaction.response.defer()
        getID = await interaction.original_response()

        
        with open("setuporderinformation.txt","r+") as orderinformation:
            orderInfo = orderinformation.readlines()
            orderInfoUserIDs = [0]
            orderInfoFirstmessageIDs = [0]
            orderInfoMessageIDs = [0]
            orderInfoMessageStatus = [0]
            n = 0
            spl = 0
            unsplit = 0
            while spl < len(orderInfo):
                orderInfoSplit = orderInfo[spl].split()
                if spl == 0:
                    orderInfoUserIDs[spl] = int(orderInfoSplit[0])
                    orderInfoFirstmessageIDs[spl] = int(orderInfoSplit[1])
                    orderInfoMessageIDs[spl] = int(orderInfoSplit[2])
                    orderInfoMessageStatus[spl] = int(orderInfoSplit[3])
                else:
                    orderInfoUserIDs.append(int(orderInfoSplit[0]))
                    orderInfoFirstmessageIDs.append(int(orderInfoSplit[1]))
                    orderInfoMessageIDs.append(int(orderInfoSplit[2]))
                    orderInfoMessageStatus.append(int(orderInfoSplit[3]))
                spl += 1

            while n < len(orderInfoMessageIDs):
                if getID.id == orderInfoMessageIDs[n]:
                    customer = client.get_user(orderInfoUserIDs[n])
                    await customer.send(embed=discord.Embed(title="Ваш заказ принят!",description="Кузнец: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4')))
                    print("Order id: "+orderInfoMessageIDs[n].__str__()+" accepted")
                    print("Customer: "+customer.name)
                    print("-------")
                    orderInfoMessageStatus[n] = 1
                n += 1
            
            while unsplit < len(orderInfo):
                orderInfoLine = orderInfoUserIDs[unsplit].__str__() + " "+ orderInfoFirstmessageIDs[unsplit].__str__()+" "+orderInfoMessageIDs[unsplit].__str__()+" "+orderInfoMessageStatus[unsplit].__str__()+'\n'
                orderInfo[unsplit] = orderInfoLine
                unsplit += 1
            
            orderinformation.truncate(0)
            orderinformation.seek(0)
            orderinformation.writelines(orderInfo)
        
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
        
        with open("setuporderinformation.txt","r+") as orderinformation:
            orderInfo = orderinformation.readlines()
            orderInfoUserIDs = [0]
            orderInfoFirstmessageIDs = [0]
            orderInfoMessageIDs = [0]
            orderInfoMessageStatus = [0]
            n = 0
            spl = 0
            unsplit = 0
            while spl < len(orderInfo):
                orderInfoSplit = orderInfo[spl].split()
                if spl == 0:
                    orderInfoUserIDs[spl] = int(orderInfoSplit[0])
                    orderInfoFirstmessageIDs[spl] = int(orderInfoSplit[1])
                    orderInfoMessageIDs[spl] = int(orderInfoSplit[2])
                    orderInfoMessageStatus[spl] = int(orderInfoSplit[3])
                else:
                    orderInfoUserIDs.append(int(orderInfoSplit[0]))
                    orderInfoFirstmessageIDs.append(int(orderInfoSplit[1]))
                    orderInfoMessageIDs.append(int(orderInfoSplit[2]))
                    orderInfoMessageStatus.append(int(orderInfoSplit[3]))
                spl += 1

            while n < len(orderInfoMessageIDs):
                if getID.id == orderInfoMessageIDs[n]:
                    customer = client.get_user(orderInfoUserIDs[n])
                    readyMessage = await customer.send(embed=discord.Embed(title="Ваш заказ готов!", color=discord.Colour.from_str('0x2366c4')),view=OrderPaybyCard())
                    orderInfoMessageStatus[n] = readyMessage.id
                    with open('customers.txt','r+') as customerlistReady:
                        CostContentReady = customerlistReady.readlines()
                        print(CostContentReady)
                        k = 0
                        while k < len(CostContentReady):
                            CostContentLineReady = CostContentReady[k]
                            CostContentValueReady = CostContentLineReady.split()

                            if CostContentValueReady[0] == customer.name:
                                t = 0
                                while t < len(orderIDnumber):
                                    if getID.id == orderIDnumber[t]:
                                        if orderIDcost[t] != 0:
                                            newPoints = int(CostContentValueReady[1]) + int(orderIDcost[t])
                                            CostContentReady[k] = customer.name+" "+newPoints.__str__()+"\n"
                                    t +=1
                            k += 1

                        print(CostContentReady)
                        customerlistReady.seek(0)
                        customerlistReady.writelines(CostContentReady)

                    
                    print("Order id:"+orderInfoMessageIDs[n].__str__()+" ready")
                    print("Customer: "+customer.name)
                    print("-------")
                    t = 0
                    while t < len(orderIDcost):
                        if getID.id == orderIDnumber[t]:
                            embedReady.add_field(name="Cтоимость:",value=orderIDcost[t].__str__()+".")
                        t += 1
                n += 1
            
            while unsplit < len(orderInfo):
                orderInfoLine = orderInfoUserIDs[unsplit].__str__() + " "+ orderInfoFirstmessageIDs[unsplit].__str__()+" "+orderInfoMessageIDs[unsplit].__str__()+" "+orderInfoMessageStatus[unsplit].__str__()+'\n'
                orderInfo[unsplit] = orderInfoLine
                unsplit += 1
            
            orderinformation.truncate(0)
            orderinformation.seek(0)
            orderinformation.writelines(orderInfo)
        
        await interaction.edit_original_response(embed=embedReady,view=None)

class PayByCard(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.url, label="Оплатить заказ с карты",url='https://plasmorp.com/bank?to_card={7862}&amount={1}&message={test}')

class SelectTrimsUrlButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.url, label="ArmorTrims",url='https://armortrims.com/?h=16:1:10&c=16:1:10&l=16:1:10&b=16:1:10')



# MODALS
# Modals are the things in discord API those let user type a message in special window 
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=modals#modal

# if someone wants to comment on his order, bot should show this modal  
class orderCommentModal(discord.ui.Modal, title="Добавьте комментарий к заказу!"):
    comment = discord.ui.TextInput(
        label="Опишите все необходимые подробности заказа.",
        style=discord.TextStyle.long,
        max_length=1024
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
        await interaction.response.send_message('Что-то пошло не так :face_with_diagonal_mouth:', ephemeral=True)


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
        
        with open("setuporderinformation.txt","r+") as orderinformation:
            orderInfo = orderinformation.readlines()
            orderInfoUserIDs = [0]
            orderInfoFirstmessageIDs = [0]
            orderInfoMessageIDs = [0]
            orderInfoMessageStatus = [0]
            n = 0
            spl = 0
            unsplit = 0
            while spl < len(orderInfo):
                orderInfoSplit = orderInfo[spl].split()
                if spl == 0:
                    orderInfoUserIDs[spl] = int(orderInfoSplit[0])
                    orderInfoFirstmessageIDs[spl] = int(orderInfoSplit[1])
                    orderInfoMessageIDs[spl] = int(orderInfoSplit[2])
                    orderInfoMessageStatus[spl] = int(orderInfoSplit[3])
                else:
                    orderInfoUserIDs.append(int(orderInfoSplit[0]))
                    orderInfoFirstmessageIDs.append(int(orderInfoSplit[1]))
                    orderInfoMessageIDs.append(int(orderInfoSplit[2]))
                    orderInfoMessageStatus.append(int(orderInfoSplit[3]))
                spl += 1

        
            while n < len(orderInfoMessageIDs):
                if getID.id == orderInfoMessageIDs[n]:
                    customer = client.get_user(orderInfoUserIDs[n])
                    await customer.send(embed=embedReject)
                    orderInfoMessageStatus[n] = 4
                    print("Order id: "+orderInfoMessageIDs[n].__str__()+" rejected")
                    print("Customer: "+customer.name)
                    print("Reason: "+orderRejectValue.__str__())
                    print("Rejector: "+ interaction.user.name)
                    print("-------")

                n += 1
            
            while unsplit < len(orderInfo):
                orderInfoLine = orderInfoUserIDs[unsplit].__str__() + " "+ orderInfoFirstmessageIDs[unsplit].__str__()+" "+orderInfoMessageIDs[unsplit].__str__()+" "+orderInfoMessageStatus[unsplit].__str__()+'\n'
                orderInfo[unsplit] = orderInfoLine
                unsplit += 1
            
            orderinformation.truncate(0)
            orderinformation.seek(0)
            orderinformation.writelines(orderInfo)

        
        await interaction.edit_original_response(embed=embedReject,view=OrderTinkerViewRejected())
    
    #I sometimes get errors with modals, so i have to put some error handeling here
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)


        traceback.print_exception(type(error), error, error.__traceback__)

# Ahh, I should update this comment but i'm too lazy, sorry
# Here is a modal, where blacksmith types cost of the order without any discounts
# The bot opens "customers.txt" file, where it gets a list with usersnames of customers and their points
# After that, the bot splits this list into required elements:
# CostContent ['name1 points1','name2 points2'] --> CostContentLine = "name1 points1" --> CostContentValue ['name1','points1']
# After that, bot compares 'name1' value with names from OrderIDname list 
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

        with open("setuporderinformation.txt","r+") as orderinformation:
            orderInfo = orderinformation.readlines()
            orderInfoUserIDs = [0]
            orderInfoFirstmessageIDs = [0]
            orderInfoMessageIDs = [0]
            orderInfoMessageStatus = [0]
            n = 0
            spl = 0
            unsplit = 0
            while spl < len(orderInfo):
                orderInfoSplit = orderInfo[spl].split()
                if spl == 0:
                    orderInfoUserIDs[spl] = int(orderInfoSplit[0])
                    orderInfoFirstmessageIDs[spl] = int(orderInfoSplit[1])
                    orderInfoMessageIDs[spl] = int(orderInfoSplit[2])
                    orderInfoMessageStatus[spl] = int(orderInfoSplit[3])
                else:
                    orderInfoUserIDs.append(int(orderInfoSplit[0]))
                    orderInfoFirstmessageIDs.append(int(orderInfoSplit[1]))
                    orderInfoMessageIDs.append(int(orderInfoSplit[2]))
                    orderInfoMessageStatus.append(int(orderInfoSplit[3]))
                spl += 1

            while n < len(orderInfoMessageIDs):
                if getID.id == orderInfoMessageIDs[n]:
                    CostUser = client.get_user(orderInfoUserIDs[n])
                    CostMember = get(client.get_all_members(), id=orderInfoUserIDs[n])
                    orderInfoMessageStatus[n] = 2

                    print(f'Cost of order (ID {orderInfoMessageIDs[n]}) was set')
                    print("Customer: "+CostMember.name)
                n += 1
            
            while unsplit < len(orderInfo):
                orderInfoLine = orderInfoUserIDs[unsplit].__str__() + " "+ orderInfoFirstmessageIDs[unsplit].__str__()+" "+orderInfoMessageIDs[unsplit].__str__()+" "+orderInfoMessageStatus[unsplit].__str__()+'\n'
                orderInfo[unsplit] = orderInfoLine
                unsplit += 1
            
            orderinformation.truncate(0)
            orderinformation.seek(0)
            orderinformation.writelines(orderInfo)



        with open('customers.txt','r+') as customerlist:
            CostContent = customerlist.readlines()
            k = 0
            foundUser = False
            while k < len(CostContent):
                CostContentLine = CostContent[k]
                CostContentValue = CostContentLine.split()
            
                if CostContentValue[0] == CostUser.name:
                    foundUser = True
                    setCustomerPoints = int(CostContentValue[1])
                    customerPoints = int(CostContentValue[1])
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

            if foundUser == False:        
                CostContent.append(CostUser.name+" 0\n")
                customerlist.seek(0)
                customerlist.writelines(CostContent)
                customerPoints = 0
                setCustomerPoints = 0
                orderCost_withDiscount = orderCost
                
                   

        setCustomerPoints += orderCost_withDiscount

        embedCost = discord.Embed(title="Заказ принят",description="Заказ принял: "+interaction.user.mention, color=discord.Colour.from_str('0x2366c4'))
        embedCost.add_field(name="Стоимость без учёта скидки:", value=orderCost.__str__()+ " алмазов")
        embedCost.add_field(name="Стоимость c учётом скидки:",value=orderCost_withDiscount.__str__()+" алмазов")

        if customerPoints < 150 and setCustomerPoints >= 150 and setCustomerPoints < 200:
            await CostMember.add_roles(DiscountRole_1)
            embedCost.add_field(name=CostUser.name+" получает роль "+DiscountRole_1.name,value="Всего "+CostUser.name+" потратил в кузне "+ setCustomerPoints.__str__()+" алмазов.",inline=False)

        elif customerPoints < 200 and setCustomerPoints >= 200 and setCustomerPoints < 300:
            await CostMember.add_roles(DiscountRole_2)
            embedCost.add_field(name=CostUser.name+" получает роль "+DiscountRole_2.name,value="Всего "+CostUser.name+" потратил в кузне "+ setCustomerPoints.__str__()+" алмазов.",inline=False)

        elif customerPoints < 300 and setCustomerPoints >= 300 and setCustomerPoints < 450:
            await CostMember.add_roles(DiscountRole_3)
            embedCost.add_field(name=CostUser.name+" получает роль "+DiscountRole_3.name,value="Всего "+CostUser.name+" потратил в кузне "+ setCustomerPoints.__str__()+" алмазов.",inline=False)

        elif customerPoints < 450 and setCustomerPoints >= 450 and setCustomerPoints < 600:
            await CostMember.add_roles(DiscountRole_4)
            embedCost.add_field(name=CostUser.name+" получает роль "+DiscountRole_4.name,value="Всего "+CostUser.name+" потратил в кузне "+ setCustomerPoints.__str__()+" алмазов.",inline=False)

        elif customerPoints < 600 and setCustomerPoints >= 600:
            await CostMember.add_roles(DiscountRole_5)
            embedCost.add_field(name=CostUser.name+" получает роль "+DiscountRole_5.name,value="Всего "+CostUser.name+" потратил в кузне "+ setCustomerPoints.__str__()+" алмазов.",inline=False)

        global orderIDcost

        n = 0
        with open('last10costsNpoints.txt',"r+") as costsandnumbers:
            CostsPoints = costsandnumbers.readlines()
            while n < len(orderIDnumber):
                if getID.id == orderIDnumber[n]:
                    orderIDcost[n] = orderCost_withDiscount
                    CostsPoints[n] = orderCost_withDiscount.__str__() + " " + orderIDnumber[n].__str__()+'\n'
                n += 1
            costsandnumbers.truncate(0)
            costsandnumbers.seek(0)
            costsandnumbers.writelines(CostsPoints)

        print('Cost: '+ orderCost_withDiscount.__str__())
        print("Last orders' costs: "+orderIDcost.__str__())
        print("-------")
  
        await interaction.edit_original_response(embed=embedCost)
        await CostUser.send(embed=discord.Embed(title="Стоимость вашего заказа с учётом скидки: " +orderCost_withDiscount.__str__()+ " алмазов.", color=discord.Colour.from_str('0x2366c4')))






# VIEWS
# https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=view#discord.ui.View

# View with button that helps user start ordering
class OrderButtonView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(StartOrder())

# View with main order menu buttons
class OrderView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(OrderSelect())
        self.add_item(SelectEnchantments())
        self.add_item(OrderNetherite())
        self.add_item(SelectTrims())
        self.add_item(OrderComment())
        self.add_item(OrderSubmit())
        
# View that contains a select menu that is sent to user if netherite analogs are needed
class OrderNetheriteView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(OrderSelectNetherite())

# View that contains a modal that is sent to user if he wants to comment on his order
class OrderCommentView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(OrderComment())

# Views with menus, where someone can choose enchantments for his items
# Discord limits the amount of selects we can put in one view, so i had to make 4 different views and send them with 4 messages 
# (I also divided items on weaponry, tools, armour and other)
class OrderEnchantmentsView1(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if products[0] == True:
            self.add_item(SelectTrezubEnchantments())
        if products[1]  == True:
            self.add_item(SelectSwordEnchantments())
        if products[2]  == True:
            self.add_item(SelectCrossbowEnchantments())
        if products[3]  == True:
            self.add_item(SelectBowEnchantments())
        
class OrderEnchantmentsView2(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if products[4]  == True:
            self.add_item(SelectAxeEnchantments())
        if products[5]  == True:
            self.add_item(SelectPickaxeEnchantments())
        if products[6]  == True:
            self.add_item(SelectShovelEnchantments())
        if products[7]  == True:
            self.add_item(SelectHoeEnchantments())
        if products[8]  == True:
            self.add_item(SelectFishingRodEnchantments())
        
class OrderEnchantmentsView3(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if products[9]  == True:
            self.add_item(SelectTurtleEnchantments())
        if products[10]  == True:
            self.add_item(SelectHelmetEnchantments())
        if products[11]  == True:
            self.add_item(SelectChestplateEnchantments())
        if products[12]  == True:
            self.add_item(SelectLeggingsEnchantments())
        if products[13]  == True:
            self.add_item(SelectBootsEnchantments())

class OrderEnchantmentsView4(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        if products[14]  == True:
            self.add_item(SelectFlintNsteelEnchantments())
        if products[15]  == True:
            self.add_item(SelectShieldEnchantments())
        if products[16]  == True:
            self.add_item(SelectScissorsEnchantments())

# Views with menus where someone can choose armour decoration
# I made a view for every armour item so we can get information separately
# Each view contains 2 selection menu, first one let user choose trim pattern, second one - trim material 
# I also had to make 2 selection menus for every armour item so we can get results properly
class OrderTrimsViewTurtle(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)

        self.add_item(SelectTrimPatternTurtle())
        self.add_item(SelectTrimMaterialTurtle())

class OrderTrimsViewHelmet(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)

        self.add_item(SelectTrimPatternHelmet())
        self.add_item(SelectTrimMaterialHelmet())

class OrderTrimsViewChastplate(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)

        self.add_item(SelectTrimPatternChestplate())
        self.add_item(SelectTrimMaterialChestplate())

class OrderTrimsViewLeggings(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)

        self.add_item(SelectTrimPatternLeggings())
        self.add_item(SelectTrimMaterialLeggings())

class OrderTrimsViewBoots(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)

        self.add_item(SelectTrimPatternBoots())
        self.add_item(SelectTrimMaterialBoots())

# View with 2 buttons for blacksmith (accept order or reject order)
class OrderTinkerView(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(AcceptOrder())
        self.add_item(RejectOrder())   

# Another view with 3 buttons for blacksmith (tell customer cost of his order, tell customer that his order is ready or reject customer's order)
class OrderTinkerViewAccepted(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(ReadyOrder())
        self.add_item(OrderCost())
        self.add_item(RejectOrder())    

# Another view with "accept order" button for blacksmith (if the order is rejected earlier)
class OrderTinkerViewRejected(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(AcceptOrder())

# Another view with nothing in it to send if the order is ready (we need this only to not get any errors while setupping)
class OrderTinkerViewReady(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        
class OrderPaybyCard(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(PayByCard())

class SelectTrimsUrl(discord.ui.View):
    def __init__(self, timeout = None):
        super().__init__(timeout=timeout)
        self.add_item(SelectTrimsUrlButton())


client.run("your token here")