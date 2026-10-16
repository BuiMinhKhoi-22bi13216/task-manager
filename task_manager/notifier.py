from abc import ABC, abstractmethod

class Notifier(ABC):

   @abstractmethod
   def send(self, message:str) -> None:
    pass

class ConsoleNotifier(Notifier):
   def send(self, message:str) -> None:
     print(message)

class EmailNotifier(Notifier):
   def send(self, message:str) -> None:
     print("Email send: ", message)