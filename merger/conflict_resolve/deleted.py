# removing the files "deleted by us"

from . import ConflictResolver

class DeletedInNewerVersion(ConflictResolver):
    _docker_client = None

    def isKnown(self, git_repo):
        # for file in [i[0] for i in git_repo.index.unmerged_blobs()]:
        #     if file not in [a[0][0] for a in git_repo.index.entries.items()]

        for file,blobs in git_repo.index.unmerged_blobs().items():
            if len(blobs) == 2:
                return True

        return False

    def resolve(self, git_repo):
        super().resolve(git_repo)

        for file,blobs in git_repo.index.unmerged_blobs().items():
            if len(blobs) == 2:
                git_repo.git.rm(file)

        return True
