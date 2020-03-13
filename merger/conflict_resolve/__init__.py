class ConflictResolver:
    def isKnown(self, git_repo):
        return False

    def resolve(self, git_repo):
        pass

    @property
    def name(self):
        return self.__class__.__qualname__