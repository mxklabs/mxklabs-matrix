class Observable:

    """ Implements observer pattern. """

    def __init__(self):
        """ Constructor. """
        self._observers = []

    def add_observer(self, observer):
        """ Add an observer. """
        self._observers.append(observer)

    def remove_observer(self, observer):
        """ Remove an observer. """
        self._observers.remove(observer)

    def _notify_observers(self):
        """ Notify observers. """
        for observer in self._observers:
            observer()