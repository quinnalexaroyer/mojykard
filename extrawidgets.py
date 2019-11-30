import tkinter as tk

class SequenceWidget:
    def __init__(self, parent, height=4, width=20, zero=0):
        self.frame = tk.Frame(parent)
        self.indexVar = tk.StringVar()
        self.zero = zero
        tk.Button(self.frame, text="<", command=self.prev).grid(row=0, column=0)
        tk.Button(self.frame, text=">", command=self.next).grid(row=0, column=2)
        tk.Label(self.frame, textvariable=self.indexVar).grid(row=0, column=1)
        self.resetMembers()
    def resetMembers(self):
        self.entries = []
        self.currentNum = 0
        self.total = 0
    def reset(self):
        self.resetMembers()
        self.text.delete("1.0", "end")
        self.indexVar.set("")
    def get(self, number):
        if 1 <= number <= len(self.entries):
            return self.entries[number-1]
    def set(self, number, value):
        self.entries[number-1] = value
    def trivialEntry(self):
        return self.getText().strip() == ""
    def fill(self, theList):
        self.entries = theList[:]
        self.total = len(theList)
        if self.total > 0:
            self.currentNum = 1
        else:
            self.currentNum = 0
        self.showText()
        self.setVar()
    def showText(self):
        pass
    def append(self, value):
        self.entries.append(value)
        self.total += 1
    def setVar(self):
        num = str(self.currentNum) if self.currentNum != 0 else str(self.zero)
        self.indexVar.set(num + " of " + str(self.total))
    def showText(self):
        self.setText(self.get(self.currentNum))
    def prev(self):
        self.currentNum -= 1
        if self.currentNum < 1:
            self.currentNum = self.total
        self.setVar()
        self.showText()
    def next(self):
        self.currentNum += 1
        if self.currentNum > self.total:
            self.currentNum = 1
        self.setVar()
        self.showText()
    def resetEntriesModified(self):
        self.entriesModified = 0
    def grid_forget(self):
        self.frame.grid_forget()
    def grid(self, *args, **kwargs):
        self.frame.grid(*args, **kwargs)
    def config(self, *args, **kwargs):
        if "zero" in kwargs:
            self.zero = kwargs["zero"]
            del kwargs["zero"]
        self.frame.config(*args, **kwargs)

class SequenceLabel(SequenceWidget):
    def __init__(self, parent, height=4, width=20, zero=0):
        super().__init__(parent, height=height, width=width, zero=zero)
        self.var = tk.StringVar()
        self.label = tk.Label(parent, textvariable=self.var, height=height,\
            width=width)
        self.label.grid(row=1, column=0, columnspan=3)
    def setText(self, value):
        self.var.set(value)

class SequenceText(SequenceWidget):
    def __init__(self, parent, height=4, width=20, zero=0):
        super().__init__(parent, height=height, width=width, zero=zero)
        self.text = tk.Text(self.frame, height=height, width=width)
        self.text.grid(row=1, column=0, columnspan=3)
    def getText(self):
        return self.text.get("1.0", "end").strip()
    def setText(self, value):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", value)
    def store(self):
        if not self.trivialEntry():
            if self.currentNum == 0:
                self.append(self.getText().strip())
            else:
                self.set(self.currentNum, self.getText())
    def showText(self):
        if self.currentNum != 0:
            self.setText(self.get(self.currentNum))
        else:
            self.setText("")
    def prev(self):
        self.store()
        self.currentNum -= 1
        if self.currentNum < 0:
            self.currentNum = self.total
        self.setVar()
        self.showText()
    def next(self):
        self.store()
        self.currentNum += 1
        if self.currentNum > self.total:
            self.currentNum = 0
        self.setVar()
        self.showText()

class Divider:
    def __init__(self, parent, **options):
        self.parent = parent
        self.frame = tk.Frame(parent)
        self.setOptions(**options)
        self.configOptions()
    def setOptions(self, **options):
        self.color = options["color"] if "color" in options else "black"
        self.thickness = options["thickness"] if "thickness" in options else 2
        self.o = options["o"] if "o" in options else "h"
    def configOptions(self):
        self.frame.config(bg=self.color)
        if self.o == "h":
            self.frame.config(height=self.thickness)
        elif self.o == "v":
            self.frame.config(width=self.thickness)
