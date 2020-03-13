# removing the files "deleted by us"

import logging

from . import ConflictResolver

class DeletedInNewerVersion(ConflictResolver):
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
                logging.info('Removing %s', file)
                git_repo.git.rm(file)

        return True
