class BinaryHeap:
	def __init__(self):
		self.values = []
	def insert(self,k,v):
		i = len(self.values)
		self.values.append(None)
		while i >= 1 and self.values[(i-1)//2][0] > k:
			self.values[i] = self.values[(i-1)//2]
			i = (i-1)//2
		self.values[i] = (k,v)
	def getRootKey(self):
		if len(self.values) > 0:
			return self.values[0][0]
	def getRoot(self):
		if len(self.values) > 0:
			return self.values[0][1]
	def popRoot(self):
		if len(self.values) == 0:
			return None
		i = 0
		oldRoot = self.values[0]
		while 2*i+2 < len(self.values) and (self.values[-1][0] > self.values[2*i+1][0] or self.values[-1][0] > self.values[2*i+2][0]):
			if self.values[2*i+1][0] > self.values[2*i+2][0]:
				self.values[i] = self.values[2*i+2]
				i = 2*i+2
			else:
				self.values[i] = self.values[2*i+1]
				i = 2*i+1
		self.values[i] = self.values[-1]
		del self.values[-1]
		return oldRoot[1]
	def getValues(self):
		return [i[1] for i in self.values]
	def size(self):
		return len(self.values)
	def printList(self):
		if len(self.values) > 0:
			self.printListStep(0,0)
	def printListStep(self,start,indent):
		print(" "*indent + str(self.values[start]))
		if len(self.values) > 2*start+1:
			self.printListStep(2*start+1,indent+1)
		if len(self.values) > 2*start+2:
			self.printListStep(2*start+2,indent+1)
