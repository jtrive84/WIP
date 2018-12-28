#!/bin/bash
#==============================================================================#
# Commands to integrate working copy development commits with                  #
# larger LLE codebase.                                                         #
#                                                                              #
# Requires that `master` branch be used only for tracking origin/master,       #
# and that al ldevelopment happens in `dev` branch.                            #
#==============================================================================#
COMMIT_MSG_ARGV="$1"
GIT_EXE="$(which git)"

# Use first command line argument as commit message if present, otherwise 
# use standard WIP commit message. 
if [[ ${#COMMIT_MSG_ARGVS} -gt 0 ]]; then
    COMMIT_MSG="${COMMIT_MSG_ARGVS}"
else
    COMMIT_MSG="DH=> WIP commit."
fi

#==============================================================================#
# The fundamental idea of rebasing is that you make sure that your commits go  # 
# on top of the "public" branch, that you "rebase" them so that instead of     #
# being related to some commit way back when you started working on this       #
# feature, they get reworked a little so they go on top of what's there now.   #
#==============================================================================#

# Assumes changes exist on local `dev` branch which need to be integrated with 
# origin/master.
pushd "/SAS/enterprise/Large_Loss_2018/dheinz/LLE" > /dev/null

"${GIT_EXE}" add --all; wait                  # Stage commits in working copy's `dev` branch

"${GIT_EXE}" commit -m "${COMMIT_MSG}"; wait  # Commit changes to working copy's `dev` branch

"${GIT_EXE}" fetch origin; wait               # Update LLE origin/ branches from remote repo

"${GIT_EXE}" rebase origin/master; wait       # Plop latest commits in `dev` on top of fetched origin/master

"${GIT_EXE}" checkout master; wait            # Switch to working copy's local tracking branch

"${GIT_EXE}" pull; wait                       # Make local tracking branch match current state of origin/master

"${GIT_EXE}" rebase dev; wait                 # Rebase current origin/master commits on top of `dev` commits

"${GIT_EXE}" push -u origin master; wait      # Push changes back to origin/master

"${GIT_EXE}" branch -d dev; wait              # Purge local development branch

"${GIT_EXE}" checkout -b dev; wait            # Create new `dev` branch for development. 

echo "Rebase complete!"
