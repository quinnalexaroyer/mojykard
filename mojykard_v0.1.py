import tkinter as tk
import datetime
import random
import sqlite3
import dataclasses
import copy
from tkinter import filedialog
from tkinter import messagebox
from dataclasses import dataclass

import binary_heap
from binary_heap import BinaryHeap
import extrawidgets
from extrawidgets import *

class Card:
    def __init__(self, *args):
        self.id = args[0] if 0 < len(args) else None
        self.deck = args[1] if 1 < len(args) else None
        self.content = args[2] if 2 < len(args) else None
        self.hints = args[3] if 3 < len(args) else []
        self.tags = set(args[4]) if 4 < len(args) else set()
    def key(self):
        return self.id
    def copy(self, other=None):
        if other is None:
            other = Card()
        for i in ("id", "content", "hints", "tags", "side", "user", "span",\
            "due", "lowest", "rating", "timesReviewed"):
            setattr(other, i, getattr(self, i, None))
        return other
    def deepCopy(self, other=None):
        if other is None:
            other = Card()
        for i in ("id", "content", "side", "user", "span", "due", "lowest",\
            "rating", "timesReviewed"):
            setattr(other, i, getattr(self, i, None))
        if hasattr(self, "hints"):
            other.hints = Utility.deepListCopy(self.hints)
        if hasattr(self, "tags"):
            other.tags = Utility.deepSetCopy(self.tags)
    def set(self, other):
        self.id = other.id if not None else self.id
        self.content = other.content if not None else self.content
        self.hints = other.hints if not None else self.hints
        self.tags = other.tags if not None else self.tags
    def printMultiline(self):
        s = "ID: " + str(self.id) + "\n" +\
            "content: " + str(self.content) + "\n" +\
            "hints: " + str(self.hints) + "\n" +\
            "tags: " + str(self.tags) + "\n"
        return s

class CardSide(Card):
    def __init__(self, *args):
        super().__init__(*args)
        self.side = args[5] if 5 < len(args) else None
        self.span = args[6] if 6 < len(args) else None
        self.due = args[7] if 7 < len(args) else None
        self.lowest = 6
        self.rating = [0,0,0,0,0,0]
        self.timesReviewed = 0
        self.updateSpan = None
        self.updateDue = None
        if self.content is None:
            self.content = ""
    def key(self):
        return (self.id, self.side)

class FullCard(Card):
    def __init__(self, *args):
        super().__init__(*args)
        self.user = args[5] if 5 < len(args) else None
        self.deck = args[6] if 6 < len(args) else None
        if self.content is None:
            self.content = []
    def copy(self):
        return super().copy(FullCard())
    def getSide(self, side):
        return Utility.getAtIndexIfArray(self.content,side-1)
    def getHint(self, side, number):
        return Utility.getAtIndexIfArray(self.hints[side],number-1)
    def compare(self, other):
        if len(self.content) != len(other.content) or len(self.tags) != \
            len(other.tags) or len(self.hints) != len(other.hints):
            return False
        for idx,i in enumerate(self.content):
            if i != other.content[idx]:
                return False
        for idx,i in enumerate(self.hints):
            if len(i) != len(other.hints[idx]):
                return False
            for jdx,j in enumerate(i):
                if j != other.hints[idx][jdx]:
                    return False
        return len(self.tags.symmetric_difference(other.tags)) == 0

class Utility:
    span = tuple([2**((i-3)/2) for i in range(6)])
    @staticmethod
    def newDB(filename):
        conn = sqlite3.connect(filename+".db")
        c = conn.cursor()
        e = c.execute
        e("CREATE TABLE users (name VARCHAR, time DATETIME)")
        e("CREATE TABLE decks (name VARCHAR, sides INTEGER, owner INTEGER)")
        e("CREATE TABLE cards (deck INTEGER, owner INTEGER, created DATETIME, "\
            "edited DATETIME, edits INTEGER)")
        e("CREATE TABLE card_sides (card INTEGER, side INTEGER, content TEXT)")
        e("CREATE TABLE user_decks (user INTEGER, deck INTEGER, sides INTEGER)")
        e("CREATE TABLE user_cards (user INTEGER, card INTEGER, side INTEGER, "\
            "span FLOAT, due DATETIME, rate0 INTEGER, rate1 INTEGER, rate2 INTEGER, "\
            "rate3 INTEGER, rate4 INTEGER, rate5 INTEGER)")
        e("CREATE TABLE options (user INTEGER, deck INTEGER, option INTEGER, "\
            "value INTEGER)")
        e("CREATE TABLE tags (tag VARCHAR)")
        e("CREATE TABLE card_tags (card INTEGER, tag INTEGER)")
        e("CREATE TABLE hints (card INTEGER, side INTEGER, user INTEGER, "\
            "hintOrder INTEGER, content VARCHAR)")
        conn.commit()
        conn.close()
    @staticmethod
    def getBinaryFlags(b):
        f = []
        i = 0
        while b > 0:
            if b%2 == 1:
                f.append(i)
            i += 1
            b //= 2
        return f
    @staticmethod
    def getBinaryFlags1(b):
        return Utility.getBinaryFlags(b << 1)
    @staticmethod
    def isBitFlagged(bit, flag):
        return (1 << bit) & flag != 0
    @staticmethod
    def isBitFlagged1(bit, flag):
        return Utility.isBitFlagged(bit-1, flag)
    @staticmethod
    def resetBit(bit, flag):
        return flag & ~(1 << bit)
    @staticmethod
    def resetBit1(bit, flag):
        return Utility.resetBit(bit-1, flag)
    @staticmethod
    def setBit(bit, flag):
        return flag | (1 << bit)
    @staticmethod
    def setBit1(bit, flag):
        return Utility.setBit(bit-1, flag)
    @staticmethod
    def makeNumberFromBits(bitList):
        sum = 0
        for i in range(len(bitList)):
            if bitList[i]:
                sum += 2**i
        return sum
    @staticmethod
    def makeNumberFromBits1(bitList):
        return 2*Utility.makeNumberFromBits(bitList)
    @staticmethod
    def getIndexOfValue(value, theList):
        for i in range(len(theList)):
            if theList[i] == value:
                return i
        return -1
    @staticmethod
    def arrangeByIndex(l0):
        # l0 is a list where each element has two items. Item 0 is an index and item 1 is a values
        # It returns a list of the "item 1" values in the index given by "item 0"
        if len(l0) == 0:
            return []
        l = [None for i in range(max([j[0] for j in l0])+1)]
        for i in l0:
            l[i[0]] = i[1]
        return l
    @staticmethod
    def deepListCopy(theList):
        theCopy = []
        for i in theList:
            if isinstance(i, list):
                theCopy.append(Utility.deepListCopy(i))
            elif isinstance(i, set):
                theCopy.append(Utility.deepSetCopy(i))
            else:
                theCopy.append(i)
        return theCopy
    @staticmethod
    def deepSetCopy(theSet):
        return set(Utility.deepListCopy(list(theSet)))
    @staticmethod
    def strToSeconds(s):
        s1 = [int(i) for i in s.split(":")]
        return 60*s1[-2] + s1[-1]
    @staticmethod
    def secondsToStr(s):
        if s > 3600:
            return str(int(s)//60) + ":" + str(int(s)%60).zfill(2)
        else:
            return str(int(s)//3600) + ":" + str((int(s)//60)%60).zfill(2) + ":"\
				+ str(int(s)%60).zfill(2)
    @staticmethod
    def setPageNumOfTotal(var, page, total):
        if page == 0:
            var.set("NEW of " + str(total))
        else:
            var.set(str(page) + " of " + str(total))
    @staticmethod
    def setXOfY(var, number, total, zero="0"):
        if number == 0:
            var.set(zero + " of " + str(total))
        else:
            var.set(str(number) + " of " + str(total))
    @staticmethod
    def getAtIndexIfArray(theArray, theIndex, ifNotList=None, ifOutRange=None):
        if type(theArray) is list or type(theArray) is tuple:
            return theArray[theIndex] if -len(theArray) <= theIndex < len(theArray)\
                else ifOutRange
        else:
            return ifNotList
    @staticmethod
    def ZeroOrNone(theList):
        return Utility.getAtIndexIfArray(theList, 0)
    @staticmethod
    def notZeroValue(value):
        def tests(v):
            return v is not None and v != 0 and v is not False
        if (isinstance(value, tuple) or isinstance(value, list)):
            return len(value) == 0 or tests(value[0])
        else:
            return tests(value)
    @staticmethod
    def isListNone(theList):
        for i in theList:
            if isinstance(i, list):
                if not Utility.isListNone(i):
                    return False
            elif i is not None:
                return False
        return True
    @staticmethod
    def setListItem(theList, theIndex, value):
        while len(theList) <= abs(theIndex):
            theList.append(None)
        theList[theIndex] = value
    @staticmethod
    def listIndicesExist(theList, *indices):
        l = theList
        for i in indices:
            if i >= len(l) or i < -len(l):
                return False
            l = l[i]
        return True

class Order:
    def __init__(self):
        self.index = {}
        self.reverseIndex = []
    def insert(self, key):
        self.index[key] = len(self.reverseIndex)
        self.reverseIndex.append(key)
    def removeByKey(self, key):
        idx = self.index[key]
        self.reverseIndex[idx] = self.reverseIndex[-1]
        self.index[self.reverseIndex[-1]] = idx
        self.reverseIndex.pop()
        self.index.pop(key)
    def removeByIndex(self, idx):
        self.removeByKey(self.reverseIndex[idx])
    def getIndex(self, key):
        return self.index[key]
    def getKey(self, idx):
        return self.reverseIndex[idx]

class Deck:
    def __init__(self):
        self.deck = {}
        self.order = Order()
        self.orderMarker = -1
    def __iter__(self):
        return self.deck.__iter__()
    def __getitem__(self, idx):
        return self.get(idx)
    def __contains__(self, idx):
        return idx in self.deck
    def remove(self, theCard):
        idx = self.order.getIndex(theCard.key())
        self.deck.pop(theCard.key())
        self.order.removeByKey(theCard.key())
    def removeByOrder(self, idx):
        key = self.order.getKey(idx)
        self.deck.pop(getKey)
        self.order.pop(idx)
    def insert(self, newCard):
        self.deck[newCard.key()] = newCard
        self.order.insert(newCard.key())
    def get(self, idx):
        return self.deck[idx]
    def getByOrder(self, idx):
        return self.deck[self.order.getKey(idx)]
    def size(self):
        return len(self.deck)
    def fill(self, cardList):
        for i in cardList: self.insert(i)
    def keys(self):
        return self.deck.keys()
    def getCardList(self):
        return list(self.deck.values())
    def getNext(self):
        orderMarker += 1
        if orderMarker >= self.size():
            orderMarker = 0
        return self.getByOrder(orderMarker)
    def getRandom(self):
        return self.getByOrder(random.randint(0, self.size()-1))
    def getRandomExceptID(self, idx):
        numericMap = list(range(self.size()))
        theCard = self.getRandom()
        while theCard.id == idx and len(numericMap) > 0:
            r = random.randint(0, len(numericMap)-1)
            theCard = self.getByOrder(numericMap[r])
            numericMap.pop(r)
        if theCard.id != idx:
            return theCard
        else:
            return None

class ReviewDeck(Deck):
    def __init__(self):
        self.deck = BinaryHeap()
    def getRoot(self):
        return self.deck.getRoot()
    def popRoot(self):
        return self.deck.popRoot()
    def insert(self, timeDue, theCard):
        self.deck.insert(timeDue, theCard)
    def size(self):
        return self.deck.size()
    def getTimeDue(self):
        return self.deck.getRootKey()
    def getCardList(self):
        return self.deck.getValues()
    def get(self, indexInDeck):
        return self.deck.values[indexInDeck]
    def size(self):
        return len(self.deck.values)

@dataclass
class DeckInfo:
    id: int = None
    name: str = None
    totalSides: int = None
    sidesUsed: int = None
    totalCards: int = None
    totalDue: int = None
    totalNeverReviewed: int = None
    numNew: int = None
    numDue: int = None
    percentNewInSession: int = None
    numNewInSession: int = 0
    numDrawnInSession: int = 0
    sidesUsedInSession: int = 0
    newLimitOffset: int = 0
    dueLimitOffset: int = 0
    notDueLimitOffset: int = 0
    def copy(self):
        return copy.copy(self)

class ModelInfo:
    def __init__(self, databaseConnection, userID):
        self.conn = databaseConnection
        self.c = self.conn.cursor()
        self.user = userID
    def getUserDecks(self):
        e = self.c.execute
        e("SELECT u.deck,d.name,d.sides,u.sides FROM user_decks u INNER "\
            "JOIN decks d ON u.deck=d.rowid WHERE user=?", (self.user,))
        sqlDecks = self.c.fetchall()
        decks = []
        for i in sqlDecks:
            deckID = i[0]
            decks.append(DeckInfo(deckID,i[1],i[2],i[3]))
            e("SELECT COUNT(*) FROM user_cards u INNER JOIN cards c ON "\
                "u.card=c.rowid WHERE c.deck=?", (deckID,))
            decks[-1].totalCards = self.c.fetchone()[0]
            e("SELECT COUNT(*) FROM user_cards u INNER JOIN cards c ON "\
                "u.card=c.rowid WHERE c.deck=? AND u.due IS NULL", (deckID,))
            decks[-1].totalNeverReviewed = self.c.fetchone()[0]
            e("SELECT COUNT(*) FROM user_cards u INNER JOIN cards c ON "\
                "u.card=c.rowid WHERE c.deck=? AND u.due <= ?", (deckID,\
                datetime.date.today()))
            decks[-1].totalDue = self.c.fetchone()[0]
        return decks
    def getOption(self, option, deckID=None):
        if deckID is not None:
            self.c.execute("SELECT value FROM options WHERE user=? AND deck=? AND "\
                "option=?", (self.user, deckID, option))
        else:
            self.c.execute("SELECT value FROM options WHERE user=? AND option=? AND "\
            "deck IS NULL", (self.user, option))
        r = self.c.fetchone()
        return r[0] if r is not None else None
    def getDeckNames(self):
        self.c.execute("SELECT name FROM decks")
        return [i[0] for i in self.c.fetchall()]
    def getUserID(self, name):
        self.c.execute("SELECT rowid FROM users WHERE name=?", (name,))
        r = self.c.fetchone()
        return r[0] if r is not None else None
    def getDeckNameFromID(self, id):
        self.c.execute("SELECT name FROM decks WHERE rowid=?", (id,))
        r = self.c.fetchone()
        return r[0] if r is not None else None
    def getDeckIDFromName(self, name):
        self.c.execute("SELECT rowid FROM decks WHERE name=?", (name,))
        r = self.c.fetchone()
        return r[0] if r is not None else None
    def getDeckSidesFlag(self, deckID):
        self.c.execute("SELECT sides FROM user_decks WHERE deck=? AND user=?", \
            (deckID,self.user))
        r = self.c.fetchone()
        return Utility.ZeroOrNone(r)
    def getNumDeckSides(self, deckID):
        self.c.execute("SELECT sides FROM decks WHERE rowid=?", (deckID,))
        r = self.c.fetchone()
        return Utility.getAtIndexIfArray(r, 0, ifNotList=0, ifOutRange=0)
    def getDeckOfCard(self, cardID):
        self.c.execute("SELECT deck FROM cards WHERE rowid=?", (cardID,))
        return Utility.ZeroOrNone(self.c.fetchone())
    def getCardContent(self, cardID):
        e = self.c.execute
        e("SELECT side,content FROM card_sides WHERE card=? ORDER BY side", (cardID,))
        return Utility.arrangeByIndex(self.c.fetchall())[1:]
    def getHintsOfSide(self, userID, cardID, side):
        self.c.execute("SELECT hintOrder,content FROM hints WHERE user=? AND card=? "\
        "AND side=? ORDER BY hintOrder", (userID, cardID, side))
        return Utility.arrangeByIndex(self.c.fetchall())[1:]
    def getHintsAllSides(self, userID, cardID):
        deckID = self.getDeckOfCard(cardID)
        hintList = []
        for i in range(self.getNumDeckSides(deckID)):
            hintList.append(self.getHintsOfSide(userID, cardID, i+1))
        return hintList
    def getCardHints(self, userID, cardID):
        self.c.execute("SELECT hintOrder,content FROM hints WHERE user=? AND card=? "\
            "AND side IS NULL ORDER BY hintOrder", (userID, cardID))
        return Utility.arrangeByIndex(self.c.fetchall())[1:]
    def getHints(self, userID, cardID):
        return [self.getCardHints(userID, cardID)] +\
            self.getHintsAllSides(userID, cardID)
    def getTags(self, cardID):
        self.c.execute("SELECT t.tag FROM tags t INNER JOIN card_tags c ON "\
            "t.rowid=c.tag WHERE c.card=? ORDER BY t.tag", (cardID,))
        return set([i[0] for i in self.c.fetchall()])
    def getTagID(self, tagText):
        self.c.execute("SELECT rowid FROM tags WHERE tag=?", (tagText,))
        return Utility.ZeroOrNone(self.c.fetchone())
    def getCardsFromDeck(self, deckID):
        theDeck = []
        self.c.execute("SELECT rowid,owner FROM cards WHERE deck=?", (deckID,))
        for i in self.c.fetchall():
            theDeck.append(FullCard(i[0], deckID, self.getCardContent(i[0]),\
                self.getHints(i[1], i[0]), set(self.getTags(i[0])), i[1]))
        return theDeck
    def getNumEdits(self, theCard):
        self.c.execute("SELECT edits FROM cards WHERE rowid=?", (theCard.id,))
        r = Utility.ZeroOrNone(self.c.fetchone())
        return r if r is not None else 0
    def getCardIDFromDeck(self, deckID):
        self.c.execute("SELECT rowid FROM cards WHERE deck=?", (deckID,))
        return Utility.ZeroOrNone(self.c.fetchone())
    def getCardIDFromSide(self, side, deck, content):
        self.c.execute("SELECT s.card FROM card_sides s INNER JOIN cards c ON "\
            "c.rowid=s.card WHERE s.side=? AND s.content=? AND c.deck=?",\
            (side, content, deck))
        return Utility.ZeroOrNone(self.c.fetchone())
    def getUsers(self):
        ModelInfo.getUsers(self.c)
    def doesNameExist(self, table, name):
        self.c.execute("SELECT count(*) FROM " + table + " WHERE name=?", (name,))
        return self.c.fetchone()[0] > 0
    def doesUsernameExist(self, username):
        return self.doesNameExist("users", username)
    def doesDeckExist(self, deckName):
        return self.doesNameExist("decks", deckName)
    def doesDeckIDExist(self, deckID):
        self.c.execute("SELECT count(rowid) FROM decks WHERE rowid=?", (deckID,))
        return self.c.fetchone()[0] > 0
    def isUsingDeckName(self, deckName):
        self.c.execute("SELECT * FROM user_decks u INNER JOIN decks d ON "\
            "u.deck=d.rowid WHERE u.user=? AND d.name=?", (self.user, deckName))
        r = self.c.fetchone()
        return r is not None and len(r) > 0 and r[0] is not None
    def doesHintExist(self, cardID, side, hintNum):
        if side != 0:
            self.c.execute("SELECT COUNT(*) FROM hints WHERE card=? AND side=? "\
                "AND hintOrder=? AND user=?", (cardID, side, hintNum, self.user))
        else:
            self.c.execute("SELECT COUNT(*) FROM hints WHERE card=? AND side IS NULL "\
                "AND hintOrder=? AND user=?", (cardID, hintNum, self.user))
        return Utility.notZeroValue(self.c.fetchone())
    def doesCardSideExist(self, cardID, side):
        self.c.execute("SELECT COUNT(*) FROM card_sides WHERE card=? AND side=?",\
            (cardID, side))
        return Utility.notZeroValue(self.c.fetchone())
    def isTagUsed(self, tag):
        e = self.c.execute
        e("SELECT rowid FROM tags WHERE tag=?", (tag,))
        tagID = Utility.ZeroOrNone(self.c.fetchone())
        if tagID is not None:
            e("SELECT COUNT(*) FROM card_tags WHERE tag=?", (tagID,))
            return Utility.notZeroValue(self.c.fetchone())
        else:
            return False
    def getUsersOfDeck(self, deckID):
        self.c.execute("SELECT user,sides FROM user_decks WHERE deck=?", (deckID,))
        return self.c.fetchall()
    def useCardSide(self, cardID, side, user):
        self.c.execute("INSERT INTO user_cards (user, card, side, span, "\
            "rate0, rate1, rate2, rate3, rate4, rate5) VALUES (?,?,?,1,0,0,0,0,0,0)",\
            (user, cardID, side))
    @staticmethod
    def getUsers(c):
        c.execute("SELECT rowid,name FROM users")
        return c.fetchall()

class Model(ModelInfo):
    SECONDS_TO_REVIEW = [120,120,300,300,0,0]
    TIMES_TO_REVIEW = [0,0,8,4,2,1]
    NUMBER_OF_NEW_CARDS = 10
    NUMBER_OF_REVIEWED_CARDS = 30
    PERCENT_NEW = 30
    SPAN = [2**((i-3)/2) for i in range(6)]
    def __init__(self, conn):
        self.active = Deck()
        self.review = ReviewDeck()
        self.discard = Deck()
        self.reference = Deck()
        self.conn = conn
        self.c = self.conn.cursor()
        self.secondsToReview = self.__class__.SECONDS_TO_REVIEW
        self.nTimesToReview = self.__class__.TIMES_TO_REVIEW # Do not allow [5] to be 0
        self.randomOrder = True
        self.stats = {"new":0, "rerun":0, "total":0, "unique":0, "ratingSum":0}
        self.logfile = "mojykard_log.txt"
    def getListOfSides(self, deckID):
        areSidesUsed = self.control.getSidesUsed(deckID)
        return [i+1 for i in range(len(areSidesUsed)) if areSidesUsed[i]]
    def loadCard(self, row, deckID):
        self.active.insert(CardSide(row[0], deckID, row[1], [], [], row[2], row[3], row[4]))
        if row[0] not in self.reference:
            newCard = FullCard(row[0], deckID, self.getCardContent(row[0]),\
                self.getHints(self.user, row[0]), self.getTags(row[0]),\
                self.user, row[0])
            self.reference.insert(newCard)
    def getNewCardsFromDB(self, deckID, numNew):
        listOfSides = self.getListOfSides(deckID)
        limitOffset = self.deckInfo[deckID].newLimitOffset
        queryPiece = ",".join("?"*len(listOfSides))
        queryVars = tuple([deckID, self.user] + listOfSides + [limitOffset, numNew])
        self.c.execute("SELECT u.card,s.content,u.side,u.span,u.due FROM user_cards "\
            "u INNER JOIN card_sides s ON s.card=u.card AND s.side=u.side INNER "\
            "JOIN cards c ON c.rowid=u.card WHERE u.due IS NULL AND c.deck=? AND "\
            "u.user=? AND u.side IN (" + queryPiece + ") ORDER BY u.card ASC, "\
            "u.side ASC LIMIT ?,?", queryVars)
        r = self.c.fetchall()
        for i in r:
            self.loadCard(i, deckID)
        self.deckInfo[deckID].newLimitOffset += len(r)
        return len(r)
    def getDueCardsFromDB(self, deckID, numDue):
        listOfSides = self.getListOfSides(deckID)
        limitOffset = self.deckInfo[deckID].dueLimitOffset
        queryPiece = ",".join("?"*len(listOfSides))
        queryVars = tuple([datetime.date.today(), deckID, self.user] + listOfSides\
            + [limitOffset, numDue])
        self.c.execute("SELECT u.card,s.content,u.side,u.span,u.due FROM "\
            "user_cards u INNER JOIN card_sides s ON s.card=u.card AND "\
            "s.side=u.side INNER JOIN cards c ON c.rowid=u.card WHERE u.due <= ? "\
            "AND c.deck=? AND u.user=? AND u.side IN (" + queryPiece + ") ORDER "\
            "BY u.due DESC, u.card ASC, u.side ASC LIMIT ?,?", queryVars)
        r = self.c.fetchall()
        for i in r:
            self.loadCard(i, deckID)
        self.deckInfo[deckID].dueLimitOffset += len(r)
        return len(r)
    def getNotDueCardsFromDB(self, deckID, numCards):
        listOfSides = self.getListOfSides(deckID)
        limitOffset = self.deckInfo[deckID].notDueLimitOffset
        queryPiece = ",".join("?"*len(listOfSides))
        queryVars = tuple([datetime.date.today(), deckID, self.user] + listOfSides\
            + [limitOffset, numCards])
        self.c.execute("SELECT u.card,s.content,u.side,u.span,u.due FROM "\
            "user_cards u INNER JOIN card_sides s ON s.card=u.card AND "\
            "s.side=u.side INNER JOIN cards c ON c.rowid=u.card WHERE u.due > ? "\
            "AND c.deck=? AND u.user=? AND u.side IN (" + queryPiece + ") ORDER "\
            "BY u.due DESC, u.card ASC, u.side ASC LIMIT ?,?", queryVars)
        r = self.c.fetchall()
        for i in r:
            self.loadCard(i, deckID)
        self.deckInfo[deckID].notDueLimitOffset += len(r)
        return len(r)
    def loadDeck(self, deckID):
        def moreCardsToLoad(total):
            return total - self.active.size()
        numNew = self.deckInfo[deckID].numNew
        numDue = self.deckInfo[deckID].numDue
        numNewLoaded = self.getNewCardsFromDB(deckID, numNew)
        numDueLoaded = self.getDueCardsFromDB(deckID, numDue)
        if self.active.size() < numDue+numNew:
            self.getNewCardsFromDB(deckID, moreCardsToLoad(numNew+numDue))
            self.getDueCardsFromDB(deckID, moreCardsToLoad(numNew+numDue))
            self.getNotDueCardsFromDB(deckID, moreCardsToLoad(numNew+numDue))
    def isReviewDeckDue(self):
        return self.review.size() > 0 and self.review.getTimeDue() <= datetime.datetime.today()
    def drawReviewCard(self):
        self.currentCard = self.review.popRoot()
    def toReview(self, seconds):
        self.review.insert(datetime.datetime.today() + datetime.timedelta(seconds=seconds),\
            self.currentCard)
        if self.currentCard.key() in self.active:
            self.active.remove(self.currentCard)
        if self.currentCard.key() in self.discard:
            self.discard.remove(self.currentCard)
    def toActive(self):
        if self.currentCard.key() not in self.active:
            self.active.insert(self.currentCard)
    def toDiscard(self):
        if self.currentCard.key() in self.active:
            self.active.remove(self.currentCard)
        if self.currentCard.key() not in self.discard:
            self.discard.insert(self.currentCard)
    def reviewEarly(self):
        if self.review.size() > 0:
            self.drawReviewCard()
        else:
            self.drawCard()
    def drawCard(self):
        def drawFromDiscard():
            if self.discard.size() > 0:
                theCard = self.discard.getRandomExceptID(self.currentCard.id)
                if theCard is None: # and active size == 0
                    theCard = self.discard.getRandom()
                self.currentCard = theCard
            else:
                self.drawReviewCard()
        if self.isReviewDeckDue() and self.currentCard.id != self.review.getRoot().id:
            self.drawReviewCard()
        elif self.randomOrder:
            if self.active.size() > 0:
                theCard = self.active.getRandomExceptID(self.currentCard.id)
                if theCard is None:
                    theCard = self.discard.getRandomExceptID(self.currentCard.id) # might want to replace with drawfromdiscard()
                if theCard is None:
                    theCard = self.active.getRandom()
                self.currentCard = theCard
            else:
                drawFromDiscard()
        else:
            if self.active.size() > 0:
                self.currentCard = self.active.getNext()
            else:
                self.drawFromDiscard()
        self.setTimeShownCard()
    def rateCard(self, rating):
        self.currentCard.rating[rating] += 1
        if self.currentCard.lowest > rating:
            self.currentCard.lowest = rating
        self.logRating(rating)
    def updateStatsAfterRating(self, rating):
        self.stats["total"] += 1
        self.stats["ratingSum"] += rating
        if self.currentCard.timesReviewed == 0:
            self.stats["unique"] += 1
            if self.currentCard.due is None:
                self.stats["new"] += 1
            else:
                self.stats["rerun"] += 1
        self.currentCard.timesReviewed += 1
    def addCardFromDB(self, deckID):
        d = self.deckInfo[deckID]
        if d.numDrawnInSession == 0 or d.numNewInSession/d.numDrawnInSession\
            > d.percentNewInSession/100:
            numLoaded = self.getDueCardsFromDB(deckID, 1)
            if numLoaded == 0:
                numLoaded = self.getNewCardsFromDB(deckID, 1)
                d.numNewInSession += numLoaded
                if numLoaded == 0:
                    numLoaded = self.getNotDueCardsFromDB(deckID, 1)
            d.numDrawnInSession += numLoaded
        else:
            numLoaded = self.getNewCardsFromDB(deckID, 1)
            d.numNewInSession += numLoaded
            if numLoaded == 0:
                numLoaded = self.getDueCardsFromDB(deckID, 1)
                if numLoaded == 0:
                    numLoaded = self.getNotDueCardsFromDB(deckID, 1)
            d.numDrawnInSession += numLoaded
    def returnCardToDeck(self, rating):
        if self.currentCard.id not in self.discard:
            if self.nTimesToReview[rating] != 0 and self.currentCard.timesReviewed\
                >= self.nTimesToReview[rating]:
                self.toDiscard()
                self.addCardFromDB(self.currentCard.deck)
            elif self.secondsToReview[rating] != 0:
                self.toReview(self.secondsToReview[rating])
            else:
                self.toActive()
    def save(self):
        e = self.c.execute
        l = self.active.getCardList() + self.review.getCardList() +\
            self.discard.getCardList()
        for i in l:
            if i.lowest != 6:
                e("SELECT rowid,span,due,rate0,rate1,rate2,rate3,rate4,rate5 FROM "\
                    "user_cards WHERE card=? AND side=?", (i.id, i.side))
                r = self.c.fetchone()
                newDue = 0
                newSpan = 0
                if i.updateSpan is not None:
                    newSpan = i.updateSpan
                else:
                    newSpan = Model.SPAN[i.lowest] * r[1]
                if i.updateDue is not None:
                    newDue = i.updateDue
                else:
                    newDue = datetime.date.today() + datetime.timedelta(days=max(1,round(newSpan)))
                queryVars = tuple([newSpan, newDue] + [r[3+j] + i.rating[j] for\
                    j in range(6)] + [r[0]])
                e(("UPDATE user_cards SET span=?, due=?, rate0=?, rate1=?, "\
                    "rate2=?, rate3=?, rate4=?, rate5=? WHERE rowid=?"), queryVars)
        self.control.commit()
    def getCurrentCardContent(self):
        return self.reference.get(self.currentCard.id)
    def openLog(self):
        self.logOutput = open(self.logfile,"a")
    def closeLog(self):
        self.logOutput.close()
    def logBeginning(self):
        self.openLog()
        self.timeSessionBegan = datetime.datetime.now()
        self.logOutput.write("\n--------\n" + str(datetime.datetime.now()) + "\n")
    def setTimeShownCard(self):
        timeDelta = datetime.datetime.now() - self.timeSessionBegan
        self.timeShownCard = timeDelta.seconds + timeDelta.microseconds/1000000
    def logRating(self, rating):
        timeDeltaOfRating = (datetime.datetime.now() - self.timeSessionBegan)
        timeToRating = timeDeltaOfRating.seconds + timeDeltaOfRating.microseconds/1000000\
            - self.timeShownCard
        self.logOutput.write(",".join([str(self.currentCard.deck),\
            str(self.currentCard.id), str(self.currentCard.side), str(rating),\
            str(round(self.timeShownCard,3)), str(round(timeToRating,3))]) + "\n")

class EditUser(ModelInfo):
    @staticmethod
    def newUser(conn, username):
        c = conn.cursor()
        c.execute("INSERT INTO users (name) VALUES (?)", (username,))
        userID = c.lastrowid
        conn.commit()
        c.close()
        return userID
    def newDeck(self, deckName, numSides):
        self.c.execute("INSERT INTO decks (name,sides,owner) VALUES (?,?,?)", \
            (deckName, numSides, self.user))
        self.conn.commit()
    def updateUsingDeckSides(self, deckID, sideFlag):
        self.c.execute("SELECT sides FROM user_decks WHERE user=? AND deck=?",\
            (self.user, deckID))
        r = self.c.fetchone()
        if r is None or len(r) == 0 or r[0] is None:
            self.c.execute("INSERT INTO user_decks (user, deck, sides) VALUES (?,?,?)",\
                (self.user, deckID, sideFlag))
        else:
            newFlag = r[0] & sideFlag
            if newFlag != sideFlag:
                self.c.execute("UPDATE user_decks SET sides=? WHERE user=? AND deck=?",\
                (newFlag, self.user, deckID))
    def useSidesOfDeck(self, deckID, sideFlag):
        self.updateUsingDeckSides(deckID, sideFlag)
        sides = Utility.getBinaryFlags1(sideFlag)
        for i in self.getCardsFromDeck(deckID):
            for j in sides:
                self.useCardSide(i.id, j, self.user)
    def useDeck(self, deckID, sideFlag):
        self.useSidesOfDeck(deckID, sideFlag)
        self.conn.commit()
    def setOptions(self, deckID, secondsToReview=[], timesToReview=[], numCardsToDraw=[]):
        def setOption(number, value):
            e = self.c.execute
            if deckID is not None:
                e("SELECT value FROM options WHERE user=? AND deck=? AND option=?",\
                    (self.user, deckID, number))
                r = self.c.fetchone()
                if r is None or len(r) == 0:
                    e("INSERT INTO options (user, deck, option, value) "\
                        "VALUES (?,?,?,?)", (self.user, deckID, number, value))
                else:
                    e("UPDATE options SET value=? WHERE user=? AND deck=? AND "\
                        "option=?", (value, self.user, deckID, number))
            else:
                e("SELECT value FROM options WHERE user=? AND deck IS NULL AND "\
                    "option=?", (self.user, number))
                r = self.c.fetchone()
                if r is None or len(r) == 0:
                    e("INSERT INTO options (user, option, value) VALUES "\
                        "(?,?,?)", (self.user, number, value))
                else:
                    e("UPDATE options SET value=? WHERE user=? AND deck IS NULL "\
                        "AND option=?", (value, self.user, number))
        for i in range(len(secondsToReview)):
            setOption(i, secondsToReview[i])
        for i in range(len(timesToReview)):
            setOption(6+i, timesToReview[i])
        for i in range(len(numCardsToDraw)):
            setOption(12+i, numCardsToDraw[i])
        self.conn.commit()

class EditCards(ModelInfo):
    def __init__(self, databaseConnection, userID):
        super().__init__(databaseConnection, userID)
        self.resetData()
    def resetData(self):
        self.deckID = 0 # ID of deck currently being edited
        self.edited = None # collection of cards that have been edited (to be saved)
        self.original = None # deck of cards without edits in the current session
        self.cardOrder = None # list of card IDs; the order in which cards are browsed
        self.numNewCards = 0 # number of cards inserted during the editing session
        self.numSides = 2 # number of sides of the deck currently being edited
        self.totalCards = 0 # Total number of cards being edited in the deck
    def getOriginalCard(self, cardID):
        return self.original.get(cardID)
    def getEditedCard(self, cardID):
        return self.edited.get(cardID)
    def getCard(self, cardID):
        if cardID in self.edited:
            return self.edited.get(cardID)
        elif cardID in self.original:
            return self.original.get(cardID)
        else:
            return None
    def cardNumToID(self, theIndex):
        if 1 <= theIndex <= len(self.cardOrder):
            return self.cardOrder[theIndex-1]
        else:
            return -self.numNewCards-1
    def getCardByNumber(self, n):
        return self.getCard(self.cardNumToID(n))
    def selectDeckForEditing(self, deckID):
        self.deckID = deckID
        self.original = Deck()
        self.edited = Deck()
        self.original.fill(self.getCardsFromDeck(deckID))
        self.cardOrder = list(self.original.keys())
        self.numSides = self.getNumDeckSides(deckID)
        self.totalCards = self.original.size()
    def insertHint(self, cardID, side, hintOrder, hintContent):
        if side != 0:
            self.c.execute("INSERT INTO hints (content,card,user,side,hintOrder) "\
                "VALUES (?,?,?,?,?)", (hintContent, cardID, self.user, side, hintOrder))
        else:
            self.c.execute("INSERT INTO hints (content,card,user,hintOrder) "\
                "VALUES (?,?,?,?)", (hintContent, cardID, self.user, hintOrder))
    def updateHint(self, cardID, side, hintOrder, hintContent):
        if side != 0:
            self.c.execute("UPDATE hints SET content=? WHERE card=? AND user=? "\
                "AND side=? AND hintOrder=?", (hintContent, cardID, self.user,\
                side, hintOrder))
        else:
            self.c.execute("UPDATE hints SET content=? WHERE card=? AND user=? "\
                "AND side IS NULL AND hintOrder=?", (hintContent, cardID, self.user,\
                hintOrder))
    def saveHints(self, theCard):
        cardID = theCard.id
        hints = theCard.hints
        origCard = self.original.get(cardID) if cardID in self.original else None
        if hints is not None:
            for side,hintsOfSide in enumerate(hints):
                for idx,h in enumerate(hintsOfSide):
                    hintNum = idx+1
                    if not self.doesHintExist(cardID, side, hintNum):
                        self.insertHint(cardID, side, hintNum, h)
                    elif origCard is None or theCard.hints[side][idx] != \
                        origCard.hints[side][idx]:
                        self.updateHint(cardID, side, hintNum, h)
    def insertTag(self, cardID, tagText):
        e = self.c.execute
        tagID = self.getTagID(tagText)
        if tagID is None:
            e("INSERT INTO tags (tag) VALUES (?)", (tagText,))
            tagID = self.c.lastrowid
        e("INSERT INTO card_tags (card, tag) VALUES (?,?)", (cardID, tagID))
    def removeTag(self, cardID, tagText):
        self.c.execute("DELETE FROM card_tags WHERE tag IN (SELECT t.rowid "\
            "FROM card_tags c INNER JOIN tags t ON c.tag=t.rowid WHERE "\
            "c.card=? AND t.tag=?)", (cardID, tagText))
        if not self.isTagUsed(tagText):
            self.c.execute("DELETE FROM tags WHERE tag=?", (tagText,))
    def saveTags(self, theCard):
        cardID = theCard.id
        tags = theCard.tags
        oldTags = self.getTags(cardID)
        for i in list(tags.difference(oldTags)):
            self.insertTag(cardID, i)
        for i in list(oldTags.difference(tags)):
            self.removeTag(cardID, i)
    def newDeck(self,name,sides):
        self.c.execute("INSERT INTO decks (name,sides,owner) VALUES (?,?,?)",\
            (name,sides,self.user))
    def useNewCard(self, cardID):
        for (user,sideFlag) in self.listOfUsersOfDecks:
            sideList = Utility.getBinaryFlags1(sideFlag)
            for side in sideList:
                self.useCardSide(cardID, side, user)
    def newCard(self, theCard):
        content = theCard.content
        e = self.c.execute
        now = datetime.datetime.today()
        e("INSERT INTO cards (deck,owner,created,edited,edits) VALUES (?,?,?,?,1)",\
            (self.deckID,self.user,now,now))
        theCard.id = self.c.lastrowid
        for i in range(len(content)):
            e("INSERT INTO card_sides (card,side,content) VALUES (?,?,?)",\
                (theCard.id, i+1, content[i]))
        for i in range(len(content), self.numSides, 1):
            e("INSERT INTO card_sides (card,side,content) VALUES (?,?,\"\")",\
                (theCard.id, i+1))
        self.saveHints(theCard)
        self.saveTags(theCard)
        self.useNewCard(theCard.id)
        return theCard
    def updateSideContent(self, side, theCard):
        if self.doesCardSideExist(theCard.id, side):
            self.c.execute("UPDATE card_sides SET content=? WHERE card=? "\
                "AND side=?", (theCard.content[side-1], theCard.id, side))
    def updateCardEdits(self, theCard):
        numEdits = self.getNumEdits(theCard)
        self.c.execute("UPDATE cards SET edited=?, edits=? WHERE rowid=?",\
            (datetime.datetime.today(), numEdits+1, theCard.id))
    def isCardModified(self, cardID):
        if cardID not in self.edited or cardID not in self.original:
            return True
        else:
            origCard = self.original.get(cardID)
            editCard = self.edited.get(cardID)
            return not origCard.compare(editCard)
    def saveSides(self, theCard):
        origCard = self.original.get(theCard.id)
        for i in range(len(theCard.content)):
            if len(origCard.content) < i or theCard.content[i] != origCard.content[i]:
                self.updateSideContent(i+1, theCard)
    def saveCard(self, theCard):
        if theCard.id >= 0:
            if self.isCardModified(theCard.id):
                self.saveSides(theCard)
                self.updateCardEdits(theCard)
        else:
            self.newCard(theCard)
        self.saveHints(theCard)
        self.saveTags(theCard)
    def saveCards(self):
        self.listOfUsersOfDecks = self.getUsersOfDeck(self.deckID)
        for i in self.edited:
            self.saveCard(self.edited[i])
        self.conn.commit()
    def isHintNew(self, **kwargs):
        return False
    def storeCard(self, theCard):
        if theCard.id not in self.edited:
            self.edited.insert(theCard)
            if theCard.id < 0:
                self.numNewCards += 1
                self.totalCards += 1
                self.cardOrder.append(theCard.id)
        else:
            self.edited.get(theCard.id).set(theCard)
    def resetCurrentCard(self):
        theCard = self.getCurrentCard()
        if theCard is not None and theCard.id in self.edited:
            self.edited.remove(theCard.id)
    def copyAttr(self, other):
        for i in ("conn", "c", "user", "deckID", "edited", "original", "cardOrder",\
            "numNewCards", "numSides", "totalCards"):
            setattr(self, i, getattr(other, i, None))

class EditSingleCard(EditCards):
    def resetData(self):
        super().resetData()
        self.cardNumber = 0 # the card currently being edited, given as an index of cardOrder
        self.hintNumber = [0] * (self.numSides+1) # Number of the hint currently being edited
        self.totalHints = [0] * (self.numSides+1) # Total number of hints for the card currently being edited
        self.isTextModified = False
        # The member currentHints is lists of lists, and hintNumber and totalHints are lists of integers.
        # List #0 contains information for card-wide hints, and #i contains information
        # about the hints for side #i (for i >= 1)
    def resetTotalHints(self):
        theCard = self.getCurrentCard()
        if self.cardNumber is None or self.cardNumber == 0 or theCard is None:
            self.totalHints = [0] * (self.numSides + 1)
        else:
            self.totalHints = [len(i) for i in theCard.hints]
    def clearHints(self):
        pass
    def setCardNumber(self):
        if self.totalCards >= 1:
            self.cardNumber = 1
        else:
            self.cardNumber = 0
        #self.resetHintNumbers()
    def selectDeckForEditing(self, deckID):
        super().selectDeckForEditing(deckID)
        self.setCardNumber()
    def getCurrentCard(self):
        return self.getCardByNumber(self.cardNumber)
    def textModified(self, event):
        self.isTextModified = True
    def isHintNew(self, **kwargs):
        return self.hintNumber[kwargs["side"]] == 0
    def storeCard(self, theCard):
        theCard.id = self.cardNumToID(self.cardNumber)
        if self.isCardModified(theCard.id):
            self.isTextModified = False
            super().storeCard(theCard)
    def prevCard(self):
        self.cardNumber -= 1
        if self.cardNumber < 0:
            self.cardNumber = self.totalCards
        self.clearHints()
    def nextCard(self):
        self.cardNumber += 1
        if self.cardNumber > self.totalCards:
            self.cardNumber = 0
        self.clearHints()
    def editNewCard(self):
        self.cardNumber = 0
    def newHint(self, side):
        self.hintNumber[side] = 0
    def resetHints(self):
        cardID = ec.cardNumToID(self.cardNumber)
        if cardID in self.edited:
            originalCard = ec.getOriginalCard(cardID)
            self.getCurrentCard().hints = originalCard.hints
        resetHintNumbers()
    def resetTags(self):
        cardID = ec.cardNumToID(self.cardNumber)
        if cardID in self.edited:
            originalCard = ec.getOriginalCard(cardID)
            self.getCurrentCard().tags = originalCard.tags.copy()
    def fromMulti(self, other):
        self.copyAttr(other)
        self.setCardNumber()

class EditMultiCards(EditCards):
    ROWS = 25
    def resetData(self):
        super().resetData()
        self.pageNumber = 1 # the page currently being edited
    def cardOrderOfRow(self, rowNum):
        return self.__class__.ROWS * (self.pageNumber-1) + rowNum + 1
    def rowNumToID(self, rowNum):
        return self.cardNumToID(self.cardOrderOfRow(rowNum))
    def getCardOfRow(self, rowNum):
        return self.getCard(self.rowNumToID(rowNum))
    def newPage(self, delta):
        ROWS = self.__class__.ROWS
        self.pageNumber += delta
        if self.pageNumber <= 0:
            self.pageNumber = 1
        elif self.pageNumber > 1 + (self.original.size()+self.numNewCards)//ROWS:
            self.pageNumber = 1 + (self.original.size()+self.numNewCards)//ROWS
    def storeCard(self, theCard, rowNum): # saves the card in the FullCard class
        theCard.id = self.rowNumToID(rowNum)
        if self.isCardModified(theCard.id):
            super().storeCard(theCard)
    def resetCard(self, cardID):
        del self.edited[cardID]
    def saveRow(self, rowNum): # saves to the database
        theCard = self.getCardOfRow(rowNum)
        if theCard.id > 0:
            self.saveCard(theCard)
        else:
            self.newCard(theCard)
    def setPageNumber(self):
        self.pageNumber = 1
        self.totalPages = 1 + self.original.size() // self.__class__.ROWS
    def selectDeckForEditing(self, deckID):
        super().selectDeckForEditing(deckID)
        self.setPageNumber()
    def fromSingle(self, other):
        self.copyAttr(other)
        self.setPageNumber()

class View:
    def __init__(self, controller):
        self.win = tk.Tk()
        self.win.geometry("600x600+200+50")
        self.control = controller
        self.lay = {}
        self.w = {}
        self.v = {}
        self.edituser = None
        self.currentLayout = None
        self.returnLayout = None
    # * * * * *   UTILITY METHODS   * * * * *
    def begin(self): # rename this
        self.menuGUI()
        self.createScrollbar()
        self.openFileGUI()
        self.selectUserGUI()
        self.switchLayout("openFile")
        self.win.mainloop()
    def makeNumWidgets(self, numWidgets, frame, widgetType, widgetList,\
        argList={}, functionList={}, start=(0,0), delta=(1,0)):
        def getRowCol(i):
            return {"row":start[0]+i*delta[0], "column":start[1]+i*delta[1]}
        def runFunctionList(x):
            functionResults = {}
            for j in functionList: functionResults[j] = functionList[j](x)
            return functionResults
        for i in widgetList:
            i.grid_forget()
        for i in range(min(len(widgetList),numWidgets)):
            widgetList[i].grid(**getRowCol(i))
        while len(widgetList) < numWidgets:
            i = len(widgetList)
            newWidget = widgetType(frame)
            widgetList.append(newWidget)
            functionResults = runFunctionList(i)
            newWidget.config(**{**argList, **functionResults})
            newWidget.grid(**getRowCol(i))
    def makeNumVars(self, numVars, varType, varList):
        while len(varList) < numVars:
            varList.append(varType())
    def selectDeckListBox(self, frame, var=None, filter=lambda x:True):
        box = tk.Listbox(frame, selectmode="single", height=4)
        if var is not None:
            box.config(listvariable=var)
        if self.edituser is not None:
            for i in self.edituser.getDeckNames():
                if filter(i): box.insert("end", i)
        return box
    def selectDeckHeader(self, parentFrame, command, filter=None):
        theListBox = None
        frame = tk.Frame(parentFrame)
        if filter is None:
            theListBox = self.selectDeckListBox(frame)
        else:
            theListBox = self.selectDeckListBox(frame, filter=filter)
        def enter():
            selectionIdx = theListBox.get(0,"end").index(entryVar.get())
            if selectionIdx >= 0:
                theListBox.selection_set(selectionIdx)
        def select():
            deckName = theListBox.get("active")
            entryVar.set(deckName)
            selectedVar.set(deckName)
            command(self.edituser.getDeckIDFromName(deckName))
        entryVar = tk.StringVar()
        selectedVar = tk.StringVar()
        theEntry = tk.Entry(frame, textvariable=entryVar)
        enterButton = tk.Button(frame, text="Enter", command=enter)
        selectButton = tk.Button(frame, text="Select", command=select)
        displayFrame = tk.Frame(frame)
        theEntry.grid(row=0, column=0, sticky="e")
        enterButton.grid(row=0, column=1, sticky="w")
        theListBox.grid(row=0, column=2, sticky="e")
        selectButton.grid(row=0, column=3, sticky="w")
        tk.Label(displayFrame, text="Deck Selected:").grid(row=0, column=0,\
            sticky="s")
        tk.Label(displayFrame, textvariable=selectedVar).grid(row=1, column=0,\
            sticky="n")
        displayFrame.grid(row=0, column=4)
        return (frame, theListBox)
    @staticmethod
    def trivialEntry(theList):
        # theList is a list where each entry is a tkinter variable or text widget
        for i in theList:
            if isinstance(i, tk.Text):
                if i.get("1.0", "end").strip() != "":
                    return False
            elif isinstance(i, tk.StringVar):
                if i.get().strip() != "":
                    return False
            elif isinstance(i, tk.IntVar) or isinstance(i, tk.DoubleVar) or \
                isinstance(i, tk.BooleanVar):
                if i.get() is not None:
                    return False
        return True
    def switchLayout(self,newLayout):
        if self.currentLayout is not None:
            self.currentLayout.pack_forget()
        self.prevLayout = self.currentLayout
        self.lay[newLayout].pack(fill="both")
        self.currentLayout = self.lay[newLayout]
    def revertLayout(self):
        if self.currentLayout is not None:
            self.currentLayout.pack_forget()
        self.prevLayout.pack()
        temp = self.prevLayout
        self.prevLayout = self.currentLayout
        self.currentLayout = temp
    def switchFrame(self,x,y,row,col):
        self.w[x].grid_forget()
        self.w[y].grid(row=row, column=col)
    def updateTimer(self):
        if self.timer is not None:
            t = self.datetime.datetime.today() - self.timer
            self.v["timer"].set(str(t.seconds//3600) + ":" +\
                str((t.seconds//60)%60).zfill(2) + ":" + str(t.seconds%60).zfill(2))
        self.win.after(1001-t.microseconds//1000,self.updateTimer)
    # * * * * *   GET FORM DATA    * * * * *
    def shouldOverrideReviewTime(self):
        return self.v["shouldOverrideReviewTime"].get()
    def shouldOverrideDueDate(self):
        return self.v["shouldOverrideDueDate"].get()
    def shouldOverrideDueSpan(self):
        return self.v["shouldOverrideDueSpan"].get()
    def getOverrideReviewTime(self):
        return self.v["overrideReviewTime"].get()
    def getOverrideDueDate(self):
        return datetime.datetime.strptime(self.v["overrideDueDate"].get(), "%Y-%m-%d")
    def getOverrideDueSpan(self):
        return self.v["overrideDueSpan"].get()
    # * * * * *   DRAW INITIAL GUIs   * * * * *
    def drawGUI(self):
        self.userDecksGUI()
        self.preReviewGUI()
        self.cardGUI()
        self.editSingleCardGUI()
        self.editMultiCardGUI()
        self.importCardsGUI()
        self.newDeckGUI()
        self.useDeckGUI()
        self.setOptionsGUI()
    def createScrollbar(self):
        canvas = tk.Canvas(self.win, width=600, height=600)
        canvas.configure(scrollregion=canvas.bbox("all"))
        self.mainCanvas = canvas
        frame = tk.Frame(canvas)
        self.mainFrame = frame
        def onFrameConfig(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def onCanvasConfig(event):
            width = max(600, frame.winfo_reqwidth())
            height = max(600, frame.winfo_reqheight())
            canvas.configure(width=width, height=height)
        yScroll = tk.Scrollbar(self.win, orient="vertical", command=canvas.yview)
        yScroll.pack(side="right", anchor="e", fill="y")
        xScroll = tk.Scrollbar(self.win, orient="horizontal", command=canvas.xview)
        xScroll.pack(side="bottom", anchor="s", fill="x")
        canvas.config(xscrollcommand=xScroll.set, yscrollcommand=yScroll.set)
        canvas.pack(side="right", anchor="nw")
        canvas.create_window((0,0), window=frame, anchor="nw")
        frame.bind("<Configure>", onFrameConfig)
        canvas.bind("<Configure>", onCanvasConfig)
    def menuGUI(self):
        def optionsMenu():
            self.switchLayout("options")
        def useDeckMenu():
            self.switchLayout("useDeck")
        def logOffMenu():
            pass
        def newDeckMenu():
            self.switchLayout("newDeck")
        def editSingleCardsMenu():
            self.switchLayout("editSingleCard")
        def editMultiCardsMenu():
            self.switchLayout("editMultiCard")
        def importCardsMenu():
            self.switchLayout("importCards")
        def newFileMenu():
            self.switchLayout("newFile")
        def newUserMenu():
            self.switchLayout("newUser")
        self.menu = tk.Menu(self.win)
        self.win.config(menu=self.menu)
        usermenu = tk.Menu(self.menu, tearoff=0)
        usermenu.add_command(label="Options", command=optionsMenu)
        usermenu.add_command(label="Use Deck", command=useDeckMenu)
        usermenu.add_command(label="Log Off", command=logOffMenu)
        editmenu = tk.Menu(self.menu, tearoff=0)
        editmenu.add_command(label="New Deck", command=newDeckMenu)
        editmenu.add_command(label="Edit Cards (Singular Mode)", command=editSingleCardsMenu)
        editmenu.add_command(label="Edit Cards (Multiple Mode)", command=editMultiCardsMenu)
        editmenu.add_command(label="Import Cards", command=importCardsMenu)
        adminmenu = tk.Menu(self.menu, tearoff=0)
        adminmenu.add_command(label="New File", command=newFileMenu)
        adminmenu.add_command(label="New User", command=newUserMenu)
        self.menu.add_cascade(label="User", menu=usermenu)
        self.menu.add_cascade(label="Edit", menu=editmenu)
        self.menu.add_cascade(label="Admin", menu=adminmenu)
    def openFileGUI(self):
        layout = tk.Frame(self.mainFrame)
        self.lay["openFile"] = layout
        selectFileVar = tk.StringVar()
        newFileVar = tk.StringVar()
        filebox = None
        def getFiles():
            fin = open("files.txt","r")
            fileList = [i.strip() for i in fin.read().split("\n") if len(i.strip()) != 0]
            fin.close()
            if len(fileList) == 0:
                fileList.append(None)
            return fileList
        def newFile():
            filename = newFileVar.get()
            Utility.newDB(filename)
            fin = open("files.txt", "r")
            fileList = fin.read().strip().split("\n")
            fin.close()
            i = 0
            while i < len(fileList) and fileList[i] < filename:
                i += 1
            fileList.insert(i, filename)
            fout = open("files.txt","w")
            fout.write("\n".join(fileList))
            fout.close()
            filebox["menu"].add_command(label=filename, command=tk._setit(selectFileVar,\
                filename))
        def openFile():
            self.control.openFile(selectFileVar.get())
        filebox = tk.OptionMenu(layout, selectFileVar, *getFiles())
        filebox.grid(row=0,column=0)
        tk.Button(layout, text="Select File", command=openFile).grid(row=0, column=1)
        tk.Entry(layout, textvariable=newFileVar).grid(row=1, column=0)
        tk.Button(layout, text="New File", command=newFile).grid(row=1, column=1)
    def selectUserGUI(self):
        selectedUser = tk.StringVar()
        newUserVar = tk.StringVar()
        layout = tk.Frame(self.mainFrame)
        self.lay["selectUser"] = layout
        userbox = tk.OptionMenu(layout, selectedUser, None)
        self.w["selectUserBox"] = userbox
        self.v["selectedUser"] = selectedUser
        def selectUser():
            self.control.selectUser(selectedUser.get())
        def newUser():
            username = newUserVar.get()
            if username.strip() != "":
                EditUser.newUser(self.control.conn, username)
                menu = userbox["menu"]
                menu.add_command(label=username, command=tk._setit(selectedUser,\
                    username))
        userbox.grid(row=0,column=0)
        tk.Button(layout, text="Select User", command=selectUser).grid(row=0,\
            column=1)
        tk.Entry(layout, textvariable=newUserVar).grid(row=1,column=0)
        tk.Button(layout, text="Add User", command=newUser).grid(row=1, column=1)
    def resetSelectUserbox(self, userList):
        userbox = self.w["selectUserBox"]
        uservar = self.v["selectedUser"]
        userbox["menu"].delete(0, "end")
        for i in userList:
            userbox["menu"].add_command(label=i[1], command=tk._setit(uservar, i[1]))
    # * * * * *   GUIs FOR RUNNING SESSION   * * * * *
    def userDecksGUI(self):
        def isADeckChecked():
            for i in self.v["userDeckChecks"]:
                if i.get():
                    return True
            return False
        def begin():
            if isADeckChecked():
                self.switchLayout("preReview")
                self.displayPreReview()
        layout = tk.Frame(self.mainFrame)
        deckNameVar = tk.StringVar()
        self.lay["userDecks"] = layout
        self.w["userDecks"] = {"checks":[], "name":[], "totalDue":[], "totalNeverReviewed":[],\
            "totalCards":[], "sidesUsed":[]}
        self.v["userDeckChecks"] = [tk.BooleanVar(), tk.BooleanVar()]
        tk.Button(layout, text="Begin Session", command=begin).grid(row=0, column=0)
    def displayUserDecks(self):
        self.control.setUserDecks()
        decks = self.control.getUserDecks()
        def getSideStr(x):
            sidesUsedList = Utility.getBinaryFlags(decks[x].sidesUsed)
            return str([i+1 for i in sidesUsedList])[1:-1]
        layout = self.lay["userDecks"]
        while len(self.v["userDeckChecks"]) < len(decks):
            self.v["userDeckChecks"].append(tk.BooleanVar())
        self.makeNumWidgets(len(decks), layout, tk.Checkbutton, self.w["userDecks"]["checks"],\
            functionList={"variable": (lambda x:self.v["userDeckChecks"][x])}, start=(1,0), delta=(1,0))
        self.makeNumWidgets(len(decks), layout, tk.Label, self.w["userDecks"]["name"],\
            functionList={"text":(lambda x:decks[x].name)},  start=(1,1), delta=(1,0))
        self.makeNumWidgets(len(decks), layout, tk.Label, self.w["userDecks"]["totalCards"],\
            functionList={"text":(lambda x:decks[x].totalCards)},  start=(1,2), delta=(1,0))
        self.makeNumWidgets(len(decks), layout, tk.Label, self.w["userDecks"]["totalDue"],\
            functionList={"text":(lambda x:decks[x].totalDue)},  start=(1,3), delta=(1,0))
        self.makeNumWidgets(len(decks), layout, tk.Label, self.w["userDecks"]["totalNeverReviewed"],\
            functionList={"text":(lambda x:decks[x].totalNeverReviewed)},  start=(1,4), delta=(1,0))
        self.makeNumWidgets(len(decks), layout, tk.Label, self.w["userDecks"]["sidesUsed"],\
            functionList={"text":(lambda x:str(decks[x].totalSides) + " | " +\
            getSideStr(x))},  start=(1,5), delta=(1,0))
    def preReviewGUI(self):
        # Layout:
        # row 0: Buttons (begin/back)
        # row 1: labels for ratings (0-5)
        # row 2: wigets of amount of time to wait until showing a card again for ratings 0-5
        # row 3: widgets of the number of times to get a card correct before it is discarded for ratings 0-5
        # row 4: labels for the table of decks
        # rows 5 and above: a table of decks to enter information before starting the session
        #    columns 0 and 1: name of the deck
        #    column 2: initial new cards
        #    column 3: initial reviewed cards
        #    column 4: percent of cards drawn in session to be new
        #    column 5: frame of checkboxes to indicate which sides to study
        # In the variables below:
        # name: name of the deck
        # new: number of new cards drawn when the session begins
        # reviewed: number of reviewed cards drawn when the session begins
        # session: percent of cards drawn in session to be new
        # (widget only) sides: a frame which contains checkboxes to select the sides to use
        layout = tk.Frame(self.mainFrame)
        self.lay["preReview"] = layout
        self.w["preReviewDeckOptions"] = {"name":[], "new":[], "reviewed":[], "session":[], "sides":[]}
        self.v["preReviewDeckOptions"] = {"name":[], "new":[], "reviewed":[], "session":[], "sides":[]}
        self.v["preReviewRateWait"] = [tk.IntVar() for i in range(6)]
        self.v["preReviewRateTimes"] = [tk.IntVar() for i in range(6)]
        def begin():
            self.control.begin()
        def back():
            self.switchLayout("userDecks")
        tk.Button(layout, text="Begin", command=begin).grid(row=0, column=0, columnspan=3)
        tk.Button(layout, text="Back", command=back).grid(row=0, column=4, columnspan=3)
        tk.Label(layout, text="Seconds to wait").grid(row=2, column=0)
        tk.Label(layout, text="Number of times to review").grid(row=3, column=0)
        for i in range(6):
            tk.Label(layout, text=str(i)).grid(row=1, column=i+1)
            tk.Entry(layout, textvariable=self.v["preReviewRateWait"][i], width=5)\
                .grid(row=2, column=i+1)
            tk.Entry(layout, textvariable=self.v["preReviewRateTimes"][i], width=5)\
                .grid(row=3, column=i+1)
        deckOptionsFrame = tk.Frame(layout)
        self.lay["preReviewDeckFrame"] = deckOptionsFrame
        tk.Label(deckOptionsFrame, text="Name of\nDeck").grid(row=0, column=0)
        tk.Label(deckOptionsFrame, text="Initial\nNew\nCards").grid(row=0, column=1)
        tk.Label(deckOptionsFrame, text="Initial\nReviewed\nCards").grid(row=0, column=2)
        tk.Label(deckOptionsFrame, text="Percent\nnew cards\ndrawn in\nsession").grid(row=0, column=3)
        tk.Label(deckOptionsFrame, text="Sides\nto study").grid(row=0, column=4)
        deckOptionsFrame.grid(row=4, columnspan=7)
    def displayPreReview(self):
        layout = self.lay["preReview"]
        deckOptionsFrame = self.lay["preReviewDeckFrame"]
        self.control.setSessionDecks()
        decks = self.control.getSessionDecks()
        def makeOptionsFrame():
            self.makeNumVars(len(decks), tk.StringVar, self.v["preReviewDeckOptions"]["name"])
            for i in ("new", "reviewed", "session"):
                self.makeNumVars(len(decks), tk.IntVar, self.v["preReviewDeckOptions"][i])
            self.makeNumWidgets(len(decks), deckOptionsFrame, tk.Label, self.w["preReviewDeckOptions"]["name"],\
                functionList={"textvariable":(lambda x:self.v["preReviewDeckOptions"]["name"][x])},\
                start=(1,0), delta=(1,0))
            for idx,i in enumerate(("new", "reviewed", "session")):
                self.makeNumWidgets(len(decks), deckOptionsFrame, tk.Entry, self.w["preReviewDeckOptions"][i],\
                    argList={"width":5}, functionList={"textvariable":lambda x:self.v["preReviewDeckOptions"][i][x]},\
                    start=(1,idx+1), delta=(1,0))
            self.makeNumWidgets(len(decks), deckOptionsFrame, tk.Frame, self.w["preReviewDeckOptions"]["sides"],\
                start=(1,4), delta=(1,0))
        def makeCheckboxes():
            for idx,i in enumerate(decks):
                sides = Utility.getBinaryFlags1(self.edituser.getDeckSidesFlag(i))
                self.w["preReviewDeckOptions"]["sides"].append([])
                self.v["preReviewDeckOptions"]["sides"].append([])
                self.makeNumVars(len(sides), tk.BooleanVar, self.v["preReviewDeckOptions"]["sides"][-1])
                self.makeNumWidgets(len(sides), self.w["preReviewDeckOptions"]["sides"][idx],\
                    tk.Checkbutton, [], functionList={"text":(lambda x:sides[x]),\
                    "variable":(lambda x:self.v["preReviewDeckOptions"]["sides"][-1][x])},\
                    start=(0,0), delta=(0,1))
            for j in self.v["preReviewDeckOptions"]["sides"]:
                j[0].set(True)
        def enterOptions():
            deckID = None
            if len(decks) == 1:
                deckID = list(decks.keys())[0]
            for i in range(6):
                theOption = self.edituser.getOption(i, deckID=deckID)
                if theOption is None: theOption = Model.SECONDS_TO_REVIEW[i]
                self.v["preReviewRateWait"][i].set(theOption)
                theOption = self.edituser.getOption(i+6, deckID=deckID)
                if theOption is None: theOption = Model.TIMES_TO_REVIEW[i]
                self.v["preReviewRateTimes"][i].set(theOption)
            for i in range(len(decks)):
                deckID = self.control.getDeckNumber(i).id
                self.v["preReviewDeckOptions"]["name"][i].set(\
                    self.edituser.getDeckNameFromID(deckID))
                for j in ( (12,"new",Model.NUMBER_OF_NEW_CARDS),\
                    (13,"reviewed",Model.NUMBER_OF_REVIEWED_CARDS),\
                    (14,"session",Model.PERCENT_NEW) ):
                    theOption = self.edituser.getOption(j[0], deckID=deckID)
                    if theOption is None: theOption=j[2]
                    self.v["preReviewDeckOptions"][j[1]][i].set(theOption)
        makeOptionsFrame()
        makeCheckboxes()
        enterOptions()
    def popHints(self, hintNumber):
        pop = tk.Toplevel()
        hintWidget = SequenceLabel(pop, width=60, height=6)
        hintList = self.control.getHints()[hintNumber]
        hintWidget.fill(hintList)
        hintWidget.grid(row=0, column=0)
    def cardGUI(self):
        # Rows:
        # 0: Deck name
        # 1: Show hint/tag buttons, timer
        # 2: Sides of the cards
        # 3: Rating buttons, buttons to end session, show new card
        # 4: Edit due date, etc.
        # 5: Statistics
        layout = tk.Frame(self.mainFrame)
        self.lay["card"] = layout
        timelayout = tk.Frame(layout)
        deckNameVar = tk.StringVar()
        self.v["sides"] = [tk.StringVar(),tk.StringVar()]
        self.v["timer"] = tk.StringVar()
        def drawStatsFrame():
            self.w["cardStats"] = tk.Frame(layout)
            self.w["cardStats"].grid(row=5, column=0)
            self.v["cardStats"] = {}
            for i in [("Active Deck Size", "active", 0, 0, 0),\
                ("Review Deck Size", "review", 1, 0, 0),\
                ("Discarded Deck Size", "discard", 2, 0, 0),\
                ("Unique Cards Reviewed", "unique", 3, 0, 0),\
                ("Average Rating", "average", 0, 2, 1),\
                ("New Cards Reviewed", "new", 1, 2, 0),\
                ("Reruns Reviewed", "rerun", 2, 2, 0),\
                ("Total Cards Reviewed", "total", 3, 2, 0)]:
                tk.Label(self.w["cardStats"], text=i[0], font="Arial 10")\
                    .grid(row=i[2], column=i[3], sticky="e")
                var = None
                if i[4] == 0: var = tk.IntVar()
                elif i[4] == 1: var = tk.DoubleVar()
                self.v["cardStats"][i[1]] = var
                tk.Label(self.w["cardStats"], textvariable=var, font="Arial 10")\
                    .grid(row=i[2], column=i[3]+1, sticky="w")
        def makeRateButton(i):
            tk.Button(rateButtons, text=str(i), command=lambda:self.control.rateCard(i))\
                .grid(row=0, column=i)
        def hints():
            self.popHints(0)
        def tags():
            tagList = list(self.control.getTags())
            pop = tk.Toplevel()
            tk.Label(pop, text=tagList[1:-1]).grid()
        tk.Label(layout, textvariable=deckNameVar).grid(row=0, column=0)
        tk.Button(timelayout, text="Hints", command=hints).grid(row=0, column=0)
        tk.Button(timelayout, text="Tags", command=tags).grid(row=0, column=1)
        tk.Label(timelayout, textvariable=self.v["timer"]).grid(row=0, column=2)
        timelayout.grid(row=1, column=0)
        self.w["cardSideLabels"] = []
        self.w["cardSidesFrame"] = tk.Frame(layout)
        self.w["cardSidesFrame"].grid(row=2, column=0)
        self.w["cardSideHintButtons"] = []
        self.w["cardSides"] = []
        self.v["cardSides"] = []
        rateButtons = tk.Frame(layout)
        rateButtons.grid(row=3, column=0)
        statusButtons = tk.Frame(layout)
        self.w["cardRateButtons"] = rateButtons
        self.w["cardStatusButtons"] = statusButtons
        overrideDueTimesFrame = tk.Frame(layout)
        self.v["overrideReviewTime"] = tk.IntVar()
        self.v["overrideDueDate"] = tk.StringVar()
        self.v["overrideDueSpan"] = tk.DoubleVar()
        self.v["shouldOverrideReviewTime"] = tk.BooleanVar()
        self.v["shouldOverrideDueDate"] = tk.BooleanVar()
        self.v["shouldOverrideDueSpan"] = tk.BooleanVar()
        tk.Label(overrideDueTimesFrame, text="Review in").grid(row=0, column=0)
        tk.Label(overrideDueTimesFrame, text="Due date").grid(row=1, column=0)
        tk.Label(overrideDueTimesFrame, text="Due span").grid(row=2, column=0)
        for idx,i in enumerate(("ReviewTime", "DueDate", "DueSpan")):
            tk.Entry(overrideDueTimesFrame, textvariable=self.v["override"+i])\
                .grid(row=idx, column=1)
            tk.Checkbutton(overrideDueTimesFrame, variable=self.v["shouldOverride"+i]).\
                grid(row=idx, column=2)
        overrideDueTimesFrame.grid(row=4, column=0)
        for i in range(6):
            makeRateButton(i)
        tk.Button(statusButtons, text="End Session",\
            command=self.control.endSession).grid(row=0, column=0)
        tk.Button(statusButtons, text="Review Early",\
            command=self.control.reviewEarly).grid(row=0, column=1)
        tk.Button(statusButtons, text="New Card",\
            command=self.control.drawCard).grid(row=0, column=2)
        drawStatsFrame()
    def drawCardGUI(self):
        numSides = self.control.getNumberOfSides()
        self.makeNumVars(numSides, tk.StringVar, self.v["cardSides"])
        self.makeNumWidgets(numSides, self.w["cardSidesFrame"], tk.Label,\
            self.w["cardSideLabels"], argList={"font":"Times 14"},\
            functionList={"text":lambda x:str(x+1)}, start=(0,0))
        self.makeNumWidgets(numSides, self.w["cardSidesFrame"], tk.Label, self.w["cardSides"],\
            argList={"font":"Times 24"}, functionList={"textvariable":lambda x:self.v["cardSides"][x]},\
            start=(0,1))
        self.makeNumWidgets(numSides, self.w["cardSidesFrame"], tk.Button,\
            self.w["cardSideHintButtons"], argList={"text":"Hint", "padx":1,\
            "pady":1, "font":"Arial 8"}, functionList={"command":(lambda x:\
            (lambda:self.popHints(x+1)))}, start=(0,2))
    def startSession(self,sides):
        while sides > len(self.v["sides"]):
            self.v["sides"].append(tk.StringVar())
        self.timer = datetime.datetime.today()
    def enterOverrideReviewTime(self, card):
        DEFAULT_OVERRIDE_TIME = 30
        self.v["shouldOverrideReviewTime"].set(False)
        self.v["overrideReviewTime"].set(DEFAULT_OVERRIDE_TIME)
    def enterOverrideDueDate(self, card):
        if card.updateDue is None:
            dueDate = ""
            if isinstance(card.due, str):
                dueDate = card.due
            elif isinstance(card.due, datetime.datetime) or isinstance(card.due,\
                datetime.date):
                dueDate = card.due.strftime("%Y-%m-%d")
            self.v["shouldOverrideDueDate"].set(False)
            self.v["overrideDueDate"].set(dueDate)
        else:
            self.v["shouldOverrideDueDate"].set(True)
            self.v["overrideDueDate"].set(card.updateDue.strftime("%Y-%m-%d"))
    def enterOverrideDueSpan(self, card):
        if card.updateSpan is None:
            self.v["shouldOverrideDueSpan"].set(False)
            if card.span is not None:
                self.v["overrideDueSpan"].set(card.span)
            else:
                self.v["overrideDueSpan"].set(1)
        else:
            self.v["shouldOverrideDueSpan"].set(True)
            self.v["overrideDueSpan"].set(card.updateSpan)
    def enterOverrideOptions(self, card):
        self.enterOverrideReviewTime(card)
        self.enterOverrideDueDate(card)
        self.enterOverrideDueSpan(card)
    def displayCard(self, card):
        for i in self.v["cardSides"]: i.set("")
        self.v["cardSides"][card.side-1].set(card.content)
        self.enterOverrideOptions(card)
    def displayAllSides(self, theCard):
        for idx,i in enumerate(theCard.content):
            self.v["cardSides"][idx].set(i)
    def updateStats(self):
        theStats = self.control.getStats()
        for i in ("active", "review", "discard", "unique", "total", "new", "rerun"):
            self.v["cardStats"][i].set(theStats[i])
        if theStats["total"] != 0:
            self.v["cardStats"]["average"].set(theStats["ratingSum"]/theStats["total"])
    # * * * * *   GUIs FOR EDITING CARDS   * * * * *
    def editSingleCardGUI(self):
        deckHeadingEntry = tk.StringVar()
        cardNumberVar = tk.StringVar()
        layout = tk.Frame(self.mainFrame)
        sideFrame = tk.Frame(layout)
        deckFrame = tk.Frame(layout)
        self.lay["editSingleCard"] = layout
        sideLabels = []
        sideTexts = []
        hintTexts = [SequenceText(layout, height=5, width=40, zero="NEW")]
        tagsText = tk.Text(layout, height=5, width=40)
        ec = None
        def trivialEntry():
            if not self.__class__.trivialEntry(sideTexts + [tagsText]):
                return False
            for i in hintTexts:
                if not i.trivialEntry():
                    return False
            return True
        def clearForms():
            for i in sideTexts + [tagsText]:
                i.delete("1.0", "end")
            for i in hintTexts:
                i.reset()
                i.frame.grid_forget()
            for i in sideLabels + sideTexts:
                i.grid_forget()
            cardNumberVar.set("")
        def setCardVar():
            Utility.setXOfY(cardNumberVar, max(0, ec.cardNumber), ec.totalCards,\
                zero="NEW")
        def showHint(number):
            hintTexts[number].showText()
        def setHints(theCard):
            hints = theCard.hints if theCard is not None else [[] for i in\
                range(ec.numSides+1)]
            for i in range(ec.numSides+1):
                hintTexts[i].fill(hints[i])
                showHint(i)
        def showTags(theCard):
            tagsText.delete("1.0", "end")
            if theCard is not None:
                tagsText.insert("1.0", " ".join(list(theCard.tags)))
        def showCard():
            theCard = ec.getCurrentCard()
            setCardVar()
            for i in range(ec.numSides):
                theText = sideTexts[i]
                theText.delete("1.0", "end")
                if theCard is not None and i < len(theCard.content):
                    theText.insert("1.0", theCard.content[i])
            setHints(theCard)
            showTags(theCard)
        def getHintList():
            return [i.entries for i in hintTexts]
        def storeHints():
            for i in hintTexts:
                i.store()
        def storeCard():
            storeHints()
            hintList = Utility.deepListCopy(getHintList())
            tags = set(tagsText.get("1.0", "end").strip().split(" "))
            content = []
            for i in range(len(sideTexts)):
                theText = sideTexts[i]
                content.append(theText.get("1.0", "end").strip())
            newCard = FullCard(None, None, content, hintList, tags)
            if not trivialEntry():
                ec.storeCard(newCard)
        def makeSideWidgets():
            functionList = {"text":(lambda x:"Side "+str(x+1))}
            self.makeNumWidgets(ec.numSides, sideFrame, tk.Label, sideLabels,\
                functionList=functionList, start=(0,0), delta=(1,0))
            self.makeNumWidgets(ec.numSides, sideFrame, tk.Text, sideTexts,\
                argList={"height":6, "width":30}, start=(0,1), delta=(1,0))
        def makeHintWidgets():
            sideHintTexts = hintTexts[1:]
            self.makeNumWidgets(ec.numSides, sideFrame, SequenceText,\
                sideHintTexts, argList={"height":4, "width":20, "zero":"NEW"},\
                start=(0,2), delta=(1,0))
            hintTexts[1:] = sideHintTexts
        def bindTextFields():
            for j in sideTexts + [tagsText]:
                j.bind("<Key>", ec.textModified)
        def setInterface():
            makeHintWidgets()
            makeSideWidgets()
            bindTextFields()
            showCard()
        def selectDeck(deckID):
            nonlocal ec
            ec = self.control.getEditSingleCard()
            ec.selectDeckForEditing(deckID)
            setInterface()
        def resetHints():
            ec.resetHints()
            hintsText.delete("1.0", "end")
            theCard = ec.getCurrentCard()
            hintsText.insert("1.0", theCard.hints[0])
        def resetTags():
            ec.resetTags()
            tagsText.delete("1.0", "end")
            theCard = ec.getCurrentCard()
            tagsText.insert("1.0", " ".join(list(theCard.tags)))
        def newCard():
            storeCard()
            ec.editNewCard()
            for i in range(ec.numSides):
                sideTexts[i].delete("1.0", "end")
        def save():
            storeCard()
            ec.saveCards()
        def close():
            nonlocal ec
            self.switchLayout("userDecks")
            clearForms()
            ec = None
        def saveAndClose():
            save()
            close()
        def closeWithoutSave():
            close()
        def reset():
            ec.resetCurrentCard()
            showCard()
        def prevCard():
            storeCard()
            ec.prevCard()
            showCard()
        def nextCard():
            storeCard()
            ec.nextCard()
            showCard()
        def toMulti():
            storeCard()
            self.control.switchToMultiCardEdit(ec)
        def fromMulti(other):
            nonlocal ec
            ec = self.control.getEditSingleCard()
            ec.fromMulti(other)
            self.switchLayout("editSingleCard")
            setInterface()
        self.control.switchToSingleCardEdit = fromMulti
        self.selectDeckHeader(deckFrame, selectDeck)[0].grid(row=0, column=0,\
            columnspan=4)
        tk.Button(deckFrame, text="<", command=prevCard).grid(row=1, column=0)
        tk.Label(deckFrame, textvariable=cardNumberVar).grid(row=1, column=1)
        tk.Button(deckFrame, text=">", command=nextCard).grid(row=1, column=2)
        tk.Button(deckFrame, text="New Card", command=newCard).grid(row=1, column=3)
        tk.Button(deckFrame, text="Save and Close", command=saveAndClose)\
            .grid(row=2, column=0)
        tk.Button(deckFrame, text="Save and Continue", command=save)\
            .grid(row=2, column=1)
        tk.Button(deckFrame, text="Close without saving", command=closeWithoutSave)\
            .grid(row=2, column=2)
        tk.Button(deckFrame, text="Multiple Mode", command=toMulti).grid(row=2,\
            column=3)
        tk.Button(deckFrame, text="Reset", command=reset).grid(row=2, column=4)
        deckFrame.grid(row=0, column=0)
        sideFrame.grid(row=1, column=0)
        tk.Label(layout, text="Card Hints").grid(row=2, column=0)
        hintTexts[0].frame.grid(row=3, column=0)
        tk.Label(layout, text="Tags").grid(row=4, column=0)
        tagsText.grid(row=5, column=0)
    def editMultiCardGUI(self):
        ROWS = EditMultiCards.ROWS
        ec = None
        layout = tk.Frame(self.mainFrame)
        topFrame = tk.Frame(layout)
        bodyFrame = tk.Frame(layout)
        self.lay["editMultiCard"] = layout
        deckNameVar = tk.StringVar()
        pageNumberVar = tk.StringVar()
        rowCheckVars = [tk.BooleanVar() for i in range(ROWS)]
        sideTexts = [[] for i in range(ROWS)]
        hintTexts = [[] for i in range(ROWS)]
        tagTexts = [tk.Text(bodyFrame, height=4, width=15) for i in range(ROWS)]
        sideLabels = [tk.Label(bodyFrame, text="Side 1"), tk.Label(bodyFrame,\
            text="Side 2")]
        rowChecks = [tk.Checkbutton(bodyFrame) for i in range(ROWS)]
        isHintOpen = [True for i in range(ROWS)]
        dividers = []
        def trivialEntry(rowNum):
            return self.__class__.trivialEntry(sideTexts[rowNum] + [tagTexts[rowNum]]\
                + [i.text for i in hintTexts[rowNum]])
        def clearForms():
            for i in ([k for j in sideTexts for k in j] + tagTexts):
                i.delete("1.0", "end")
            for i in hintTexts:
                for j in i:
                    j.setText("")
        def setPageVar():
            Utility.setXOfY(pageNumberVar, ec.pageNumber, ec.totalPages)
        def getHintList():
            return [[j.entries for j in i] for i in hintTexts]
        def getHintListForRow(rowNum):
            return [i.entries for i in hintTexts[rowNum]]
        def displayRow(rowNum):
            theCard = ec.getCardOfRow(rowNum)
            tagTexts[rowNum].delete("1.0", "end")
            if theCard is not None:
                tagTexts[rowNum].insert("1.0", " ".join(list(theCard.tags)))
                for i in range(len(sideTexts[rowNum])):
                    sText = sideTexts[rowNum][i]
                    sText.delete("1.0", "end")
                    enterSide = Utility.getAtIndexIfArray(theCard.content,\
                        i, ifOutRange="")
                    sText.insert("1.0", enterSide)
                for i in range(len(hintTexts[rowNum])):
                    if i < len(hintTexts[rowNum]) and i < len(theCard.hints):
                        hintTexts[rowNum][i].fill(theCard.hints[i][:])
            else:
                for i in range(ec.numSides):
                    sideTexts[rowNum][i].delete("1.0", "end")
                    for j in hintTexts[i]:
                        j.reset()
        def displayPage():
            for i in range(ROWS):
                displayRow(i)
        def newPage(delta):
            ec.newPage(delta)
            setPageVar()
            displayPage()
        def storeHint(rowNum, side):
            ht = hintTexts[rowNum][side]
            ht.store()
        def storeCard(rowNum):
            content = []
            tags = set(tagTexts[rowNum].get("1.0", "end").strip().split(" "))
            for i in range(ec.numSides):
                theText = sideTexts[rowNum][i]
                content.append(theText.get("1.0", "end").strip())
            for i in range(ec.numSides+1):
                storeHint(rowNum, i)
            hintList = Utility.deepListCopy(getHintListForRow(rowNum))
            newCard = FullCard(None, None, content, hintList, tags)
            ec.storeCard(newCard, rowNum)
        def storePage():
            for i in range(ROWS):
                if not trivialEntry(i):
                    storeCard(i)
        def makeHintText(rowNum):
            return SequenceText(bodyFrame, height=4, width=20, zero="NEW")
        def makeHintTextsForRow(rowNum, total):
            while len(hintTexts[rowNum]) < total:
                hintTexts[rowNum].append(makeHintText(rowNum))
            for i in hintTexts[rowNum]:
                i.frame.grid_forget()
            for i in range(ec.numSides+1):
                hintTexts[rowNum][i].frame.grid(row=3*rowNum+3, column=i+2)
        def makeAllHintTexts():
            for i in range(ROWS):
                makeHintTextsForRow(i, ec.numSides+1)
        def makeTextFields():
            for i in range(ROWS):
                self.makeNumWidgets(ec.numSides, bodyFrame, tk.Text, sideTexts[i],\
                    argList={"height":4, "width":20}, start=(3*i+2,3), delta=(0,1))
        def makeSideLabels():
            self.makeNumWidgets(ec.numSides, bodyFrame, tk.Label, sideLabels,\
                functionList={"text":lambda x:"Side "+str(x+1)}, start=(0,3),\
                delta=(0,1))
        def makeTagTexts():
            for i in range(ROWS):
                tagTexts[i].grid(row=3*i+2, column=2)
        def setDividerSpan():
            for i in range(ROWS):
                dividers[i].frame.grid_forget()
                dividers[i].frame.grid(row=3*i+1, column=0, sticky="ew",\
                    columnspan=ec.numSides+3)
        def setInterface():
            makeTextFields()
            makeAllHintTexts()
            makeSideLabels()
            setDividerSpan()
            newPage(0)
        def selectDeck(deckID):
            nonlocal ec
            ec = self.control.getEditMultiCards()
            ec.selectDeckForEditing(deckID)
            setInterface()
        def resetRow(rowNum):
            ec.resetCard(ec.getCardID(rowNum))
            displayRow(rowNum)
        def resetPage():
            for i in range(ROWS): reset(i)
        def saveRow(rowNum):
            if not trivialEntry(rowNum):
                storeCard(rowNum)
                ec.saveRow(rowNum)
        def save():
            for i in range(ROWS):
                saveRow(i)
        def close():
            nonlocal ec
            self.switchLayout("userDecks")
            clearForms()
            ec = None
        def saveAndClose():
            save()
            close()
        def closeWithoutSave():
            close()
        def makeFunctionsMenu(i, theFrame):
            button = tk.Menubutton(theFrame, text="Functions")
            menu = tk.Menu(button, tearoff=0)
            button["menu"] = menu
            button.menu = menu
            menu.add_command(label="Save", command=lambda:saveRow(i))
            menu.add("separator")
            menu.add_command(label="Reset", command=lambda:resetRow(i))
            return button
        def toggleHints(rowNum):
            if isHintOpen[rowNum]:
                for i in hintTexts[rowNum]:
                    i.frame.grid_forget()
            else:
                for idx,i in enumerate(hintTexts[rowNum]):
                    i.frame.grid(row=3*rowNum+3, column=idx+2)
            isHintOpen[rowNum] = not isHintOpen[rowNum]
        def toSingle():
            storePage()
            self.control.switchToSingleCardEdit(ec)
        def fromSingle(other):
            nonlocal ec
            ec = self.control.getEditMultiCards()
            ec.fromSingle(other)
            self.switchLayout("editMultiCard")
            setInterface()
        def getToggleHintFunction(rowNum):
            return lambda:toggleHints(rowNum)
        layout = tk.Frame()
        topFrame.grid(row=0, column=0)
        bodyFrame.grid(row=1, column=0)
        multiPageNum = tk.StringVar()
        multiPageNum.set("Page 1 of 1")
        self.selectDeckHeader(topFrame, selectDeck)[0].grid(row=0, column=0,\
            columnspan=7)
        tk.Button(topFrame, text="<<<", command=lambda:newPage(-100)).grid(row=1,\
            column=0)
        tk.Button(topFrame, text="<<", command=lambda:newPage(-10)).grid(row=1,\
            column=1)
        tk.Button(topFrame, text="<", command=lambda:newPage(-1)).grid(row=1,\
            column=2)
        tk.Label(topFrame, textvariable=pageNumberVar).grid(row=1, column=3)
        tk.Button(topFrame, text=">", command=lambda:newPage(1)).grid(row=1,\
            column=4)
        tk.Button(topFrame, text=">>", command=lambda:newPage(10)).grid(row=1,\
            column=5)
        tk.Button(topFrame, text=">>>", command=lambda:newPage(100)).grid(row=1,\
            column=6)
        tk.Button(topFrame, text="Save and Close", command=saveAndClose).grid(row=2,\
            column=0, columnspan=2)
        tk.Button(topFrame, text="Save and Continue", command=save).grid(row=2,\
            column=2, columnspan=2)
        tk.Button(topFrame, text="Close without Save", command=closeWithoutSave)\
            .grid(row=2, column=4, columnspan=2)
        tk.Button(topFrame, text="Singular Mode", command=toSingle).grid(\
            row=2, column=6)
        tk.Label(bodyFrame, text="Tags/Card Hints").grid(row=0, column=2)
        makeTagTexts()
        self.control.switchToMultiCardEdit = fromSingle
        #for (iIdx,i) in enumerate(sideLabels):
        #    i.grid(row=0, column=iIdx+3)
        for i in range(ROWS):
            theFrame = tk.Frame(bodyFrame)
            rowChecks[i].grid(row=3*i+2, column=1)
            makeFunctionsMenu(i, theFrame).grid(row=0, column=0)
            tk.Button(theFrame, text="Toggle Hints", command=getToggleHintFunction(i))\
                .grid(row=1, column=0)
            theFrame.grid(row=3*i+2, column=0)
            dv = Divider(bodyFrame, o="h", color="black", thickness=6)
            dv.frame.grid(row=3*i+1, columnspan=5, sticky="ew")
            dividers.append(dv)
    def importCardsGUI(self):
        ec = None
        fileName = tk.StringVar()
        currentCard = None
        numNewCards = 0
        deckID = None
        def selectDeck(selectedDeckID):
            nonlocal deckID, ec, numNewCards, currentCard
            ec = self.control.getEditCards()
            numNewCards = 0
            currentCard = None
            ec.selectDeckForEditing(selectedDeckID)
            deckID = selectedDeckID
        def browse():
            fileName.set(tk.filedialog.askopenfilename())
        def newCard(line):
            nonlocal currentCard, numNewCards
            numNewCards += 1
            currentCard = FullCard(-numNewCards, None, [i.strip() for i in line])
        def parseCard(line):
            nonlocal currentCard
            if currentCard is not None:
                ec.storeCard(currentCard)
            cardID = ec.getCardIDFromSide(1, deckID, line[0].strip())
            if cardID is None:
                newCard(line)
            else:
                ecCard = ec.getCard(cardID).copy()
                currentCard = FullCard(cardID, None, ecCard.content[:],\
                    Utility.deepListCopy(ecCard.hints))
        def parseHint(line):
            side = int(line[1])
            content = line[2].strip()
            while len(currentCard.hints) <= side:
                currentCard.hints.append([])
            if content not in currentCard.hints[side]:
                currentCard.hints[side].append(content)
        def parseTags(line):
            currentCard.tags.update(set(line[2].strip().split(" ")))
        def importFile():
            if self.control.canEditDeck(ec.deckID):
                fin = open(fileName.get(), "r")
                lineStr = "\n"
                while lineStr != "":
                    lineStr = fin.readline()
                    line = lineStr.rstrip().split("\t")
                    if len(line) >= 2:
                        if line[0] != "":
                            parseCard(line)
                        elif line[1][0] in "0123456789":
                            parseHint(line)
                        elif line[1].strip() == "tags":
                            parseTags(line)
                if currentCard is not None:
                    ec.storeCard(currentCard)
                ec.saveCards()
            else:
                messagebox.showinfo("Cannot import to that deck.")
        layout = tk.Frame(self.mainFrame)
        self.lay["importCards"] = layout
        self.selectDeckHeader(layout, selectDeck)[0].grid(row=0, column=0,\
            columnspan=3)
        tk.Label(layout, text="File Path").grid(row=1, column=0)
        tk.Entry(layout, textvariable=fileName).grid(row=1, column=1)
        tk.Button(layout, text="Browse", command=browse).grid(row=1, column=2)
        tk.Button(layout, text="Import", command=importFile).grid(row=2, column=0,\
            columnspan=3)
    # * * * * *   GUIs FOR EDITING USER AND OTHER INFORMATION   * * * * *
    def newFileGUI(self):
        fileName = tk.StringVar()
        layout = tk.Frame(self.mainFrame)
        def submit():
            if os.path.isfile(fileName.get() + ".db"):
                messagebox.showinfo("A database with that name already exists.")
            else:
                Utility.newDB(fileName.get())

        self.lay["newFile"] = layout
        tk.Label(layout, text="Database Name:").grid(row=0, column=0)
        tk.Entry(layout, textvariable=fileName).grid(row=0, column=1)
        tk.Button(layout, text="Submit", command=submit).grid(row=1, column=1)
    def newUserGUI(self):
        userName = tk.StringVar()
        layout = tk.Frame(self.mainFrame)
        def submit():
            if self.info.doesUsernameExist(userName.get()):
                messagebox.showinfo("A user with that name already exists.")
            else:
                self.edituser.newUser(userName.get())
        self.lay["newUser"] = layout
        tk.Label(layout, text="User Name:").grid(row=0, column=0)
        tk.Entry(layout, textvariable=fileName).grid(row=0, column=1)
        tk.Button(layout, text="Submit", command=submit).grid(row=1, column=1)
    def newDeckGUI(self):
        layout = tk.Frame(self.mainFrame)
        self.lay["newDeck"] = layout
        deckName = tk.StringVar()
        numSides = tk.IntVar()
        numSides.set(2)
        def back():
            self.revertLayout()
        def create():
            if deckName.get().strip() != "":
                numSidesArg = numSides.get()
                if numSidesArg < 2:
                    numSidesArg = 2
                self.edituser.newDeck(deckName.get(), numSidesArg)
        tk.Button(layout, text="Go Back", command=back).grid(row=0, column=0)
        tk.Label(layout, text="Name of Deck").grid(row=1, column=0)
        tk.Entry(layout, textvariable=deckName).grid(row=1, column=1)
        tk.Label(layout, text="Number of Sides").grid(row=2, column=0)
        tk.Entry(layout, textvariable=numSides).grid(row=2, column=1)
        tk.Button(layout, text="Create Deck", command=create).grid(row=3, column=0,\
            columnspan=2)
    def useDeckGUI(self):
        layout = tk.Frame(self.mainFrame)
        self.lay["useDeck"] = layout
        deckHeadingEntry = tk.StringVar()
        checkboxFrame = tk.Frame(layout)
        sideVars = [tk.BooleanVar(), tk.BooleanVar()]
        sideChecks = []
        message = tk.StringVar()
        def deckInFilter(x):
            return True # filter already used
        def getSideFlag(): # replace with Utility.makeNumberFromBits
            sum = 0
            for i in range(len(sideVars)):
                if sideVars[i].get(): sum += 2**i
            if sum == 0:
                return 2**len(sideVars)-1
            return sum
        def updateSides(event):
            listBoxWidget = event.widget
            selectionNumber = listBoxWidget.curselection()[0]
            deckID = self.edituser.getDeckIDFromName(listBoxWidget.get(selectionNumber))
            numSides = self.edituser.getNumDeckSides(deckID)
            functionList = {"text":(lambda x:x+1), "variable":(lambda x:sideVars[x])}
            self.makeNumVars(numSides, tk.BooleanVar, sideVars)
            self.makeNumWidgets(numSides, checkboxFrame, tk.Checkbutton, sideChecks,\
                functionList=functionList, start=(0,0), delta=(0,1))
        def selectDeck(deckID):
            self.edituser.useDeck(deckID, getSideFlag())
            message.set("The deck " + self.edituser.getDeckNameFromID(deckID) +\
                " has been selected. You may select a new deck or push 'Finished'")
        def finished():
            self.switchLayout("userDecks")
        checkboxFrame.grid(row=1, column=0)
        r = self.selectDeckHeader(layout, selectDeck, filter=deckInFilter)
        r[0].grid(row=0, column=0)
        r[1].bind("<<ListboxSelect>>", updateSides)
        message.set("Select a deck and which sides to use.")
        tk.Label(layout, textvariable=message).grid(row=2, column=0)
        tk.Button(layout, text="Finished", command=finished).grid(row=3, column=0)
    def setOptionsGUI(self):
        layout = tk.Frame(self.mainFrame)
        self.lay["options"] = layout
        optionsFrame = tk.Frame(layout)
        reviewByRatingFrame = tk.Frame(layout)
        numberOfCardsFrame = tk.Frame(layout)
        secondsToReview = [tk.IntVar() for i in range(6)]
        timesToReview = [tk.IntVar() for i in range(6)]
        numNewCards = tk.IntVar()
        numReviewedCards = tk.IntVar()
        percentNew = tk.IntVar()
        deckID = None
        options = {}
        def getFields():
            secondsToReviewValues = [i.get() for i in secondsToReview]
            timesToReviewValues = [i.get() for i in timesToReview]
            numberCardsToDrawValues = [numNewCards.get(), numReviewedCards.get(),\
                percentNew.get()]
            return {"secondsToReview":secondsToReviewValues,\
                "timesToReview":timesToReviewValues,\
                "numCardsToDraw":numberCardsToDrawValues}
        def fillFields():
            for i in range(6):
                secondsToReview[i].set(self.edituser.getOption(i, deckID=deckID))
                timesToReview[i].set(self.edituser.getOption(i+6, deckID=deckID))
            numNewCards.set(self.edituser.getOption(12, deckID=deckID))
            numReviewedCards.set(self.edituser.getOption(13, deckID=deckID))
            percentNew.set(self.edituser.getOption(14, deckID=deckID))
        def deckSelected(deckName):
            nonlocal deckID
            if deckName != "-- GENERA --":
                deckID = self.edituser.getDeckIDFromName(deckName)
            else:
                deckID = None
            fillFields()
        def finished():
            self.edituser.setOptions(deckID, **getFields())
        def filterUserDecks(x):
            self.edituser.isUsingDeckName(x)
        (listBoxFrame, theListBox) = self.selectDeckHeader(layout, deckSelected,\
            filter=filterUserDecks)
        theListBox.insert(0, "-- GENERAL --")
        tk.Label(reviewByRatingFrame, text="Minutes to review cards rated:").\
            grid(row=0, column=0, rowspan=2)
        tk.Label(reviewByRatingFrame, text="Number of times to review cards rated:")\
            .grid(row=2, column=0, rowspan=2)
        for i in range(6):
            tk.Label(reviewByRatingFrame, text=str(i)).grid(row=0, column=i+1)
            tk.Entry(reviewByRatingFrame, textvariable=secondsToReview[i], width=4)\
                .grid(row=1, column=i+1)
            tk.Label(reviewByRatingFrame, text=str(i)).grid(row=2, column=i+1)
            tk.Entry(reviewByRatingFrame, textvariable=timesToReview[i], width=4)\
                .grid(row=3, column=i+1)
        tk.Label(numberOfCardsFrame, text="Number of new cards to draw when the "\
            "session begins").grid(row=0, column=0, sticky="e")
        tk.Entry(numberOfCardsFrame, textvariable=numNewCards, width=10).grid(row=0,\
            column=1, sticky="w")
        tk.Label(numberOfCardsFrame, text="Number of reviewed cards to draw when the "\
            "session begins").grid(row=1, column=0, sticky="e")
        tk.Entry(numberOfCardsFrame, textvariable=numReviewedCards, width=10)\
            .grid(row=1, column=1, sticky="w")
        tk.Label(numberOfCardsFrame, text="Percent of cards drawn during the session "\
            "to be new").grid(row=2, column=0, sticky="e")
        tk.Entry(numberOfCardsFrame, textvariable=percentNew, width=10).grid(row=2,\
            column=1, sticky="w")
        tk.Button(layout, text="Save", command=finished).grid(row=3, column=0)
        for i in range(6):
            secondsToReview[i].set(Model.SECONDS_TO_REVIEW[i])
            timesToReview[i].set(Model.TIMES_TO_REVIEW[i])
        numNewCards.set(Model.NUMBER_OF_NEW_CARDS)
        numReviewedCards.set(Model.NUMBER_OF_REVIEWED_CARDS)
        percentNew.set(Model.PERCENT_NEW)
        listBoxFrame.grid(row=0, column=0)
        reviewByRatingFrame.grid(row=1, column=0)
        numberOfCardsFrame.grid(row=2, column=0)

class Controller:
    def __init__(self):
        self.view = View(self)
        self.view.begin()
    def getConnection(self):
        return self.conn
    def getUserID(self):
        return self.user
    def openFile(self, filename):
        self.conn = sqlite3.connect(filename+".db")
        c = self.conn.cursor()
        self.view.resetSelectUserbox(ModelInfo.getUsers(c))
        c.close()
        self.model = Model(self.conn)
        self.model.control = self
        self.view.switchLayout("selectUser")
    def getUserDecks(self):
        return self.userDecks
    def setUserDecks(self):
        self.userDecks = self.view.edituser.getUserDecks()
    def setSessionDecks(self):
        self.sessionDecks = {}
        self.deckIDList = []
        for idx,i in enumerate(self.view.v["userDeckChecks"]):
            if i.get():
                theDeck = self.userDecks[idx].copy()
                self.sessionDecks[theDeck.id] = theDeck
                self.deckIDList.append(theDeck.id)
    def getSessionDecks(self):
        return self.sessionDecks
    def getNumberOfSides(self):
        return max([self.sessionDecks[i].totalSides for i in self.sessionDecks])
    def getDeckInfo(self, deckID):
        return self.sessionDecks[deckID]
    def getDeckNumber(self, number):
        return self.sessionDecks[self.deckIDList[number]]
    def getHints(self, cardID=None):
        if cardID is None:
            cardID = self.model.currentCard.id
        return self.model.reference[cardID].hints
    def getTags(self, cardID=None):
        if cardID is None:
            cardID = self.model.currentCard.id
        return self.model.reference[cardID].tags
    def selectUser(self, username):
        self.view.edituser = EditUser(self.conn, None)
        eu = self.view.edituser
        eu.user = eu.getUserID(username)
        self.user = eu.user
        self.model.user = eu.user
        self.setUserDecks()
        self.view.drawGUI()
        self.view.switchLayout("userDecks")
        self.view.displayUserDecks()
    def getSidesUsed(self, deckID):
        return Utility.getBinaryFlags1(self.getDeckInfo(deckID).sidesUsedInSession)
    def areAllDecksChecked(self):
        for i in self.sessionDecks:
            if self.sessionDecks[i].sidesUsedInSession == 0:
                return False
        return True
    def setSidesUsedInSession(self, theDeck, varListIndex):
        sideCheckList = [j.get() for j in\
            self.view.v["preReviewDeckOptions"]["sides"][varListIndex]]
        sidesUsed = Utility.getBinaryFlags1(theDeck.sidesUsed)
        sideList = []
        for i in range(len(sidesUsed)):
            if sideCheckList[i]:
                sideList.append(sidesUsed[i])
        theDeck.sidesUsedInSession = Utility.makeNumberFromBits1(sideList)
    def setPreReviewData(self):
        for i in range(6):
            self.model.secondsToReview[i] = self.view.v["preReviewRateWait"][i].get()
            self.model.nTimesToReview[i] = self.view.v["preReviewRateTimes"][i].get()
        for i in range(len(self.deckIDList)):
            theDeck = self.sessionDecks[self.deckIDList[i]]
            theDeck.numNew = self.view.v["preReviewDeckOptions"]["new"][i].get()
            theDeck.numDue = self.view.v["preReviewDeckOptions"]["reviewed"][i].get()
            theDeck.percentNewInSession = self.view.v["preReviewDeckOptions"]["session"][i].get()
            self.setSidesUsedInSession(theDeck, i)
    def setDeckInfoForModel(self):
        self.model.deckInfo = {}
        for i in self.sessionDecks:
            self.model.deckInfo[i] = self.sessionDecks[i].copy()
    def loadDecks(self):
        for i in self.sessionDecks:
            self.model.loadDeck(i)
    def begin(self):
        self.setPreReviewData()
        if self.areAllDecksChecked():
            self.setDeckInfoForModel()
            self.loadDecks()
            self.model.logBeginning()
            self.view.switchLayout("card")
            self.view.drawCardGUI()
            self.view.updateStats()
            self.model.currentCard = CardSide()
            self.drawCard()
    def setOverrideDueTimes(self):
        if self.view.shouldOverrideDueDate():
            self.model.currentCard.updateDue = self.view.getOverrideDueDate()
        else:
            self.model.currentCard.updateDue = None
        if self.view.shouldOverrideDueSpan():
            self.model.currentCard.updateSpan = self.view.getOverrideDueSpan()
        else:
            self.model.currentCard.updateSpan = None
    def rateCard(self, r):
        self.model.rateCard(r)
        self.setOverrideDueTimes()
        self.model.updateStatsAfterRating(r)
        if self.view.shouldOverrideReviewTime():
            self.model.toReview(self.view.getOverrideReviewTime())
        else:
            self.model.returnCardToDeck(r)
        self.view.switchFrame("cardRateButtons","cardStatusButtons",3,0)
        theCard = self.model.reference[self.model.currentCard.id]
        self.view.displayAllSides(theCard)
        self.view.updateStats()
    def displayCard(self):
        self.view.switchFrame("cardStatusButtons","cardRateButtons",3,0)
        self.view.displayCard(self.model.currentCard)
    def reviewEarly(self):
        self.model.reviewEarly()
        self.displayCard()
    def drawCard(self):
        self.model.drawCard()
        self.displayCard()
    def endSession(self):
        self.model.save()
        self.model.closeLog()
        self.view.switchLayout("userDecks")
    def canEditDeck(self, deckID):
        return self.view.edituser.doesDeckIDExist(deckID)
    def getEditSingleCard(self):
        return EditSingleCard(self.conn, self.user)
    def getEditMultiCards(self):
        return EditMultiCards(self.conn, self.user)
    def getEditCards(self):
        return EditCards(self.conn, self.user)
    def getStats(self):
        theStats = {}
        theStats["active"] = self.model.active.size()
        theStats["review"] = self.model.review.size()
        theStats["discard"] = self.model.discard.size()
        for i in self.model.stats:
            theStats[i] = self.model.stats[i]
        return theStats
    def commit(self):
        self.conn.commit()

c = Controller()
