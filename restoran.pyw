# coding=utf-8
'''
@author: Milan
'''

import sys
from PyQt4 import QtGui, QtCore, Qt, QtSql
from windows import *
from base import Article, Transaction, User


inactivity_timeout=1 #dali da ima log

def d2u(text):
    "konverzija vo UTF-8"
    return text.decode('utf-8')

class MainWindow(QtGui.QMainWindow):
    def __init__(self,Parent=None):
        QtGui.QMainWindow.__init__(self,Parent)
        self.setWindowTitle(d2u("Ресторан"))
        self.setWindowIcon(QtGui.QIcon("static/icons/Restoran.ico"))
        
        self.DatabaseName = "Base.adb"
        self.Database = QtSql.QSqlDatabase.addDatabase("QSQLITE");
        self.User = '' #koj korisnik e najaven

        self.CreateCentralWidget()
        self.CreateActions()
        self.CreateToolbar()
        #self.CreateMenu()
        self.DatabaseDefaultOpen()

        if (inactivity_timeout): 
            self.event_filter = InactivityFilter()
            QtCore.QCoreApplication.instance().installEventFilter(self.event_filter)
            self.connect(self.event_filter, QtCore.SIGNAL("timeout()"), self.TriggeredTimeOut)
        else:
            self.event_filter = None
        
        #self.TriggeredTimeOut() #da se prikaze log-screen na prvoto vklucuvanje

    def CreateCentralWidget(self):
        LayoutCentral = QtGui.QVBoxLayout()
        font = QtGui.QFont('verdana', 9)

        #DRVO na aktivni naracki
        self.ListaNaracki = QtGui.QTreeWidget()
        self.ListaNaracki.setColumnCount(4)
        self.ListaNaracki.setFont(font)
        self.ListaNaracki.setHeaderLabels([d2u('Нарачкa'),d2u('бр.Сметка'),d2u('Време'),d2u('Датум')])
        self.ListaNaracki.setSortingEnabled(True)
        #self.ListaNaracki.hideColumn(1)
        self.ListaNaracki.setColumnWidth(2, 80)
        self.ListaNaracki.setColumnWidth(3, 80)
        self.ListaNaracki.header().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.connect(self.ListaNaracki,QtCore.SIGNAL("itemSelectionChanged()"),self.TriggeredTreeSelection)

        #DRVO na artikli
        self.TreeArticleList = QtGui.QTreeWidget()
        self.TreeArticleList.setHeaderLabel(d2u("Мени"))
        self.TreeArticleList.setSortingEnabled(True)
        self.TreeArticleList.setFont(font)
        self.TreeArticleList.setColumnCount(6)
        self.TreeArticleList.sortByColumn(0,Qt.Qt.AscendingOrder)
        self.TreeArticleList.hideColumn(1) #ID
        self.TreeArticleList.hideColumn(2) #Parent
        self.TreeArticleList.hideColumn(3) #Name
        self.TreeArticleList.hideColumn(4) #Price
        self.TreeArticleList.hideColumn(5) #Tax
        self.TreeArticleList.doubleClicked.connect(self.TriggeredTableAdd)
        
        #TABELA za prikaz na aktivna narackata
        self.TableNarackaPrikaz = QtGui.QTableWidget()
        self.TableNarackaPrikaz.setColumnCount(4)
        self.TableNarackaPrikaz.horizontalHeader().setFont(font)
        self.TableNarackaPrikaz.setHorizontalHeaderLabels([d2u("Артикл"),d2u("Цена"),d2u("Количина"),d2u("Вкупно")])
        self.TableNarackaPrikaz.setRowCount(0)
        self.TableNarackaPrikaz.verticalHeader().setVisible(False)
        self.TableNarackaPrikaz.setColumnWidth(1,80)
        self.TableNarackaPrikaz.setColumnWidth(2,80)
        self.TableNarackaPrikaz.setColumnWidth(3,80)
        self.TableNarackaPrikaz.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        
        #TABELA za kreiranje nova naracka
        self.TableNaracka = QtGui.QTableWidget()
        self.TableNaracka.setColumnCount(4)
        self.TableNaracka.horizontalHeader().setFont(font)
        self.TableNaracka.setHorizontalHeaderLabels([d2u("Артикл"),d2u("Цена"),d2u("Данок"),d2u("Количина")])
        self.TableNaracka.setRowCount(0)
        self.TableNaracka.verticalHeader().setVisible(False)
        self.TableNaracka.setColumnWidth(3,80)
        self.TableNaracka.setColumnHidden(1, True)
        self.TableNaracka.setColumnHidden(2, True)
        self.TableNaracka.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)

        #DISPLEJ za vkupen iznos na smetka
        self.LCDNumberSum = QtGui.QLCDNumber()
        self.LCDNumberSum.setSegmentStyle(2)
        self.LCDNumberSum.setFixedHeight(35)
        #self.LCDNumberSum.setFixedWidth(130)
        self.LCDNumberSum.setObjectName('LCD')

        #Labela za ime na firma
        self.LabelFirm = QtGui.QLabel(d2u("Име на фирма"))
        self.LabelFirm.setAlignment(QtCore.Qt.AlignRight)
        self.LabelFirm.setObjectName('Firma')

        #Labela za prikaz na aktiven korisnik
        self.LabelUser = QtGui.QLabel()
        self.LabelUser.setAlignment(QtCore.Qt.AlignRight)
        self.LabelUser.setObjectName('User')

        #Labela za prikazuvanje na greski
        self.LabelError = QtGui.QLabel("")
        self.LabelError.hide()
        self.LabelError.setObjectName('Error')
       
        #BUTTONS naracaj, komentar
        self.ButtonNaracaj = QtGui.QPushButton(d2u("Нарачај"))
        self.connect(self.ButtonNaracaj,QtCore.SIGNAL("clicked()"),self.OrderClicked)
        self.ButtonIzbrisi = QtGui.QPushButton(d2u("Избриши"))
        self.connect(self.ButtonIzbrisi,QtCore.SIGNAL("clicked()"),self.ClearClicked)
        self.TextComment  = QtGui.QLineEdit()
        self.TextComment.setFixedWidth(30)

        #layout
        HeaderLeft = QtGui.QVBoxLayout()
        HeaderLeft.addWidget(self.LabelFirm)
        HeaderLeft.addWidget(self.LabelUser)

        Header = QtGui.QHBoxLayout()
        Header.addLayout(HeaderLeft)

        MakeTransaction = QtGui.QHBoxLayout()
        MakeTransactionRight = QtGui.QHBoxLayout()
        MakeTransactionRight.addStretch()
        MakeTransactionRight.addWidget(QtGui.QLabel(d2u("Маса број: ")))
        MakeTransactionRight.addWidget(self.TextComment)
        MakeTransactionRight.addWidget(self.ButtonNaracaj)
        MakeTransactionRight.addWidget(self.ButtonIzbrisi)
        MakeTransaction.addWidget(self.LabelError)
        MakeTransaction.addLayout(MakeTransactionRight)

        #groups
        self.GroupBoxActive = QtGui.QGroupBox(d2u('АКТИВНИ НАРАЧКИ'))
        Active = QtGui.QHBoxLayout()
        ActiveRight = QtGui.QVBoxLayout()
        ActiveRight.addWidget(self.LCDNumberSum)
        ActiveRight.addWidget(self.TableNarackaPrikaz)
        Active.addWidget(self.ListaNaracki)
        Active.addLayout(ActiveRight)
        self.GroupBoxActive.setLayout(Active)
        self.GroupBoxActive.setObjectName('Active')
        
        self.GroupBoxNew = QtGui.QGroupBox(d2u('НОВА НАРАЧКА'))
        New = QtGui.QVBoxLayout()
        NewTables = QtGui.QHBoxLayout()
        NewTables.addWidget(self.TreeArticleList)
        NewTables.addWidget(self.TableNaracka)
        New.addLayout(NewTables)
        New.addLayout(MakeTransaction)
        self.GroupBoxNew.setLayout(New)
        self.GroupBoxNew.setObjectName('New')
     
        LayoutCentral.addLayout(Header)
        LayoutCentral.addWidget(self.GroupBoxActive)
        LayoutCentral.addWidget(self.GroupBoxNew)

        CentralWidget = QtGui.QWidget()
        CentralWidget.setLayout(LayoutCentral)
        CentralWidget.setObjectName('Central')
        self.setCentralWidget(CentralWidget)

    def OrderClicked(self):
        """
        * Ja zapisuva vnesenata naracka vo bazanite tabeli Active i Trans
        
        * Avtomatski generira broj na smetka 
        
        * Azurira prikaz na aktivni transakcii
        """
        if self.TextComment.text(): #ako e vnesen brojot na masa
            Query = self.Database.exec_("SELECT * FROM Trans")
            if Query.last(): # posledna naracka
                self.CountNumber = Query.value(6).toInt()[0] + 1 # broj na nova smetka
            else: #prva naracka
                self.CountNumber = 1

            quantity_valid=True
            for i in range(self.TableNaracka.rowCount()): #dali ima vneseno kolicina vo site polinja od tabelata
                if not self.TableNaracka.item(i,3): 
                    quantity_valid=False

            if quantity_valid and self.TableNaracka.rowCount(): #ako za sekoj artikl ima vneseno kolicina
                for i in range(self.TableNaracka.rowCount()):
                    self.myTransaction = Transaction()
                    self.myTransaction.Type  = unicode(QtCore.QString(d2u('материјално')))
                    self.myTransaction.Name  = unicode(self.TableNaracka.item(i,0).text())
                    self.myTransaction.Price = unicode(self.TableNaracka.item(i,1).text())
                    self.myTransaction.Tax   = unicode(self.TableNaracka.item(i,2).text())
                    self.myTransaction.Quantity = unicode(self.TableNaracka.item(i,3).text())
                    self.myTransaction.Count = unicode(QtCore.QString(str(self.CountNumber)))
                    self.myTransaction.Comment = unicode(self.TextComment.text())
                    self.myTransaction.Waiter = unicode(self.User)

                    #zapisuvanje vo dvete tabeli
                    self.DatabaseActiveTransactionAdd(self.myTransaction)
                    self.DatabaseTransactionAdd(self.myTransaction)

                self.TableClear()
                #azurira drvo na aktivni naracki
                Comment = d2u("Маса број: %s") % self.TextComment.text()
                Date = unicode(QtCore.QDate.currentDate().toPyDate().strftime('%Y-%m-%d'))
                Time = unicode(QtCore.QTime.currentTime().toPyTime().strftime('%H:%M:%S')) 
                lista=[Comment, unicode(self.CountNumber),Time,Date]

                QtGui.QTreeWidgetItem(self.ListaNaracki,lista)
                self.TextComment.clear()
                self.LabelError.hide()
            else:
                self.LabelError.setText(d2u("ГРЕШКА: НЕМАТЕ ВНЕСЕНО КОЛИЧИНА НА АРТИКЛ"))
                self.LabelError.show()

        else:
            self.LabelError.setText(d2u("ГРЕШКА: НЕМАТЕ ВНЕСЕНО БРОЈ НА МАСА"))
            self.LabelError.show()

    def ClearClicked(self):
        self.TableClear()

#------------------------------- /Akcii ----------------------------------------

    def CreateAction(self,text,slot=None,shortcut=None,icon=None,tip=None,checkable=False,signal="triggered()"):
        action=QtGui.QAction(text,self)
        if icon is not None:
            action.setIcon(QtGui.QIcon("%s.ico"%icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action,QtCore.SIGNAL(signal),slot)
        if checkable:
            action.setCheckable(True)
        return action
    
    def CreateActions(self):
        self.ActionDatabaseNew = self.CreateAction("Nova Baza...",self.TriggeredDatabaseNew,"Ctrl+T","static/icons/New",d2u("Направи нова база"))
        self.ActionDatabaseOpen = self.CreateAction("Otvori Basa...",self.TriggeredDatabaseOpen,"Ctrl+O","static/icons/Open",d2u("Отвори постоечка база"))
        self.ActionArticleAdd = self.CreateAction("Vnesi Artikl...",self.TriggeredArticleAdd,"Ctrl+A","static/icons/Add",d2u("Внеси артикл"))
        self.ActionArticleEdit = self.CreateAction("Promeni Artikl...",self.TriggeredArticleEdit,"Ctrl+E","static/icons/Edit",d2u("Промени артикл"))
        self.ActionArticleDelete = self.CreateAction("Izbrisi Artikl",self.TriggeredArticleDelete,"Ctrl+D","static/icons/Delete",d2u("Избриши артикл"))
        
        self.ActionUsers = self.CreateAction("Korisnici", self.TriggeredUsers,"Ctrl+U", "static/icons/User",d2u("Корисници"))
        self.ActionDailyReport = self.CreateAction("Dneven Izvestaj", self.TriggeredDailyReport,"F9","static/icons/Report",d2u("Дневен извештај (F9)"))
        self.ActionMakePaymant = self.CreateAction("Naplati", self.TriggeredMakePaymant,"F5","static/icons/Check", d2u("Наплати (F5)"))
        self.ActionExit = self.CreateAction("Izlez",self.TriggeredExit,"Esc","static/icons/Exit",d2u("Излез (Esc)"))

        self.UpdateActionStatus()

    #koga da bidat ovozmozeni klikovite
    def UpdateActionStatus(self):
        self.ActionDatabaseNew.setEnabled(self.User == 'admin')
        self.ActionDatabaseOpen.setEnabled(self.User == 'admin')
        self.ActionArticleAdd.setEnabled(self.Database.isOpen() and self.User == 'admin') 
        self.ActionArticleEdit.setEnabled(self.Database.isOpen() and self.User == 'admin')
        self.ActionArticleDelete.setEnabled(self.Database.isOpen() and self.User == 'admin')
        self.ActionUsers.setEnabled(self.User == 'admin')

    def CreateToolbar(self):
        Toolbar = QtGui.QToolBar()
        Toolbar.addAction(self.ActionDatabaseNew)
        Toolbar.addAction(self.ActionDatabaseOpen)
        Toolbar.addSeparator()
        Toolbar.addAction(self.ActionArticleAdd)
        Toolbar.addAction(self.ActionArticleEdit)
        Toolbar.addAction(self.ActionArticleDelete)
        Toolbar.addSeparator()
        Toolbar.addAction(self.ActionUsers)
        Toolbar.addAction(self.ActionMakePaymant)
        Toolbar.addAction(self.ActionDailyReport)
        Toolbar.addSeparator()
        Toolbar.addAction(self.ActionExit)

        self.addToolBar(Toolbar)

#------------------------------- /Trigeri ----------------------------------------

    def TriggeredDatabaseNew(self):
        self.DatabaseNew()

    def TriggeredDatabaseOpen(self):
        self.DatabaseOpen()

    def TriggeredArticleAdd(self):
        AddArticleDialog = AddEditArticle(self)
        if AddArticleDialog.exec_():
            ID = self.DatabaseArticleAdd(AddArticleDialog.myArticle)                                   
            AddArticleDialog.myArticle.ID=ID
            self.TreeArticleAdd(AddArticleDialog.myArticle)
        
    def TriggeredArticleEdit(self):
        EditArticleDialog = AddEditArticle(self,Article([self.TreeArticleList.selectedItems()[0].text(i) for i in range(1,7)]))
        if EditArticleDialog.exec_():
            SelectedItem=self.TreeArticleList.selectedItems()[0]
            ArticlesToEdit=[]
            for ChildIndex in range(SelectedItem.childCount()): #ako editira Root
                ChildArticle=Article([self.TreeArticleList.selectedItems()[0].child(ChildIndex).text(i) for i in range(1,7)])
                if EditArticleDialog.myArticle.Parent!="0":
                    ChildArticle.Parent=EditArticleDialog.myArticle.Parent
                ArticlesToEdit.append(ChildArticle)
            ArticlesToEdit.append(EditArticleDialog.myArticle)
            for aArticle in ArticlesToEdit:
                self.DatabaseArticleEdit(aArticle)
                self.TreeArticleEdit(aArticle)
    
    def TriggeredArticleDelete(self):
        DeleteConfirmBox = QtGui.QMessageBox(self)
        DeleteConfirmBox.setIcon(QtGui.QMessageBox.Warning)
        DeleteConfirmBox.setWindowTitle(d2u("Избриши артикл"))
        DeleteConfirmBox.setWindowIcon(QtGui.QIcon("static/icons/Delete.ico"))
        DeleteConfirmBox.setText(d2u("Дали сакате да го избришете селектираниот артикл?"))
        DeleteConfirmBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        #print [self.TreeArticleList.selectedItems()[0].text(i) for i in range(1,6)]
        if DeleteConfirmBox.exec_()==QtGui.QMessageBox.Ok:
            self.TableClear()
            self.DatabaseArticleDelete(Article([self.TreeArticleList.selectedItems()[0].text(i) for i in range(1,6)]))
            # DeleteFromTree?
            self.TreeArticleDelete(Article([self.TreeArticleList.selectedItems()[0].text(i) for i in range(1,6)]))

    def TriggeredTreeSelection(self):
        if self.ListaNaracki.selectedItems():
            self.InfoUpdate()        

    def TriggeredTableAdd(self):
        """
        * Pri dvoen klik na artikl od drvoto go dodava vo tabela za naracka
        """
        self.UpdateActionStatus()
        if int(self.TreeArticleList.selectedItems()[0].text(2)): #onevozmozi root
            self.TableAdd()

    def TriggeredExit(self):
        self.DatabaseClose()
        self.close()

    def TriggeredTimeOut(self):
        """
        * Ako korisnikot nema aktivnost vo predefiniranoto vreme
          se pojavuva prozorecot za najavuvanje.
        
        * Najaveniot korisnik se zacuvuva vo promenlivata self.User
        """
        self.disconnect(self.event_filter, QtCore.SIGNAL("timeout()"), self.TriggeredTimeOut)  
        users = self.DatabaseGetUsers()
        Log = Login(self,users)
        Log.showFullScreen()
        if Log.exec_():
            self.User = Log.Name
            self.LabelUser.setText(d2u('Активен корисник: %s') % self.User)
            self.connect(self.event_filter, QtCore.SIGNAL("timeout()"), self.TriggeredTimeOut)
            self.UpdateActionStatus()

    def TriggeredMakePaymant(self):
        """
        * Brise selektiranata masa od aktivni transakcii

        * Azurira tabelata

        * TODO: funkcija za pecatenje preku fiskalna kasa
        """
        if(self.ListaNaracki.selectedItems()):
            count = self.ListaNaracki.selectedItems()[0].text(1)
            self.DatabaseActiveTransactionDelete(count)
            self.TreeActiveTransactionPopulate()
            self.TableNarackaClear()
            self.LabelError.hide()
        else:
            self.LabelError.setText(d2u("ГРЕШКА: НЕМАТЕ СЕЛЕКТИРАНО МАСА"))
            self.LabelError.show()

    def TriggeredDailyReport(self):
        """
        * Prikazuva dneven izvestaj za selektiraniot den od kalendarot
        
        * TODO: zacuvuvanje vo PDF ili EXCEL file
        """
        Calendar = CalendarDialog(self)
        if Calendar.exec_():
            date = Calendar.selectedDate.toPyDate()
            Query = self.Database.exec_("SELECT * FROM Trans WHERE date_created='%s'" % str(date))
            counts={}   #key: broj_na_smetka ; value: iznos
            articles={} #key: artikl; value: [iznos, edinecna cena na artikl]
            while Query.next():
                name  = unicode(str(Query.value(2).toString().toUtf8()),"utf-8")
                #print name,type(name)
                price = Query.value(3).toInt()[0]
                quantity = Query.value(5).toInt()[0]
                count = str(Query.value(6).toString())
                #print name,price,quantity,count
                if count not in counts:
                    counts[count] = quantity * price
                elif count in counts:
                    counts[count] = counts.get(count) + quantity * price
                if name not in articles:
                    articles[name] = [quantity * price, price]
                elif name in articles:
                    articles[name][0] = articles.get(name)[0] + quantity * price
            
        counts[u"Вкупно".encode("utf-8")] = str(sum(counts.values()))
        DailyReport = DailyReportDialog(self,counts,articles)
        DailyReport.show()
        if DailyReport.exec_():
            pass
 
    def TriggeredUsers(self):
        """
        * Dodava ili brise korisnik od baznata tabela Users
        """
        Query = self.Database.exec_("SELECT * FROM Users")
        Users = UsersDialog(self,Query)
        if Users.exec_():
            if Users.delete:
                self.DatabaseUserDelete(Users.User.Name)
            if Users.sign:
                if self.DatabaseUserExist(Users.User.Name):
                    QtGui.QMessageBox.warning(
                    self, d2u('Грешка'), d2u('Корисникот веќе постои'))
                else:
                    self.DatabaseUserAdd(Users.User)

#------------------------------- /Bazi ----------------------------------------

    def DatabaseDefaultOpen(self):
        if self.DatabaseName == 'Base.adb':
            self.DatabaseConnect()

    def DatabaseNew(self):
        self.DatabaseName = unicode(QtGui.QFileDialog.getSaveFileName(self,"New Database",".","Milan Databases (*.adb)"))
        if self.DatabaseName:
            self.DatabaseCreate()
        else:
            pass # Cancel
    
    def DatabaseOpen(self):
        self.DatabaseName = unicode(QtGui.QFileDialog.getOpenFileName(self,"Open Database",".","Milan Databases (*.adb)"))
        if self.DatabaseName:
            self.DatabaseConnect()
        else:
            pass # Cancel
    
    def DatabaseConnect(self):
        self.DatabaseClose()
        self.Database.setDatabaseName(self.DatabaseName)
        self.Database.open()
        if self.Database.isOpen():
            self.TreePopulate()
            self.TreeActiveTransactionPopulate()
            self.UpdateActionStatus()
        else:
            print "Problem?"
            
    def DatabaseClose(self):
        if self.Database.isOpen():
            self.Database.close()

    def DatabaseCreate(self):
        self.DatabaseClose()
        self.Database.setDatabaseName(self.DatabaseName)
        self.Database.open()
        if self.Database.isOpen():
            self.Database.exec_("""CREATE TABLE Article (
                                id INTEGER PRIMARY KEY,
                                parent INTEGER,
                                name TEXT,
                                price TEXT,
                                tax TEXT)""")
            self.Database.exec_("""CREATE TABLE Trans (
                                id INTEGER PRIMARY KEY,
                                type TEXT,
                                name TEXT,
                                price INTEGER,
                                tax INTEGER,
                                quantity INTEGER,
                                count INTEGER,
                                waiter TEXT,
                                date_created DATE,
                                time_created TEXT)""")
            self.Database.exec_("""CREATE TABLE Active (
                                id INTEGER PRIMARY KEY,
                                type TEXT,
                                name TEXT,
                                price INTEGER,
                                tax INTEGER,
                                quantity INTEGER,
                                count INTEGER,
                                date_created DATE,
                                waiter TEXT,
                                time_created TEXT,
                                comment TEXT)""")
            self.Database.exec_("""CREATE TABLE Users (
                                id INTEGER PRIMARY KEY,
                                name TEXT,
                                pass TEXT,
                                date_created DATE)""")
            self.DatabaseClose()
            self.DatabaseConnect()
        else:
            print "Problem?!"

    def DatabaseArticleAdd(self,aArticle):
        InsertQuery = QtSql.QSqlQuery()
        InsertQuery.prepare("INSERT INTO Article (parent, name, price, tax) "
                            "VALUES (:parent, :name, :price, :tax)")
        InsertQuery.bindValue(":parent",QtCore.QVariant(aArticle.Parent))
        InsertQuery.bindValue(":name",QtCore.QVariant(aArticle.Name))
        InsertQuery.bindValue(":price",QtCore.QVariant(aArticle.Price))
        InsertQuery.bindValue(":tax",QtCore.QVariant(aArticle.Tax))
        InsertQuery.exec_()
        Query = self.Database.exec_("SELECT * FROM Article")
        Query.last()
        return Query.value(0).toString()

    def DatabaseArticleEdit(self,aArticle):
        InsertQuery = QtSql.QSqlQuery()
        InsertQuery.prepare("UPDATE Article "
                            "SET parent=:parent, name=:name, price=:price, tax=:tax "
                            "WHERE id=:id")
        InsertQuery.bindValue(":id",QtCore.QVariant(aArticle.ID))
        InsertQuery.bindValue(":parent",QtCore.QVariant(aArticle.Parent))
        InsertQuery.bindValue(":name",QtCore.QVariant(aArticle.Name))
        InsertQuery.bindValue(":price",QtCore.QVariant(aArticle.Price))
        InsertQuery.bindValue(":tax",QtCore.QVariant(aArticle.Tax))
        InsertQuery.exec_()
    
    def DatabaseArticleDelete(self,aArticle):
        InsertQuery = QtSql.QSqlQuery()
        InsertQuery.prepare("UPDATE Article "
                            "SET parent='0'"
                            "WHERE parent=:id")
        InsertQuery.bindValue(":id",QtCore.QVariant(aArticle.ID))
        InsertQuery.exec_()
        InsertQuery.prepare("DELETE FROM Article "
                            "WHERE id=:id")
        InsertQuery.bindValue(":id",QtCore.QVariant(aArticle.ID))
        InsertQuery.exec_()

    def DatabaseTransactionAdd(self,aTransaction):
        InsertQuery = QtSql.QSqlQuery()
        InsertQuery.prepare("INSERT INTO Trans (type, name, price, tax, quantity, count, date_created, time_created, waiter) " 
                            "VALUES (:type, :name, :price, :tax, :quantity, :count, :date_created, :time_created, :waiter)")
        InsertQuery.bindValue(":type",QtCore.QVariant(aTransaction.Type))
        InsertQuery.bindValue(":name",QtCore.QVariant(aTransaction.Name))
        InsertQuery.bindValue(":price",QtCore.QVariant(aTransaction.Price))
        InsertQuery.bindValue(":tax",QtCore.QVariant(aTransaction.Tax))
        InsertQuery.bindValue(":quantity",QtCore.QVariant(aTransaction.Quantity))
        InsertQuery.bindValue(":count",QtCore.QVariant(aTransaction.Count))
        InsertQuery.bindValue(":date_created",QtCore.QVariant(aTransaction.DateCreated))
        InsertQuery.bindValue(":time_created",QtCore.QVariant(aTransaction.TimeCreated))
        InsertQuery.bindValue(":waiter",QtCore.QVariant(aTransaction.Waiter))
        InsertQuery.exec_()

    def DatabaseActiveTransactionAdd(self,aTransaction):
        InsertQuery = QtSql.QSqlQuery()
        InsertQuery.prepare("INSERT INTO Active (type, name, price, tax, quantity, count, date_created, time_created, comment, waiter) " 
                            "VALUES (:type, :name, :price, :tax, :quantity, :count, :date_created, :time_created, :comment, :waiter)")
        InsertQuery.bindValue(":type",QtCore.QVariant(aTransaction.Type))
        InsertQuery.bindValue(":name",QtCore.QVariant(aTransaction.Name))
        InsertQuery.bindValue(":price",QtCore.QVariant(aTransaction.Price))
        InsertQuery.bindValue(":tax",QtCore.QVariant(aTransaction.Tax))
        InsertQuery.bindValue(":quantity",QtCore.QVariant(aTransaction.Quantity))
        InsertQuery.bindValue(":count",QtCore.QVariant(aTransaction.Count))
        InsertQuery.bindValue(":date_created",QtCore.QVariant(aTransaction.DateCreated))
        InsertQuery.bindValue(":time_created",QtCore.QVariant(aTransaction.TimeCreated))
        InsertQuery.bindValue(":comment",QtCore.QVariant(aTransaction.Comment))
        InsertQuery.bindValue(":waiter",QtCore.QVariant(aTransaction.Waiter))
        InsertQuery.exec_()
        #print InsertQuery.lastError().text()
      
    def DatabaseActiveTransactionDelete(self,count):
        self.Database.exec_("DELETE FROM Active WHERE count='%s'" % count)

    def DatabaseUserAdd(self,User):
        InsertQuery = QtSql.QSqlQuery()
        InsertQuery.prepare("INSERT INTO Users (name, pass) "
                            "VALUES (:name, :password)")
        InsertQuery.bindValue(":name",QtCore.QVariant(User.Name))
        InsertQuery.bindValue(":password",QtCore.QVariant(User.Pass))
        InsertQuery.exec_()

    def DatabaseGetUsers(self):
        """
        * Vrakja lista na site korisnici od tabelata Users
          [['user1','pass'],['user2','pass'],...]
        """
        Query = self.Database.exec_("SELECT * FROM Users")
        usr=[]
        while Query.next():
            name = Query.value(1).toString()
            password = Query.value(2).toString()
            usr.append([name,password]) 
        return usr

    def DatabaseUserExist(self,name):
        return self.Database.exec_("SELECT * FROM Users WHERE name='%s'" % name).first()
        
    def DatabaseUserDelete(self,name):
        self.Database.exec_("DELETE FROM Users WHERE name='%s'" % name)


#---------------- Popolnuvanje na drva i tabeli ---------

    def TreePopulate(self):
        self.TreeArticleList.clear()
        #Root
        Query = self.Database.exec_("SELECT * FROM Article WHERE parent='0'")
        while Query.next():
            self.TreeArticleAdd(Article([Query.value(i).toString() for i in range(5)]))
        #Childs
        Query = self.Database.exec_("SELECT * FROM Article WHERE parent<>'0'")
        while Query.next():
            self.TreeArticleAdd(Article([Query.value(i).toString() for i in range(5)]))
        self.TreeArticleList.expandAll()

    def TreeActiveTransactionPopulate(self):
        self.ListaNaracki.clear()
        Query = self.Database.exec_("SELECT * FROM Active")
        count=[]
        while Query.next():
            if Query.value(6).toString() not in count:
                count.append(Query.value(6).toString())
                date = Query.value(7).toString()
                time = Query.value(8).toString()
                comment = Query.value(9).toString()
                QtGui.QTreeWidgetItem(self.ListaNaracki,[d2u("Маса број: %s") % comment, count[-1],time,date])

    def TreeArticleAdd(self,aArticle):
        ArticleAsList = aArticle.get_list()
        ArticleAsList.insert(0,aArticle.Name.split("\n")[0])
        
        if aArticle.Parent=="0": # root
            QtGui.QTreeWidgetItem(self.TreeArticleList,ArticleAsList)
        else:
            QtGui.QTreeWidgetItem(self.TreeArticleList.findItems(aArticle.Parent,Qt.Qt.MatchExactly,1)[0],ArticleAsList)

    def TreeArticleEdit(self,aArticle):
        EditedItem = self.TreeArticleList.findItems(aArticle.ID,Qt.Qt.MatchRecursive,1)[0]
        if EditedItem.text(2)=="0": # root
            self.TreeArticleList.takeTopLevelItem(self.TreeArticleList.indexOfTopLevelItem(EditedItem))
        else:
            EditedItem.parent().takeChild(EditedItem.parent().indexOfChild(EditedItem))
        self.TreeArticleAdd(aArticle)
    
    def TreeArticleDelete(self,aArticle):
        EditedItem = self.TreeArticleList.findItems(aArticle.ID,Qt.Qt.MatchRecursive,1)[0]
        if EditedItem.text(2)=="0": #Root
            for ChildIndex in range(EditedItem.childCount()):
                ChildItem=EditedItem.takeChild(ChildIndex)
                ChildItem.setText(2,"0")
                QtGui.QTreeWidgetItem(self.TreeArticleList,[ChildItem.text(i) for i in range(5)])
            self.TreeArticleList.takeTopLevelItem(self.TreeArticleList.indexOfTopLevelItem(EditedItem))
        else:
            EditedItem.parent().takeChild(EditedItem.parent().indexOfChild(EditedItem))

    def InfoUpdate(self):
        self.TableNarackaClear()
        count = self.ListaNaracki.selectedItems()[0].text(1)
        self.Sum = 0

        Query = self.Database.exec_("SELECT * FROM Active WHERE count='%s'" % count)
        while Query.next():
            count=0
            self.TableNarackaPrikazLastRow = self.TableNaracka.rowCount()
            self.TableNarackaPrikaz.insertRow(self.TableNarackaPrikazLastRow)
            for i in (2,3,5):
                #i=name,price,quant
                item  = QtGui.QTableWidgetItem(Query.value(i).toString())
                item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                item.setFlags(QtCore.Qt.ItemIsEnabled) #read-only
                self.TableNarackaPrikaz.setItem(self.TableNarackaPrikazLastRow,count,item)
                count += 1

            itemSum = QtGui.QTableWidgetItem(QtCore.QString(str(Query.value(3).toInt()[0] * Query.value(5).toInt()[0])))
            itemSum.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            itemSum.setFlags(QtCore.Qt.ItemIsEnabled) #read-only

            self.TableNarackaPrikaz.setItem(self.TableNarackaPrikazLastRow,3,itemSum)
            
            self.Sum += Query.value(3).toInt()[0] * Query.value(5).toInt()[0]

        self.LCDNumberSum.display(self.Sum)

    def TableAdd(self):
        self.TableNarackaLastRow = self.TableNaracka.rowCount()
        self.TableNaracka.insertRow(self.TableNarackaLastRow)

        itemName  = QtGui.QTableWidgetItem(self.TreeArticleList.selectedItems()[0].text(3))
        itemName.setFlags(QtCore.Qt.ItemIsEnabled) #read-only

        itemPrice = QtGui.QTableWidgetItem(self.TreeArticleList.selectedItems()[0].text(4))
        itemTax   = QtGui.QTableWidgetItem(self.TreeArticleList.selectedItems()[0].text(5))

        self.TableNaracka.setItem(self.TableNarackaLastRow,0,itemName)
        self.TableNaracka.setItem(self.TableNarackaLastRow,1,itemPrice)
        self.TableNaracka.setItem(self.TableNarackaLastRow,2,itemTax)

    def TableClear(self):
        self.TableNaracka.clear()
        self.TableNaracka.setRowCount(0)
        self.TableNaracka.setHorizontalHeaderLabels([d2u("Артикл"),d2u("Цена"),d2u("Данок"),d2u("Количина")])
        self.LabelError.hide()

    def TableNarackaClear(self):
        self.TableNarackaPrikaz.clear()
        self.TableNarackaPrikaz.setRowCount(0)
        self.TableNarackaPrikaz.setHorizontalHeaderLabels([d2u("Артикл"),d2u("Цена"),d2u("Количина"),d2u("Вкупно")])


if __name__=="__main__":
    myApp = QtGui.QApplication(sys.argv)
    
    myProgram = MainWindow()
    myProgram.showFullScreen()
    #"windows", "motif", "cde", "plastique" and "cleanlooks", platform: "windowsxp", "windowsvista" and "macintosh"
    #myApp.setStyle(QtGui.QStyleFactory.create("cleanlooks")) 
    
    #new stylesheet

    styleFile="./static/style.stylesheet"
    with open(styleFile,"r") as fh:
        myApp.setStyleSheet(fh.read())
    fh.close()
    myApp.exec_()

