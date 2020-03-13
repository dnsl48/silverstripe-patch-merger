# removing the files "deleted by us"

import logging

from . import ConflictResolver

class TravisConfigIgnorer(ConflictResolver):
    def isKnown(self, git_repo):
        blobs = git_repo.index.unmerged_blobs()

        if '.travis.yml' in blobs and len(blobs['.travis.yml']) == 3:
            return True

        return False

    def resolve(self, git_repo):
        super().resolve(git_repo)

        git_repo.git.checkout('.travis.yml', ours=True)
        git_repo.git.add('.travis.yml', update=True)

        return True
