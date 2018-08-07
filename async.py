import asyncio
from asyncio import sleep
class Async:
	def __init__(self):
		self.tasks = []
		self.loop = asyncio.get_event_loop()
	def addTask(self,task):
		self.tasks.append(self.loop.create_task(task))

	def run(self):
		if self.tasks == []:
			return
		wait = asyncio.wait(self.tasks)
		self.loop.run_until_complete(wait)
		self.tasks = []
async def xyu(a):
	print(a)
