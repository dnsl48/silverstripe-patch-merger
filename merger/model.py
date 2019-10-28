import os
import re
import sys
import git

from .mixin import ComparableMixin

class Branch(ComparableMixin):
    _regex_minor = re.compile('(\d+)\.(\d+)')
    _branch = None

    @classmethod
    def create(cls, github_branch):
        if github_branch.name.isdecimal():  # it's major
            return MajorBranch(int(github_branch.name), github_branch)

        else:
            match = cls._regex_minor.fullmatch(github_branch.name)
            if not match:
                return None

            version = match.groups()
            return MinorBranch(int(version[0]), int(version[1]), github_branch)

    def __init__(self, github_branch):
        self._branch = github_branch

    @property
    def name(self):
        return self._branch.name

class MajorBranch(Branch):
    _v_major = None

    def __init__(self, version, github_branch):
        super().__init__(github_branch)
        self._v_major = version

    def _cmpkey(self):
        return (self._v_major, sys.maxsize)

class MinorBranch(Branch):
    _v_major = None
    _v_minor = None

    def __init__(self, major_version, minor_version, github_branch):
        super().__init__(github_branch)
        self._v_major = major_version
        self._v_minor = minor_version

    def _cmpkey(self):
        return (self._v_major, self._v_minor)

class Repo:
    _github_repo = None
    _git_repo = None
    _branches = []

    def __init__(self, github_repo):
        self._github_repo = github_repo

        _path = '/tmp/ss-merger-{}'.format(self._github_repo.id)
        if os.path.exists(_path):
            self._git_repo = git.Repo(_path)
        else:
            self._git_repo = git.Repo.clone_from(self._github_repo.clone_url, _path)

        for github_branch in github_repo.get_branches():
            branch = Branch.create(github_branch)
            if not branch:
                continue
            self._branches.append(branch)

        self._branches.sort()
        self._git_repo_init()

    @property
    def branches(self):
        return self._branches

    @property
    def g_repo(self):
        return self._git_repo

    @property
    def gh_repo(self):
        return self._github_repo

    def _git_repo_init(self):
        origin = self._git_repo.remotes.origin
        origin.fetch()

        for branch in self.branches:
            self._git_repo.create_head(branch.name, origin.refs[branch.name].commit)

    def mergeUp(self, conflict_resolvers):
        idx = 1

        while len(self.branches) > idx+1:
            self._mergeUp(idx, conflict_resolvers)
            idx += 1

    def _mergeUp(self, idx, conflict_resolvers):
        src = self.branches[idx].name
        dst = self.branches[idx+1].name

        src_head = self._git_repo.heads[src]
        dst_head = self._git_repo.heads[dst]
        dst_head.checkout()

        try:
            import ipdb; ipdb.set_trace()
            self._git_repo.git.merge(src_head)

            import ipdb; ipdb.set_trace()
        except:
            if len(self._git_repo.index.unmerged_blobs()):
                self._resolveConflicts(conflict_resolvers)
            else:
                raise Exception('weirdo...')
                # return False

        import ipdb; ipdb.set_trace()

        # merge_base = self._git_repo.merge_base(src_head, dst_head)
        # index = self._git_repo.index.merge_tree(src_head, base=merge_base)
        # import ipdb; ipdb.set_trace()

        if not self._git_repo.index.diff():
            return

        # self._git_repo.index.merge_tree(dst_head, base=merge_base)

        pass

        # self._git_repo.heads[src]

    def _resolveConflicts(self, conflict_resolvers):
        for resolver in conflict_resolvers:
            if resolver.isKnown(self._git_repo):
                try:
                    resolver.resolve(self._git_repo)
                except:
                    pass
