import sys
import re
from subprocess import check_call, call, check_output

remote = "origin"


def probe_driver_repo_for_name(driverRepoPath):
    print("Probing {} for driver name".format(driverRepoPath))
    url = check_output(
        ["git", "remote", "get-url", remote],
        cwd=driverRepoPath, universal_newlines=True)
    url = url.splitlines()[0]
    match = re.search('^(.*)/neo4j-(?P<driverName>.*)-driver.git$', url)
    if not match:
        return "unknown"
    try:
        return match.group('driverName')
    except IndexError:
        return "unknown"


def get_testkit_branch(driverName, driverTargetBranch):
    if driverName == "go" and driverTargetBranch in ['4.0', '4.1']:
        return "4.2"
    return driverTargetBranch


def main(testkitRepoPath, driverRepoPath, driverTargetBranch):
    driverName = probe_driver_repo_for_name(driverRepoPath)
    print("Driver is {} and target branch is {}".format(
        driverName, driverTargetBranch))

    testkitBranch = get_testkit_branch(driverName, driverTargetBranch)
    print("Testkit branch is {}".format(testkitBranch))

    check_call(["git", "fetch", remote], cwd=testkitRepoPath)
    # Position on master to be able to remove temp branch
    call(["git", "checkout", "master"], cwd=testkitRepoPath)
    # Checkout the branch named as a temporary to avoid having to pull but
    # delete it first to make sure it is up to date with the remote.k
    localBranch = "tempForPr"
    call(["git", "branch", "-D", localBranch], cwd=testkitRepoPath)
    remoteBranch = "{}/{}".format(remote, testkitBranch)
    check_call(
        ["git", "checkout", "-b", localBranch, remoteBranch],
        cwd=testkitRepoPath)

    # Run testkit
    testkitEnv = {
        "TEST_DRIVER_NAME": driverName,
        "TEST_DRIVER_REPO": driverRepoPath
    }
    check_call(["python3", "main.py"], env=testkitEnv, cwd=testkitRepoPath)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
