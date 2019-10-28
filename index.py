if __name__ == '__main__':
    import docker

    from merger import core
    from merger.conflict_resolve.deleted import DeletedInNewerVersion
    from merger.conflict_resolve.node import NodeJsNaiveResolver

    repo = core.get_repository('silverstripe-admin')

    repo.mergeUp([
        DeletedInNewerVersion(),
        NodeJsNaiveResolver(docker.client.from_env())
    ])

    import ipdb; ipdb.set_trace()

    print('Yeah!')