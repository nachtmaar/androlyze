#!/bin/bash

source $ANDROLYZE_UTIL

# get a value from the config file
function get_settings_value_for_key {
	cat $WORKER_CONFIG_PATH | sed -n "s/$1[ ]*=[ ]*\(.*\)/\1/p"
}

echo "getting config files ..."
init_configs.sh

# get code
if [ ! -d "$WORKER_HOME/androlyze/.git" ]; then
	echo "androlyze repo does not exist -> clone it"
	# private repo ?
	SSH_PRIV_KEY=$(get_settings_value_for_key repo_priv_key_b64)
	SSH_KNOWN_HOSTS=$(get_settings_value_for_key repo_known_host_b64)
	mkdir -p ~/.ssh
	echo $SSH_PRIV_KEY    | base64 -di > ~/.ssh/id_rsa 2>/dev/null
	chmod 600 ~/.ssh/id_rsa
	echo $SSH_KNOWN_HOSTS | base64 -di > ~/.ssh/known_hosts 2>/dev/null

	# check androlyze repository out
	ANDROLYZE_REPO=$(get_settings_value_for_key repo_path_git_url)
	ANDROLYZE_REPO_NAME=repo
	ANDROLYZE_REPO_BRANCH=$(get_settings_value_for_key repo_branch)
	echo "getting AndroLyze from $ANDROLYZE_REPO branch: $ANDROLYZE_REPO_BRANCH ..."
	cd ..
	git clone $ANDROLYZE_REPO $ANDROLYZE_REPO_NAME
	rsync -avz --ignore-existing $ANDROLYZE_REPO_NAME androlyze
	mv -n $ANDROLYZE_REPO_NAME/.* androlyze/
	cd androlyze
	git checkout -f $ANDROLYZE_REPO_BRANCH
else
	echo "androlyze repo does already exist -> using this code ..."
fi

# Get configs again because they got overwritten
echo "getting config files ..."
init_configs.sh
